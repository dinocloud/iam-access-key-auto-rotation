variable "zip_file" {
    default = "access-key-rotation.zip"
}

variable "function_name" {
    default = "lambda-function"
}

variable "role_arn" {}

variable "handler" {
    default = "lambda_function.lambda_handler"
}

variable "runtime" {
    default = "python3.8"
}

variable "tags" {}

variable "source_arn" {}