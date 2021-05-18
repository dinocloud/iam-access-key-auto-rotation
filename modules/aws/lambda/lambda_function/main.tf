resource "aws_lambda_function" "lambda" {
  filename      = var.zip_file
  function_name = var.function_name
  role          = var.role_arn
  handler       = var.handler

  # source_code_hash = filebase64sha256("access-key-rotation.zip")

  runtime       = var.runtime
  
  tags          = var.tags
}

resource "aws_lambda_permission" "with_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = var.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = var.source_arn
}