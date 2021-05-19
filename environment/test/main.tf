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
    key     = "terraform-access-key-rotation.tfstate"
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
    createdBy   = "DinoCloud-pedro-sol"
    env         = "Production"
    purpose     = "Access Key Rotation"
    Terraform   = true
  }

  # emails a los qua vas a suscribir a SES
  emails_list = ["sol.malisani@dinocloudconsulting.com", "pedro.bratti@dinocloudconsulting.com"]

}

module "automated_key_rotation" {
  source                            = "../../modules/layers/automated_key_rotation"
  config_name                       = "${var.application}-${var.environment}-access-key-config-rule"
  input_parameters                  = var.input_parameters
  cloudwatch_event_name             = "${var.application}-${var.environment}-access-key-cloudwatch-event"
  target_id                         = var.target_id
  sns_topic_name                    = "${var.application}-${var.environment}-access-key-sns"
  lambda_policy_name                = "${var.application}-${var.environment}-access-key-lambda-policy"
  lambda_role_name                  = "${var.application}-${var.environment}-access-key-lambda-role"
  lambda_funcion_name               = "${var.application}-${var.environment}-access-key-lambda_function"
  handler                           = var.handler
  runtime                           = var.runtime
  emails_count                      = length(local.emails_list)
  emails_list                       = local.emails_list

  tags                              = local.tags
}