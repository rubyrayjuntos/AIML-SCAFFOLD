# R1 local generation runbook

This runbook validates the AIML-SCAFFOLD R1 factory without changing cloud state.

## Prepare

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Use a real product manifest for live acceptance. The checked-in example contains placeholder shared-resource identifiers and is intended for contract and generation testing.

## Validate, plan, and generate

```bash
aiml-scaffold validate examples/manifests/r1-ml-batch.yaml --allow-experimental
aiml-scaffold plan examples/manifests/r1-ml-batch.yaml \
  --environment dev \
  --output /tmp/resolved-plan.json \
  --allow-experimental
aiml-scaffold generate examples/manifests/r1-ml-batch.yaml \
  --output /tmp/example-risk \
  --platform-source-commit "$PLATFORM_SOURCE_COMMIT" \
  --platform-package-digest "$PLATFORM_PACKAGE_DIGEST" \
  --allow-experimental
aiml-scaffold doctor /tmp/example-risk --environment dev --no-cloud
```

The explicit preview opt-in is required until the generated evidence path completes its Dev clean-room proof and is promoted to stable. Remove `--no-cloud` for authenticated read-only checks only after replacing the example's placeholder tenant, deployment subscription, backend, federated credential, and deployment-identity configuration. Export the manifest-named client and object ID environment variables before that check.

Doctor reports `passed`, `failed`, `warning`, `not_exercised`, or `not_applicable` for each boundary. A local user identity that differs from the intended GitHub identity is a warning, not proof of GitHub authorization. Backend management-plane visibility, container existence, and Entra data-plane reads are separate results. State writes/locks and GitHub OIDC token exchange remain `not_exercised`; only the reviewed Terraform and GitHub workflows can prove them.

Inspect `validate` and `plan` maturity output before generation. It separately reports release status, manifest policy, CLI override use, authorization, and the remaining `dev_live_pending` boundary.

## Static conformance

```bash
python -m pip install -c /tmp/example-risk/constraints.txt -e '/tmp/example-risk[dev]'
ruff check /tmp/example-risk
pytest -q /tmp/example-risk
terraform -chdir=/tmp/example-risk/infra/terraform fmt -check -recursive
terraform -chdir=/tmp/example-risk/infra/terraform init -backend=false -lockfile=readonly
terraform -chdir=/tmp/example-risk/infra/terraform validate
actionlint /tmp/example-risk/.github/workflows/*.yml
```

Also parse all YAML, scan for secrets and scenario leakage, generate a second independent tree, and compare every byte. Runtime caches and Terraform working data are not tracked generated files and are excluded from receipt verification.

Verify that `platform/source-manifest.yaml`, `platform/resolved-plan.json`, and `constraints.txt` are tracked by the generated-files digest and independently attested by `generation-receipt.json`. Do not edit these files in a generated repository; change the source manifest or platform template and regenerate.

Release candidates must supply the full source commit of the platform package and the SHA-256 digest of the exact wheel used to generate them. Generated live workflows reject receipts without both fields.

## Live boundary

Authenticated `doctor` is read-only. Terraform apply, Azure ML job submission, endpoint changes, invocation, and resource destruction require separate approval. Local or static success must not be recorded as Dev-live evidence.

## Documentation changelog

| Version | Created | Modified | Who | Notes |
|---|---|---|---|---|
| 1.0.0-rc4 | 2026-08-11 | 2026-08-12 | Ray Swan / Codex | Required exact platform source-commit and wheel-digest provenance for release-candidate generation. |
| 1.0.0-rc3 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Documented explicit Azure context, deployment identity configuration, tri-state doctor outcomes, and unexercised OIDC/write boundaries. |
| 1.0.0-rc2 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Added maturity review, provenance verification, and constrained generated-project installation. |
| 1.0.0-rc1 | 2026-08-11 | 2026-08-11 | Ray Swan / Codex | Initial local generation and static conformance runbook. |
