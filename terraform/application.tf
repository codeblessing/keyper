resource "azurerm_storage_account" "appcode" {
  name                     = "${var.name}${var.environment}storage"
  resource_group_name      = azurerm_resource_group.keyper.name
  location                 = azurerm_resource_group.keyper.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_log_analytics_workspace" "laworkspace" {
  name                = "${var.name}${var.environment}workspace"
  location            = azurerm_resource_group.keyper.location
  resource_group_name = azurerm_resource_group.keyper.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_application_insights" "application_insights" {
  name                = "${var.name}${var.environment}appinsights"
  location            = azurerm_resource_group.keyper.location
  resource_group_name = azurerm_resource_group.keyper.name
  application_type    = "other"
  workspace_id        = azurerm_log_analytics_workspace.laworkspace.id
}


resource "azurerm_service_plan" "app_service_plan" {
  name                = "${var.name}${var.environment}serviceplan"
  resource_group_name = azurerm_resource_group.keyper.name
  location            = var.service-plan-location
  os_type             = "Linux"
  sku_name            = "Y1"
}

resource "azurerm_linux_function_app" "function_app" {
  name                = "${var.name}-app-${var.environment}"
  resource_group_name = azurerm_resource_group.keyper.name
  location            = var.service-plan-location

  service_plan_id = azurerm_service_plan.app_service_plan.id

  storage_account_name       = azurerm_storage_account.appcode.name
  storage_account_access_key = azurerm_storage_account.appcode.primary_access_key

  app_settings = {
    "WEBSITE_RUN_FROM_PACKAGE"       = "",
    "FUNCTIONS_WORKER_RUNTIME"       = "python",
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.application_insights.instrumentation_key,
    "AzureWebJobsFeatureFlags"       = "EnableWorkerIndexing"

    "KEYPER_PHOTOS_CONTAINER_URL"      = azurerm_storage_account.photos.primary_blob_endpoint
    "KEYPER_PHOTOS_CONTAINER_NAME"     = azurerm_storage_container.photos.name
    "KEYPER_PHOTOS_TABLE_URL"          = azurerm_storage_account.photos.primary_table_endpoint
    "KEYPER_PHOTOS_TABLE_NAME"         = azurerm_storage_table.photos.name
    "KEYPER_PHOTOS_QUEUE_URL"          = azurerm_storage_account.photos.primary_queue_endpoint
    "KEYPER_PHOTOS_QUEUE_NAME"         = azurerm_storage_queue.photoqueue.name
    "KEYPER_PHOTOS_ACCOUNT_ACCESS_KEY" = azurerm_storage_account.photos.primary_access_key
    "KEYPER_PHOTOS_ACCOUNT_NAME"       = azurerm_storage_account.photos.name
    "KEYPER_PHOTOS_CONNECTION_STRING"            = azurerm_storage_account.photos.primary_connection_string

    "KEYPER_COGNITIVE_URL" = azurerm_cognitive_account.cognitive.endpoint
    "KEYPER_COGNITIVE_KEY" = azurerm_cognitive_account.cognitive.primary_access_key

  }

  site_config {
    always_on = false
    application_stack {
      python_version = "3.10"
    }
  }

  lifecycle {
    ignore_changes = [
      app_settings["WEBSITE_RUN_FROM_PACKAGE"],
    ]
  }
}

