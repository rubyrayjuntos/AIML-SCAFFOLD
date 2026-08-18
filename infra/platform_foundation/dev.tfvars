tenant_id       = "90a7175b-82cd-4815-9050-8cbae3a1d234"
subscription_id = "5b452321-32fd-4b1c-8bbf-6d69a5a587ad"
location        = "eastus"

# gh-aiml-scaffold-platform-oidc service principal (ADR 0014's factory identity).
# Was gh-azure-ai-ml-ops-r1-dev-oidc (c5618b4d-...) until ADR 0014's correction -
# that identity is shared with the generated project's own OIDC credential, so
# granting it platform-foundation RBAC would have let the generated project
# inherit factory-administration access through the same principal.
apply_principal_object_id = "c70e78b4-2113-4465-9797-894241713eb9"

# id-azure-ai-ml-ops-dev-compute (R1's existing Azure ML compute identity)
compute_principal_object_id = "150826ec-5b3b-4cf0-96e2-f585b8ca55b0"
