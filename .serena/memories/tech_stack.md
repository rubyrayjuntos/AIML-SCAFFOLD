Python >=3.12, package layout `src/` (setuptools, packages found under `src`).

Core deps: fastapi, pydantic v2, pydantic-settings, databricks-sdk, uvicorn[standard].
Optional `dev` extra: httpx, pytest, ruff, pyyaml.
Optional `ml` extra: mlflow, pandas, scikit-learn.

Ruff: line-length 100, target py312, lint selects E/F/I/UP.
Pytest: testpaths=`tests`, pythonpath=`src`, addopts `-q`.

IaC: Bicep (authoritative) + Terraform (portability-only, separate state) — see `mem:invariants`.
Databricks: Asset Bundles (`DATABRICKS_BUNDLE_ROOT=databricks`).
Local dev scoring adapter reads Gold features via `DATABRICKS_SQL_WAREHOUSE_ID`, auth via Databricks CLI/default credential chain (no stored tokens).
