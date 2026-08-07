terraform {
  required_version = ">= 1.6.0"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 4.0" }
  }
}

provider "azurerm" {
  features {}
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "location" {
  type    = string
  default = "eastus"
}

variable "unique_suffix" {
  type = string
}

resource "azurerm_log_analytics_workspace" "logs" {
  name                = "mlwf-${var.environment}-${var.unique_suffix}-logs"
  location            = var.location
  resource_group_name = data.azurerm_resource_group.target.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "prod" ? 90 : 30
}

data "azurerm_resource_group" "target" {
  name = "replace-me"
}

resource "azurerm_storage_account" "landing" {
  name                            = "mlwf${var.unique_suffix}${var.environment}"
  resource_group_name             = data.azurerm_resource_group.target.name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  public_network_access_enabled   = var.environment != "prod"
  allow_nested_items_to_be_public = false
}
