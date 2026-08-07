# Databricks notebook source
# ruff: noqa: F821
"""Download and write the canonical Telco source into the environment bronze schema."""

dbutils.widgets.text("catalog", "mlworkflow_dev")
catalog = dbutils.widgets.get("catalog")
source_url = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.bronze")
raw = spark.read.option("header", True).option("inferSchema", True).csv(source_url)
assert raw.count() == 7043, f"unexpected Telco row count: {raw.count()}"
raw.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.bronze.telco_customer_churn"
)
print(f"wrote {catalog}.bronze.telco_customer_churn")
