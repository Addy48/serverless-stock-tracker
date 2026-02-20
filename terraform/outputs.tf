output "lambda_name" {
  value = aws_lambda_function.tracker.function_name
}

output "dynamodb_table" {
  value = aws_dynamodb_table.ohlc.name
}

output "sns_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "schedule" {
  value = aws_cloudwatch_event_rule.weekday_close.schedule_expression
}
