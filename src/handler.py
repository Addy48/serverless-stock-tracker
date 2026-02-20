"""AWS Lambda entry: fetch -> DynamoDB -> threshold SNS."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Lambda zip layout puts these modules next to handler.py
sys.path.append(str(Path(__file__).resolve().parent))

from alerts import crossed_band, publish_alert
from config import load_settings
from market import MarketDataError, fetch_latest_daily
from storage import previous_close, put_bar

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    settings = load_settings()
    results = []
    failures = []

    for item in settings.watchlist:
        try:
            bar = fetch_latest_daily(item.symbol, settings.api_key)
            prior = previous_close(settings.table_name, settings.region, bar.symbol, bar.date)
            put_bar(settings.table_name, settings.region, bar, settings.retention_days)
            reason = crossed_band(bar, item, prior)
            alert_id = None
            if reason:
                alert_id = publish_alert(
                    settings.sns_topic_arn,
                    settings.region,
                    subject=f"Stock alert: {bar.symbol}",
                    message=reason,
                    bar=bar,
                )
            results.append(
                {
                    "symbol": bar.symbol,
                    "date": bar.date,
                    "close": bar.close,
                    "alert": reason,
                    "sns_message_id": alert_id,
                }
            )
            logger.info("processed %s close=%s alert=%s", bar.symbol, bar.close, bool(reason))
        except (MarketDataError, RuntimeError, ValueError) as exc:
            logger.exception("failed %s", item.symbol)
            failures.append({"symbol": item.symbol, "error": str(exc)})

    status = 200 if not failures else 207
    return {
        "statusCode": status,
        "body": json.dumps({"ok": results, "errors": failures}),
    }
