# Databricks notebook source
# ruff: noqa: F821
"""Download and write the canonical Telco source into the environment bronze schema."""

import pandas as pd

dbutils.widgets.text("catalog", "mlworkflow_dev")
catalog = dbutils.widgets.get("catalog")
source_url = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.bronze")
source_frame = pd.read_csv(source_url)
raw = spark.createDataFrame(source_frame.to_dict(orient="records"))
assert raw.count() == 7043, f"unexpected Telco row count: {raw.count()}"
raw.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.bronze.telco_customer_churn"
)
print(f"wrote {catalog}.bronze.telco_customer_churn")
