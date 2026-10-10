"""SA-CCR supervisory duration (Basel CRE52.34) and IR product SA-CCR smoke tests."""

from datetime import date

import numpy as np
import pytest

from qlrisk.data import create_sample_market_data
from qlrisk.products.base import Currency, SACCRParameters
import qlrisk.products.python as P


def test_supervisory_duration_formula():
    assert SACCRParameters.supervisory_duration(0, 5) == pytest.approx((1 - np.exp(-0.25)) / 0.05)
    assert SACCRParameters.supervisory_duration(1, 6) == pytest.approx((np.exp(-0.05) - np.exp(-0.3)) / 0.05)


def test_supervisory_option_delta():
    assert SACCRParameters.calculate_option_delta(True, 100, 100, 1.0, 0.2) == pytest.approx(0.5398, abs=1e-4)
    assert SACCRParameters.calculate_option_delta(False, 100, 100, 1.0, 0.2) == pytest.approx(-0.4602, abs=1e-4)


def test_ir_products_compute_saccr():
    md = create_sample_market_data(date(2026, 10, 9))
    d0, mat = md.valuation_date, date(2031, 10, 9)
    trades = [
        P.InterestRateSwap("IRS", d0, d0, mat, 1e7, Currency.USD, "CP", fixed_rate=0.04),
        P.OvernightIndexSwap("OIS", d0, d0, mat, 1e7, Currency.USD, "CP", fixed_rate=0.04),
        P.InterestRateFloor("FLR", d0, d0, mat, 1e7, Currency.USD, "CP", strike=0.03),
        P.InterestRateCap("CAP", d0, d0, mat, 1e7, Currency.USD, "CP", strike=0.05),
        P.ForwardRateAgreement("FRA", d0, date(2027, 4, 7), date(2027, 4, 9), date(2027, 10, 9), 1e7, Currency.USD, "CP", fra_rate=0.04),
        P.BasisSwap("BAS", d0, d0, mat, 1e7, Currency.USD, "CP"),
        P.Swaption("SWO", d0, date(2027, 10, 9), date(2027, 10, 9), mat, 1e7, Currency.USD, "CP", strike=0.04),
    ]
    for t in trades:
        assert t.calculate_saccr(md).ead > 0, t.trade_id
