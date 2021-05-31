## access key rotation
variable "input_parameters" { 
    default = "{\"maxAccessKeyAge\":\"90\"}"
}

variable "target_id" {
    default = "SNS"
}

variable "handler" {
    default = "access-key-rotation.lambda_handler"
}

variable "runtime" {
    default = "python3.8"
}

variable "application" {
    default = "DinoCloud"
}

variable "environment" {
    default = "test"
}