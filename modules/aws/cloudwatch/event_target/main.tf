resource "aws_cloudwatch_event_target" "sns" {
  rule      = var.cloudwatch_event_rule_name
  target_id = var.target_id
  arn       = var.sns_arn
}