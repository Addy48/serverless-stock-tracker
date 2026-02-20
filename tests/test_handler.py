import json
import os
from unittest.mock import patch

from market import DailyBar


def test_handler_writes_and_alerts(monkeypatch):
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "demo")
    monkeypatch.setenv("TABLE_NAME", "stock_ohlc")
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123:alerts")
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv(
        "WATCHLIST_JSON",
        json.dumps([{"symbol": "AAPL", "upper": 200, "lower": 100}]),
    )

    bar = DailyBar("AAPL", "2026-03-10", 201, 202, 199, 201.5, 1000)

    with (
        patch("handler.fetch_latest_daily", return_value=bar),
        patch("handler.previous_close", return_value=199.0),
        patch("handler.put_bar") as put,
        patch("handler.publish_alert", return_value="mid-1") as pub,
    ):
        from handler import lambda_handler

        resp = lambda_handler({}, None)

    assert resp["statusCode"] == 200
    body = json.loads(resp["body"])
    assert body["ok"][0]["sns_message_id"] == "mid-1"
    put.assert_called_once()
    pub.assert_called_once()
