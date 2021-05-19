resource "aws_cloudwatch_event_rule" "compliance_change" {
  name          = var.name
  event_pattern = <<PATTERN
{
  "source": [
    "aws.config"
  ],
  "detail-type": [
    "Config Rules Compliance Change"
  ],
  "detail": {
    "configRuleARN": [
      "${var.config_rule_arn}"
    ],
    "messageType": [
      "ComplianceChangeNotification"
    ],
    "configRuleName": [
      "DinoCloud-test-access-key-config-rule"
    ],
    "newEvaluationResult": {
      "complianceType": [
        "NON_COMPLIANT"
      ]
    }
  }
}
PATTERN

  tags          = var.tags
}