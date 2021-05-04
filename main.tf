terraform {
  required_version = "~> 0.14"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket  = "terraform-access-key-rotation"
    key     = "infra_rotation_keys.tfstate"
    region  = "us-east-1"
    encrypt = true
    profile = "default"
  }
}

provider "aws" {
  region  = "us-east-1"
  profile = "default"
}

locals {
  tags = {
    createdBy = "pedro/sol"
    project   = "POC"
    env       = "test"
    purpose   = "Automated Key Rotation"
  }

  mails = [ "pedro.bratti@dinocloudconsulting.com",
            "sol.malisani@dinocloudconsulting.com"
          ]
}

# Create Config Rule access_key_rotated
resource "aws_config_config_rule" "rule" {
  name             = "access-keys-rotated"
  description      = "A config rule that checks whether the active access keys are rotated within the number of days specified in maxAccessKeyAge. The rule is NON_COMPLIANT if the access keys have not been rotated for more than maxAccessKeyAge number of days."
  input_parameters = "{\"maxAccessKeyAge\":\"90\"}"
  
  source {
    owner             = "AWS"
    source_identifier = "ACCESS_KEYS_ROTATED"
  }
  
  scope {
    compliance_resource_types = []
  }
  
  tags            = local.tags
}

# Create Event Rule for non-compliant objects and associated with config rule
resource "aws_cloudwatch_event_rule" "compliance_change" {
  name          = "AWSCloudWatchEventRulePoC"
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
      "${aws_config_config_rule.rule.arn}"
    ],
    "newEvaluationResult": {
            "complianceType": [
                "NON_COMPLIANT"
            ]
        }
  }
}
PATTERN

  tags          = local.tags
}

# Create CW Event Target for CW Event Rule
resource "aws_cloudwatch_event_target" "sns" {
  rule      = aws_cloudwatch_event_rule.compliance_change.name
  target_id = "SNS"
  arn       = aws_sns_topic.sns_lambda.arn
}

# Create SNS CloudWatch Event Target
resource "aws_sns_topic" "sns_lambda" {
  name            = "AWSKeyRotationPOC"
  delivery_policy = <<EOF
{
  "http": {
    "defaultHealthyRetryPolicy": {
      "minDelayTarget": 20,
      "maxDelayTarget": 20,
      "numRetries": 3,
      "numMaxDelayRetries": 0,
      "numNoDelayRetries": 0,
      "numMinDelayRetries": 0,
      "backoffFunction": "linear"
    },
    "disableSubscriptionOverrides": false,
    "defaultThrottlePolicy": {
      "maxReceivesPerSecond": 1
    }
  }
}
EOF
}

# topic subscription to lambda
resource "aws_sns_topic_subscription" "lambda_target" {
  topic_arn = aws_sns_topic.sns_lambda.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.iam_lambda.arn
}

# IAM Role Policy Lambda
resource "aws_iam_role_policy" "keys_rotation_policy" {
  name = "test_policy"
  role = aws_iam_role.iam_for_lambda.id

  # Terraform's "jsonencode" function converts a
  # Terraform expression result to valid JSON syntax.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
           "ses:SendEmail",
           "iam:DeleteAccessKey",
           "logs:CreateLogStream",
           "ses:SendRawEmail",
           "iam:UpdateAccessKey",
           "iam:ListUsers",
           "logs:CreateLogGroup",
           "logs:PutLogEvents",
           "iam:ListUserTags",
           "iam:CreateAccessKey",
           "iam:ListAccessKeys"
        ],
        Effect   = "Allow",
        Resource = "*"
      },
    ]
  })
}

# IAM Role Lambda
resource "aws_iam_role" "iam_for_lambda" {
  name = "AWSRoleForLambdaAccessKeysRotationPocTEST_2"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })

  tags          = local.tags
}

# Lambda Fuction Python 3.8
resource "aws_lambda_function" "iam_lambda" {
  filename      = "access-key-rotation.zip"
  function_name = "access-key-rotation"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "lambda_function.lambda_handler"

  # source_code_hash = filebase64sha256("access-key-rotation.zip")

  runtime = "python3.8"
  
  tags          = local.tags
}

# SES Para envio de mails
resource "aws_ses_email_identity" "ses_mails" {
  count     = length(local.mails)
  email = local.mails[count.index]
}


# Outputs
output "rule" {
  value = aws_config_config_rule.rule.arn
}

output "sns_lambda" {
  value = aws_sns_topic.sns_lambda.arn
}