import json
from unittest.mock import patch

import pytest

from market import MarketDataError, fetch_latest_daily


def _series_payload():
    return {
        "Time Series (Daily)": {
            "2026-03-09": {
                "1. open": "100.0",
                "2. high": "110.0",
                "3. low": "99.0",
                "4. close": "105.5",
                "5. volume": "123456",
            },
            "2026-03-10": {
                "1. open": "105.5",
                "2. high": "111.0",
                "3. low": "104.0",
                "4. close": "108.25",
                "5. volume": "222000",
            },
        }
    }


def test_fetch_latest_picks_newest_date():
    with patch("market._http_get", return_value=_series_payload()):
        bar = fetch_latest_daily("aapl", "demo", sleep_fn=lambda _: None)
    assert bar.symbol == "AAPL"
    assert bar.date == "2026-03-10"
    assert bar.close == 108.25
    assert bar.volume == 222000


def test_rate_limit_note_retries_then_succeeds():
    payloads = [{"Note": "throttle"}, _series_payload()]
    sleeps = []
    with patch("market._http_get", side_effect=payloads):
        bar = fetch_latest_daily("AAPL", "demo", sleep_fn=sleeps.append)
    assert bar.close == 108.25
    assert sleeps == [1]


def test_error_message_raises():
    with patch("market._http_get", return_value={"Error Message": "bad symbol"}):
        with pytest.raises(MarketDataError, match="bad symbol"):
            fetch_latest_daily("ZZZZ", "demo", sleep_fn=lambda _: None)


def test_symbol_uppercased():
    with patch("market._http_get", return_value=_series_payload()):
        bar = fetch_latest_daily("aapl", "demo", sleep_fn=lambda _: None)
    assert bar.symbol == "AAPL"
