variable "name" {
    default = "config-rule-access-keys"
}

variable "description" {
    default = "A config rule that checks whether the active access keys are rotated within the number of days specified in maxAccessKeyAge. The rule is NON_COMPLIANT if the access keys have not been rotated for more than maxAccessKeyAge number of days."
}

variable "input_parameters" {
    default = "{\"maxAccessKeyAge\":\"90\"}"
}

variable "source_identifier" {}

variable "tags" {}