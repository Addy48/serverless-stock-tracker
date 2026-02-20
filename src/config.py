"""Runtime config from Lambda environment / .env."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WatchItem:
    symbol: str
    upper: float | None
    lower: float | None


@dataclass(frozen=True)
class Settings:
    api_key: str
    table_name: str
    sns_topic_arn: str
    region: str
    retention_days: int
    watchlist: tuple[WatchItem, ...]


def _parse_watchlist(raw: str) -> tuple[WatchItem, ...]:
    data = json.loads(raw or "[]")
    if not isinstance(data, list) or not data:
        raise ValueError("WATCHLIST_JSON must be a non-empty JSON array")
    items: list[WatchItem] = []
    for row in data:
        symbol = str(row.get("symbol", "")).strip().upper()
        if not symbol:
            raise ValueError("each watchlist row needs a symbol")
        upper = row.get("upper")
        lower = row.get("lower")
        items.append(
            WatchItem(
                symbol=symbol,
                upper=float(upper) if upper is not None else None,
                lower=float(lower) if lower is not None else None,
            )
        )
    return tuple(items)


def load_settings() -> Settings:
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ALPHA_VANTAGE_API_KEY is not set")
    return Settings(
        api_key=api_key,
        table_name=os.environ.get("TABLE_NAME", "stock_ohlc"),
        sns_topic_arn=os.environ.get("SNS_TOPIC_ARN", "").strip(),
        region=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1")),
        retention_days=int(os.environ.get("RETENTION_DAYS", "90")),
        watchlist=_parse_watchlist(os.environ.get("WATCHLIST_JSON", "")),
    )
