resource "azurerm_resource_group" "keyper" {
  name     = "rg-${var.name}-${var.environment}"
  location = var.location

  tags = {
    course = "Projektowanie Systemów Rozproszonych",
    year = "2024",
    contact = "Jakub Kwiatkowski",
  }
}
