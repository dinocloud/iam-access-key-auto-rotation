resource "aws_config_config_rule" "rule" {
  name             = var.name
  description      = var.description
  input_parameters = var.input_parameters
  
  source {
    owner             = "AWS"
    source_identifier = var.source_identifier
  }
  
  scope {
    compliance_resource_types = []
  }
  
  tags            = var.tags
}