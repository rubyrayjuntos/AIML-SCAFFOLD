# Databricks notebook source
# ruff: noqa: F821
"""Create the project-owned dev catalog objects required by the workflow."""

dbutils.widgets.text("catalog", "mlworkflow_dev")
catalog = dbutils.widgets.get("catalog")

spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
for schema in ("bronze", "silver", "gold", "ml", "ops"):
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.`{schema}`")

spark.sql(
    f"""
    CREATE TABLE IF NOT EXISTS `{catalog}`.`ops`.feature_registry (
      feature_version STRING NOT NULL,
      feature_contract STRING NOT NULL,
      feature_schema_json STRING NOT NULL,
      builder STRING NOT NULL,
      source_datasets ARRAY<STRING> NOT NULL,
      registered_at TIMESTAMP NOT NULL,
      owner STRING NOT NULL
    ) USING DELTA
    """
)
print(f"bootstrapped {catalog} and workflow schemas")
