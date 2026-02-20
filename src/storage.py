"""DynamoDB persistence: one item per symbol per trading day, 90-day TTL."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from market import DailyBar


def _table(name: str, region: str):
    import boto3

    return boto3.resource("dynamodb", region_name=region).Table(name)


def _ttl_epoch(retention_days: int) -> int:
    expires = datetime.now(timezone.utc) + timedelta(days=retention_days)
    return int(expires.timestamp())


def put_bar(table_name: str, region: str, bar: DailyBar, retention_days: int) -> None:
    item = {
        "symbol": bar.symbol,
        "date": bar.date,
        "open": str(bar.open),
        "high": str(bar.high),
        "low": str(bar.low),
        "close": str(bar.close),
        "volume": bar.volume,
        "ttl": _ttl_epoch(retention_days),
    }
    _table(table_name, region).put_item(Item=item)


def previous_close(table_name: str, region: str, symbol: str, before_date: str) -> float | None:
    """Most recent stored close strictly before `before_date`, if any."""
    from boto3.dynamodb.conditions import Key
    from botocore.exceptions import ClientError

    try:
        resp = _table(table_name, region).query(
            KeyConditionExpression=Key("symbol").eq(symbol) & Key("date").lt(before_date),
            ScanIndexForward=False,
            Limit=1,
        )
    except ClientError as exc:
        raise RuntimeError(f"DynamoDB query failed: {exc}") from exc
    items = resp.get("Items") or []
    if not items:
        return None
    return float(items[0]["close"])
