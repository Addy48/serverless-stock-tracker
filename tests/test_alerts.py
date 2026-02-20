from alerts import crossed_band
from config import WatchItem
from market import DailyBar


def _bar(close: float, date: str = "2026-03-10") -> DailyBar:
    return DailyBar("AAPL", date, close, close, close, close, 1_000)


def test_cross_above_uses_prior_close():
    item = WatchItem("AAPL", upper=200.0, lower=None)
    reason = crossed_band(_bar(201.0), item, prev_close=199.0)
    assert reason is not None
    assert "crossed above" in reason


def test_already_above_does_not_realert():
    item = WatchItem("AAPL", upper=200.0, lower=None)
    assert crossed_band(_bar(210.0), item, prev_close=205.0) is None


def test_cross_below():
    item = WatchItem("AAPL", upper=None, lower=150.0)
    reason = crossed_band(_bar(149.0), item, prev_close=151.0)
    assert reason is not None
    assert "crossed below" in reason


def test_first_observation_alerts_if_through_band():
    item = WatchItem("AAPL", upper=200.0, lower=None)
    reason = crossed_band(_bar(205.0), item, prev_close=None)
    assert reason is not None
