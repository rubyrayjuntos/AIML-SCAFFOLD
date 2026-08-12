terraform {
  # The first approved bootstrap apply uses local state because this container does not
  # exist yet. Immediately afterward, migrate state here with the reviewed backend config.
  backend "azurerm" {}
}
