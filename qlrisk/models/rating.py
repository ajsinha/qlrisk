"""
QLRisk - Credit Rating Model v1.2.0
==================================================

Credit rating and credit quality models.

Copyright © 2025-2030, All Rights Reserved
Ashutosh Sinha | Email: ajsinha@gmail.com
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import uuid


class RatingAgency(Enum):
    """Credit rating agency."""
    SP = "S&P"
    MOODYS = "Moodys"
    FITCH = "Fitch"
    INTERNAL = "Internal"


class RatingScale(Enum):
    """Standard rating scale (S&P equivalent)."""
    AAA = "AAA"
    AA_PLUS = "AA+"
    AA = "AA"
    AA_MINUS = "AA-"
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    BBB_PLUS = "BBB+"
    BBB = "BBB"
    BBB_MINUS = "BBB-"
    BB_PLUS = "BB+"
    BB = "BB"
    BB_MINUS = "BB-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    CCC_PLUS = "CCC+"
    CCC = "CCC"
    CCC_MINUS = "CCC-"
    CC = "CC"
    C = "C"
    D = "D"
    NR = "NR"


# Rating to PD mapping (annual, in basis points)
RATING_PD_MAP = {
    RatingScale.AAA: 1,
    RatingScale.AA_PLUS: 2,
    RatingScale.AA: 3,
    RatingScale.AA_MINUS: 4,
    RatingScale.A_PLUS: 5,
    RatingScale.A: 7,
    RatingScale.A_MINUS: 9,
    RatingScale.BBB_PLUS: 15,
    RatingScale.BBB: 25,
    RatingScale.BBB_MINUS: 45,
    RatingScale.BB_PLUS: 75,
    RatingScale.BB: 125,
    RatingScale.BB_MINUS: 200,
    RatingScale.B_PLUS: 350,
    RatingScale.B: 550,
    RatingScale.B_MINUS: 900,
    RatingScale.CCC_PLUS: 1500,
    RatingScale.CCC: 2500,
    RatingScale.CCC_MINUS: 4000,
    RatingScale.CC: 6500,
    RatingScale.C: 10000,
    RatingScale.D: 10000,
}


# Rating to numeric score
RATING_SCORE_MAP = {
    RatingScale.AAA: 1,
    RatingScale.AA_PLUS: 2,
    RatingScale.AA: 3,
    RatingScale.AA_MINUS: 4,
    RatingScale.A_PLUS: 5,
    RatingScale.A: 6,
    RatingScale.A_MINUS: 7,
    RatingScale.BBB_PLUS: 8,
    RatingScale.BBB: 9,
    RatingScale.BBB_MINUS: 10,
    RatingScale.BB_PLUS: 11,
    RatingScale.BB: 12,
    RatingScale.BB_MINUS: 13,
    RatingScale.B_PLUS: 14,
    RatingScale.B: 15,
    RatingScale.B_MINUS: 16,
    RatingScale.CCC_PLUS: 17,
    RatingScale.CCC: 18,
    RatingScale.CCC_MINUS: 19,
    RatingScale.CC: 20,
    RatingScale.C: 21,
    RatingScale.D: 22,
}


@dataclass
class CreditRating:
    """Credit rating for an entity."""
    entity_id: str = ""
    rating: RatingScale = RatingScale.BBB
    agency: RatingAgency = RatingAgency.INTERNAL
    rating_date: date = field(default_factory=date.today)
    outlook: str = "stable"
    
    def validate(self) -> bool:
        return bool(self.entity_id)
    
    def get_pd(self) -> float:
        """Get probability of default (annual, decimal)."""
        bps = RATING_PD_MAP.get(self.rating, 100)
        return bps / 10000
    
    def get_score(self) -> int:
        """Get numeric rating score."""
        return RATING_SCORE_MAP.get(self.rating, 10)
    
    def is_investment_grade(self) -> bool:
        """Check if investment grade."""
        return self.get_score() <= 10
    
    def is_speculative(self) -> bool:
        """Check if speculative grade."""
        return 11 <= self.get_score() <= 16
    
    def is_distressed(self) -> bool:
        """Check if distressed."""
        return self.get_score() >= 17


@dataclass
class RatingHistory:
    """Historical ratings for an entity."""
    entity_id: str = ""
    history: List[Tuple[date, RatingScale]] = field(default_factory=list)
    
    def validate(self) -> bool:
        return bool(self.entity_id)
    
    def add_rating(self, rating_date: date, rating: RatingScale) -> None:
        """Add a rating to history."""
        self.history.append((rating_date, rating))
        self.history.sort(key=lambda x: x[0])
    
    def get_rating_at_date(self, as_of: date) -> Optional[RatingScale]:
        """Get rating as of a specific date."""
        for d, r in reversed(self.history):
            if d <= as_of:
                return r
        return None
    
    def get_upgrades(self) -> int:
        """Count number of upgrades."""
        if len(self.history) < 2:
            return 0
        
        upgrades = 0
        for i in range(1, len(self.history)):
            prev_score = RATING_SCORE_MAP.get(self.history[i-1][1], 10)
            curr_score = RATING_SCORE_MAP.get(self.history[i][1], 10)
            if curr_score < prev_score:
                upgrades += 1
        
        return upgrades
    
    def get_downgrades(self) -> int:
        """Count number of downgrades."""
        if len(self.history) < 2:
            return 0
        
        downgrades = 0
        for i in range(1, len(self.history)):
            prev_score = RATING_SCORE_MAP.get(self.history[i-1][1], 10)
            curr_score = RATING_SCORE_MAP.get(self.history[i][1], 10)
            if curr_score > prev_score:
                downgrades += 1
        
        return downgrades


@dataclass
class TransitionMatrix:
    """Rating transition matrix."""
    matrix_id: str = field(default_factory=lambda: f"TM-{uuid.uuid4().hex[:8].upper()}")
    time_horizon: float = 1.0
    ratings: List[RatingScale] = field(default_factory=list)
    probabilities: List[List[float]] = field(default_factory=list)
    
    def validate(self) -> bool:
        return len(self.ratings) == len(self.probabilities)
    
    def get_transition_prob(self, from_rating: RatingScale, to_rating: RatingScale) -> float:
        """Get transition probability."""
        if from_rating not in self.ratings or to_rating not in self.ratings:
            return 0.0
        
        from_idx = self.ratings.index(from_rating)
        to_idx = self.ratings.index(to_rating)
        
        return self.probabilities[from_idx][to_idx]
    
    def get_default_prob(self, from_rating: RatingScale) -> float:
        """Get probability of transitioning to default."""
        return self.get_transition_prob(from_rating, RatingScale.D)


def create_default_transition_matrix() -> TransitionMatrix:
    """Create a default transition matrix."""
    ratings = [
        RatingScale.AAA, RatingScale.AA, RatingScale.A,
        RatingScale.BBB, RatingScale.BB, RatingScale.B,
        RatingScale.CCC, RatingScale.D
    ]
    
    probs = [
        [0.9081, 0.0833, 0.0068, 0.0006, 0.0012, 0.0000, 0.0000, 0.0000],
        [0.0070, 0.9065, 0.0779, 0.0064, 0.0006, 0.0014, 0.0002, 0.0000],
        [0.0009, 0.0227, 0.9105, 0.0552, 0.0074, 0.0026, 0.0001, 0.0006],
        [0.0002, 0.0033, 0.0595, 0.8693, 0.0530, 0.0117, 0.0012, 0.0018],
        [0.0003, 0.0014, 0.0067, 0.0773, 0.8053, 0.0884, 0.0100, 0.0106],
        [0.0000, 0.0011, 0.0024, 0.0043, 0.0648, 0.8346, 0.0407, 0.0521],
        [0.0022, 0.0000, 0.0022, 0.0130, 0.0238, 0.1124, 0.6486, 0.1978],
        [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 1.0000],
    ]
    
    return TransitionMatrix(
        ratings=ratings,
        probabilities=probs,
        time_horizon=1.0
    )


__all__ = [
    "RatingAgency",
    "RatingScale",
    "RATING_PD_MAP",
    "RATING_SCORE_MAP",
    "CreditRating",
    "RatingHistory",
    "TransitionMatrix",
    "create_default_transition_matrix",
]
