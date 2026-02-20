variable "project_name" {
  type    = string
  default = "stock-tracker"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "table_name" {
  type    = string
  default = "stock_ohlc"
}

variable "sns_topic_name" {
  type    = string
  default = "stock-price-alerts"
}

variable "alert_email" {
  type        = string
  description = "Email that must confirm the SNS subscription"
}

variable "alpha_vantage_api_key" {
  type      = string
  sensitive = true
}

variable "retention_days" {
  type    = number
  default = 90
}

variable "watchlist_json" {
  type        = string
  description = "JSON array of {symbol, upper, lower}"
  default     = "[{\"symbol\":\"AAPL\",\"upper\":230,\"lower\":180},{\"symbol\":\"MSFT\",\"upper\":450,\"lower\":350}]"
}
