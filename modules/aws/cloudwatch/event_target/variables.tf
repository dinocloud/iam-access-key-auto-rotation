variable "cloudwatch_event_rule_name" {}

variable "sns_arn" {}

variable "target_id" {
    default = "SNS"
}