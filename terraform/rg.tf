resource "azurerm_resource_group" "rg" {
  name     = "rg-myapp-sdc-dev-001"
  location = "Sweden Central"

  tags = {
    contact = "Jakub Wozniak"
  }
}
