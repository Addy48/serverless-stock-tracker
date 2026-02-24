# Serverless Stock Tracker & Notifier

Event-driven market monitor on AWS. A Lambda function pulls daily OHLCV from [Alpha Vantage](https://www.alphavantage.co/), writes the last 90 days into DynamoDB, and publishes an SNS email when a watched symbol **crosses** a price band.

Live schedule: **21:30 UTC, Monday–Friday** (after the NYSE cash close).

## Architecture

```
EventBridge cron (21:30 UTC, weekdays)
        │
        ▼
   AWS Lambda (Python 3.12)
        │
        ├── GET Alpha Vantage  TIME_SERIES_DAILY
        ├── PUT  DynamoDB      PK=symbol  SK=date  TTL=90d
        └── SNS Publish        only on a band cross
                    │
                    ▼
              confirmed email
```

| Piece | Role |
|-------|------|
| **EventBridge** | `cron(30 21 ? * MON-FRI *)` |
| **Lambda** | Fetch, persist, decide, publish |
| **DynamoDB** | On-demand table, composite key, TTL |
| **SNS** | Email topic, confirm-to-subscribe |
| **Terraform** | Entire stack in `terraform/` |
| **IAM** | PutItem + Query on one table, Publish on one topic, CloudWatch logs |

## Why a “cross”, not “currently above”

If AAPL is already at 210 and the upper band is 200, you do not want mail every weekday. The function stores yesterday’s close and fires only when price **moves through** the band (`prev < upper <= today`, or the inverse for the floor). First-ever print for a symbol still alerts if it opens already through the band.

## Repository layout

```
src/                 Lambda source (zipped by Terraform)
  handler.py         entry
  market.py          Alpha Vantage + backoff
  storage.py         DynamoDB put / previous close
  alerts.py          cross detection + SNS
  config.py          env / watchlist JSON
terraform/           S3-less IaC: DDB, SNS, IAM, Lambda, EventBridge
tests/               pytest, no AWS account required
```

## Watchlist

JSON array in `WATCHLIST_JSON` (Lambda env, set from Terraform):

```json
[
  {"symbol": "AAPL", "upper": 230, "lower": 180},
  {"symbol": "MSFT", "upper": 450, "lower": 350}
]
```

`upper` / `lower` may be omitted.

## Local tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Against a live AWS stack (after `terraform apply` and a `.env` copied from `.env.example`):

```bash
PYTHONPATH=src python3 scripts/local_invoke.py
```

## Deploy

1. Create a free Alpha Vantage key.
2. Copy `terraform/terraform.tfvars.example` → `terraform/terraform.tfvars` and fill `alert_email` + `alpha_vantage_api_key`.
3. Confirm the SNS subscription email AWS sends you (alerts stay pending until you do).
4. Apply:

```bash
cd terraform
terraform init
terraform apply
```

5. Optional smoke invoke:

```bash
aws lambda invoke \
  --function-name stock-tracker-daily \
  --payload '{}' \
  /tmp/stock-tracker-out.json
cat /tmp/stock-tracker-out.json
```

Free-tier Alpha Vantage is tightly rate-limited (a handful of calls per minute, a small daily cap). The client backs off on the provider’s `Note` / `Information` throttle payload. Keep the watchlist short.

## DynamoDB item

| Attribute | Type | Meaning |
|-----------|------|---------|
| `symbol` | S | Partition key |
| `date` | S | Sort key, `YYYY-MM-DD` |
| `open` `high` `low` `close` | S | Decimal stored as strings |
| `volume` | N | Shares |
| `ttl` | N | Unix epoch, 90 days from write |

## License

MIT. See `LICENSE`.
