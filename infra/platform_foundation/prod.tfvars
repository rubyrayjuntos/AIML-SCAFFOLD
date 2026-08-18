# SCAFFOLD ONLY - not functionally exercised by R3.2. This file exists so
# platform-foundation-plan.yml/-apply.yml have a valid dispatch target for
# `environment: prod`, per the R3.2 plan's prod-scaffold-only decision.
#
# Known gap, deliberately not fixed here: infra/platform_foundation/main.tf's
# resource names (rg-aiml-platform-foundation-dev, dbw-aiml-platform-
# foundation-dev, etc.) are hardcoded with "-dev" in the name, not
# parameterized by environment. A real `terraform plan -var-file=prod.tfvars`
# right now would target those same dev-named resources under a separate
# state key (backend-prod.hcl) - not a safe or meaningful prod plan. Fixing
# this means parameterizing every resource name in main.tf by environment,
# which would itself force destroy/recreate on the already-live dev
# resources if done carelessly. That's real follow-on work for whenever prod
# actually needs to become real, not something to rush through as part of
# scaffolding the dispatch target.
#
# The placeholder principal IDs below are intentionally invalid (not real
# object IDs) so an accidental prod dispatch fails loudly at the Azure API
# rather than silently reusing dev's identities against dev's resources.

tenant_id       = "90a7175b-82cd-4815-9050-8cbae3a1d234"
subscription_id = "5b452321-32fd-4b1c-8bbf-6d69a5a587ad"
location        = "eastus"

apply_principal_object_id   = "00000000-0000-0000-0000-000000000000"
compute_principal_object_id = "00000000-0000-0000-0000-000000000000"
