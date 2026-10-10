"""Tests for RiskFactorTimeSeries and the synthetic market history generator."""

from datetime import date, timedelta

import numpy as np
import pytest

from qlrisk.data import MarketHistoryGenerator, create_sample_market_data
from qlrisk.riskfactors import RiskFactorKey, RiskFactorTimeSeries, ShockType, apply_shocks

from conftest import VALUATION_DATE

D = [date(2026, 1, 1) + timedelta(days=i) for i in range(5)]


@pytest.fixture
def ts():
    return RiskFactorTimeSeries(D, ["IR.DISCOUNT.5Y", "EQ.AAPL"], [
        [0.040, 100.0],
        [0.041, 110.0],
        [np.nan, 121.0],
        [0.043, np.nan],
        [0.044, 133.1],
    ])


def test_construction_validates_and_sorts():
    with pytest.raises(ValueError):
        RiskFactorTimeSeries(D[:2], ["EQ.A"], [[1.0], [2.0], [3.0]])
    with pytest.raises(ValueError):
        RiskFactorTimeSeries([D[0], D[0]], ["EQ.A"], [[1.0], [2.0]])
    s = RiskFactorTimeSeries([D[1], D[0]], ["EQ.A"], [[2.0], [1.0]])
    assert s.dates == [D[0], D[1]] and list(s.series("EQ.A")) == [1.0, 2.0]


def test_values_are_read_only(ts):
    with pytest.raises(ValueError):
        ts.values[0, 0] = 1.0


def test_default_return_conventions(ts):
    dates, r = ts.returns()
    assert dates == D[1:]
    assert r[0, 0] == pytest.approx(0.001)                 # rates: absolute
    assert r[0, 1] == pytest.approx(np.log(1.1))           # prices: log
    assert np.isnan(r[1, 0]) and np.isnan(r[3, 1])          # gaps propagate as NaN


def test_return_overrides_and_horizon(ts):
    _, r = ts.returns(horizon=2, return_types={"EQ.AAPL": ShockType.RELATIVE})
    assert r.shape == (3, 2)
    assert r[0, 1] == pytest.approx(0.21)
    dates, r = ts.returns(horizon=2, overlapping=False)
    assert dates == [D[2], D[4]]


def test_fill_missing(ts):
    ff = ts.fill_missing("ffill")
    assert ff.series("IR.DISCOUNT.5Y")[2] == 0.041 and ff.series("EQ.AAPL")[3] == 121.0
    lin = ts.fill_missing("interpolate")
    assert lin.series("IR.DISCOUNT.5Y")[2] == pytest.approx(0.042)
    assert not ff.missing_counts()
    assert ts.missing_counts() == {RiskFactorKey.parse("IR.DISCOUNT.5Y"): 1, RiskFactorKey.parse("EQ.AAPL"): 1}


def test_proxy_replays_source_returns():
    s = RiskFactorTimeSeries(D[:4], ["EQ.SRC", "EQ.TGT"], [
        [100.0, np.nan], [110.0, 50.0], [121.0, np.nan], [133.1, np.nan]])
    p = s.proxy("EQ.TGT", "EQ.SRC", beta=1.0)
    assert list(p.series("EQ.TGT")) == pytest.approx([50 / 1.1, 50.0, 55.0, 60.5])


def test_window_select_append(ts):
    w = ts.window(D[1], D[3])
    assert w.dates == D[1:4]
    assert ts.select(["EQ.AAPL"]).shape == (5, 1)
    a = ts.append(date(2026, 2, 1), {"EQ.AAPL": 140.0})
    assert a.shape == (6, 2) and np.isnan(a.values[-1, 0])
    with pytest.raises(ValueError):
        ts.append(D[0], {})


def test_csv_round_trip(ts, tmp_path):
    path = tmp_path / "hist.csv"
    ts.to_csv(str(path))
    back = RiskFactorTimeSeries.from_csv(str(path))
    assert back.dates == ts.dates and back.factors == ts.factors
    np.testing.assert_array_equal(np.isnan(back.values), np.isnan(ts.values))
    np.testing.assert_allclose(np.nan_to_num(back.values), np.nan_to_num(ts.values))


def test_snapshots_and_market_data_round_trip():
    md = create_sample_market_data(VALUATION_DATE)
    md2 = apply_shocks(md, {"EQ.AAPL": 0.1}, ShockType.RELATIVE)
    md2.valuation_date = VALUATION_DATE + timedelta(days=1)
    s = RiskFactorTimeSeries.from_snapshots([(md.valuation_date, md), (md2.valuation_date, md2)])
    assert s.series("EQ.AAPL")[1] == pytest.approx(209.0)
    rebuilt = s.market_data_at(md2.valuation_date, md)
    assert rebuilt.equity_prices["AAPL"] == pytest.approx(209.0)
    assert rebuilt.valuation_date == md2.valuation_date
    assert md.equity_prices["AAPL"] == 190.0


def test_return_shocks_replay_a_day():
    md = create_sample_market_data(VALUATION_DATE)
    hist = MarketHistoryGenerator(seed=1).generate(md, num_days=20)
    dates, r = hist.returns()
    yesterday = hist.market_data_at(hist.dates[-2], md)
    replayed = apply_shocks(yesterday, hist.return_shocks(r[-1]))
    assert replayed.equity_prices["SPX"] == pytest.approx(md.equity_prices["SPX"])
    assert replayed.forward_curves["SOFR"][5.0] == pytest.approx(md.forward_curves["SOFR"][5.0])


# ------------------------------------------------------------ generator

def test_generator_ends_at_snapshot_and_is_reproducible():
    md = create_sample_market_data(VALUATION_DATE)
    a = MarketHistoryGenerator(seed=3).generate(md, num_days=100)
    b = MarketHistoryGenerator(seed=3).generate(md, num_days=100)
    np.testing.assert_array_equal(a.values, b.values)
    assert a.dates[-1] == VALUATION_DATE and all(d.weekday() < 5 for d in a.dates)
    last = a.levels_at(a.dates[-1])
    assert last[RiskFactorKey.parse("EQ.SPX")] == md.equity_prices["SPX"]


def test_generator_stress_regime_and_correlations():
    md = create_sample_market_data(VALUATION_DATE)
    h = MarketHistoryGenerator(seed=7).generate(md, num_days=750, stress_start=300, stress_days=60)
    _, r = h.returns()
    spx, vol, spread = h.column("EQ.SPX"), h.column("VOL.eq_vol.1Y"), h.column("CR.ACME.5Y")
    assert r[299:359, spx].std() > 2 * r[:299, spx].std()
    assert np.corrcoef(r[:, spx], r[:, vol])[0, 1] < -0.2
    assert np.corrcoef(r[:, spx], r[:, spread])[0, 1] < 0
    spreads = [h.column(k) for k in h.factors if k.field == "credit_curves"]
    assert (h.values[:, spreads] > 0).all()
