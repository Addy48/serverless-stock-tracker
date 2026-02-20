"""SNS publish when a close crosses a configured band."""

from __future__ import annotations

import json

from config import WatchItem
from market import DailyBar


def crossed_band(bar: DailyBar, item: WatchItem, prev_close: float | None) -> str | None:
    """
    Fire only on a cross, not while price sits past the band.

    If there is no prior close, treat today's print as the first observation
    and alert when it is already through a threshold.
    """
    close = bar.close
    if item.upper is not None:
        if prev_close is None and close >= item.upper:
            return f"{bar.symbol} close {close:.2f} is at/above upper band {item.upper:.2f}"
        if prev_close is not None and prev_close < item.upper <= close:
            return (
                f"{bar.symbol} crossed above {item.upper:.2f} "
                f"({prev_close:.2f} -> {close:.2f}) on {bar.date}"
            )
    if item.lower is not None:
        if prev_close is None and close <= item.lower:
            return f"{bar.symbol} close {close:.2f} is at/below lower band {item.lower:.2f}"
        if prev_close is not None and prev_close > item.lower >= close:
            return (
                f"{bar.symbol} crossed below {item.lower:.2f} "
                f"({prev_close:.2f} -> {close:.2f}) on {bar.date}"
            )
    return None


def publish_alert(topic_arn: str, region: str, subject: str, message: str, bar: DailyBar) -> str:
    if not topic_arn:
        raise RuntimeError("SNS_TOPIC_ARN is not set")
    import boto3

    client = boto3.client("sns", region_name=region)
    resp = client.publish(
        TopicArn=topic_arn,
        Subject=subject[:100],
        Message=message,
        MessageAttributes={
            "symbol": {"DataType": "String", "StringValue": bar.symbol},
            "date": {"DataType": "String", "StringValue": bar.date},
            "payload": {
                "DataType": "String",
                "StringValue": json.dumps(
                    {
                        "symbol": bar.symbol,
                        "date": bar.date,
                        "close": bar.close,
                    }
                ),
            },
        },
    )
    return resp["MessageId"]
