module "aws_config_rule" {
  source              = "../../aws/aws_config"
  name                = var.config_name
  input_parameters    = var.input_parameters
  source_identifier   = var.source_identifier
  tags                = var.tags
}

module "cloudwatch_event_rule" {
  source              = "../../aws/cloudwatch/event_rule"
  name                = var.cloudwatch_event_name
  config_rule_arn     = module.aws_config_rule.rule
  tags                = var.tags
}

module "cloudwatch_event_target" {
  source                      = "../../aws/cloudwatch/event_target"
  cloudwatch_event_rule_name  = module.cloudwatch_event_rule.cloudwatch_event_rule_name
  target_id                   = var.target_id
  sns_arn                     = module.sns_topic.arn
}

module "sns_topic" {
  source              = "../../aws/sns/sns_topic"
  name                = var.sns_topic_name
}

module "sns_topic_suscription" {
  source              = "../../aws/sns/sns_topic_suscription"
  topic_arn           = module.sns_topic.arn
  protocol            = var.protocol
  endpoint            = module.lambda_access_key_rotation.arn
}

resource "aws_iam_role_policy" "keys_rotation_policy" {
  name = var.lambda_policy_name
  role = aws_iam_role.iam_for_lambda.id

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
           "iam:ListAccessKeys",
           "secretsmanager:GetSecretValue",
           "secretsmanager:DescribeSecret",
           "secretsmanager:UpdateSecret",
           "secretsmanager:CreateSecret",
           "secretsmanager:PutSecretValue",
           "secretsmanager:TagResource",
           "secretsmanager:ListSecrets"
        ],
        Effect   = "Allow",
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role" "iam_for_lambda" {
  name = var.lambda_role_name

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

  tags          = var.tags
}

data "archive_file" "zip" {
  type        = "zip"
  source_file = "${path.module}/access-key-rotation.py"
  output_path = "${path.module}/access-key-rotation.zip"
}

module "lambda_access_key_rotation" {
  source              = "../../aws/lambda/lambda_function"
  zip_file            = data.archive_file.zip.output_path
  function_name       = var.lambda_funcion_name
  role_arn            = aws_iam_role.iam_for_lambda.arn
  handler             = var.handler
  runtime             = var.runtime
  tags                = var.tags
  source_arn          = module.sns_topic.arn
}

module "ses_access_key_rotation" {
  source              = "../../aws/ses/aws_ses_email_identity"
  mails_count         = var.emails_count
  emails_list         = var.emails_list
}