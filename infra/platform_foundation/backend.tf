terraform {
  # ADR 0012: independently-plannable state, separate from both the R1 bootstrap
  # state (../backend.tf) and any generated project's own state. The backend
  # container this points at (aiml-platform-foundation) was created by the
  # bootstrap root in R3.2 Step A - it already exists, so unlike the bootstrap
  # root's own first apply, this root never needs a local-state workaround.
  backend "azurerm" {}
}
