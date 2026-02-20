# Security

- Never commit `terraform/terraform.tfvars`, `.env`, or Alpha Vantage keys.
- Lambda IAM is scoped to one DynamoDB table and one SNS topic.
- SNS email subscriptions must be confirmed from the inbox; unconfirmed endpoints receive nothing.
- Rotate the Alpha Vantage key from the provider dashboard if it leaks.
