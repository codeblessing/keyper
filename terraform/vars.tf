variable "location" {
    description = "The Azure Region in which all resources will be created."
    default     = "Sweden Central"
}

variable "name" {
    description = "The name of the application."
    default     = "hotdogornot"
}

variable "environment" {
    description = "The environment in which the application will be deployed."
    default     = "dev001"
}
