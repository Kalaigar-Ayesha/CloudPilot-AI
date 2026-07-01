provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = "cloudpilot-resources"
  location = "East US"
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "cloudpilot-aks-cluster"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  dns_prefix          = "cloudpilotaks"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D2s_v3"
  }

  identity {
    type = "SystemAssigned"
  }
}

output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}
