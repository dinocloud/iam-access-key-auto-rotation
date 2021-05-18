variable "config_name" {}

variable "source_identifier" {
    default = "ACCESS_KEYS_ROTATED"
}

variable "input_parameters" {}

variable "tags" {}

variable "cloudwatch_event_name" {}

variable "target_id" {}

variable "sns_topic_name" {}

variable "lambda_policy_name" {
    default = "access_key_lambda_policy"
}

variable "lambda_role_name" {
    default = "AWSRoleForLambdaAccessKeysRotation"
}

variable "lambda_funcion_name" {
    default = "access_key_rotation"
}

variable "handler" {}

variable "runtime" {}

variable "emails_count" {}

variable "emails_list" {}

variable "protocol" {
    default = "lambda"
}

variable "zip_file" {
    default = "access-key-rotation.zip"
}