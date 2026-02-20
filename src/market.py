"""Alpha Vantage daily OHLCV fetch with backoff for the free-tier rate limit."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

ALPHA_URL = "https://www.alphavantage.co/query"
MAX_ATTEMPTS = 4
BACKOFF_SECONDS = (1, 4, 12)


@dataclass(frozen=True)
class DailyBar:
    symbol: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class MarketDataError(RuntimeError):
    pass


def _http_get(url: str, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "serverless-stock-tracker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise MarketDataError(f"HTTP {exc.code} from Alpha Vantage") from exc
    except urllib.error.URLError as exc:
        raise MarketDataError(f"network error: {exc.reason}") from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise MarketDataError("Alpha Vantage returned non-JSON") from exc
    if not isinstance(payload, dict):
        raise MarketDataError("unexpected Alpha Vantage payload")
    return payload


def fetch_latest_daily(symbol: str, api_key: str, sleep_fn=time.sleep) -> DailyBar:
    """Return the most recent completed daily bar for `symbol`."""
    params = urllib.parse.urlencode(
        {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",
            "apikey": api_key,
        }
    )
    url = f"{ALPHA_URL}?{params}"
    last_error: Exception | None = None

    for attempt in range(MAX_ATTEMPTS):
        payload = _http_get(url)
        note = payload.get("Note") or payload.get("Information")
        if note:
            last_error = MarketDataError(str(note))
            if attempt < MAX_ATTEMPTS - 1:
                sleep_fn(BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)])
                continue
            raise last_error

        series = payload.get("Time Series (Daily)")
        if not series:
            err = payload.get("Error Message") or "missing Time Series (Daily)"
            raise MarketDataError(f"{symbol}: {err}")

        date = sorted(series.keys())[-1]
        row = series[date]
        try:
            return DailyBar(
                symbol=symbol.upper(),
                date=date,
                open=float(row["1. open"]),
                high=float(row["2. high"]),
                low=float(row["3. low"]),
                close=float(row["4. close"]),
                volume=int(float(row["5. volume"])),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise MarketDataError(f"{symbol}: malformed OHLC row") from exc

    raise last_error or MarketDataError(f"{symbol}: exhausted retries")
