variable "location" {
    description = "Default Azure Region to create resources in."
    default     = "Sweden Central"
}

variable "service-plan-location" {
    description = "Azure is very picky with available SKUs for educational plan, but forgets to list allowed regions, so here's one that (temporarily) works."
    default = "East US"
}

variable "name" {
    description = "Application name."
    default     = "keyper"
}

variable "environment" {
    description = "Deployment environment for application."
    default     = "dev"
}
