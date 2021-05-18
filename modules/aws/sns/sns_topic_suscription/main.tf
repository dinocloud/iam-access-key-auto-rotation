resource "aws_sns_topic_subscription" "lambda_target" {
  topic_arn = var.topic_arn
  protocol  = var.protocol
  endpoint  = var.endpoint
}