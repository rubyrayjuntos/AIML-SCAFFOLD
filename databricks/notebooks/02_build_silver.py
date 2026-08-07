# Databricks notebook source
# ruff: noqa: F821
"""Normalize and validate the canonical Telco source."""

dbutils.widgets.text("catalog", "mlworkflow_dev")
catalog = dbutils.widgets.get("catalog")
source = spark.table(f"{catalog}.bronze.telco_customer_churn")
assert source.select("customerID").where("customerID IS NULL").count() == 0
silver = source.withColumnRenamed("customerID", "customer_id").withColumnRenamed(
    "Churn", "churned"
)
silver = silver.withColumnRenamed("tenure", "tenure_months")
silver = silver.withColumn(
    "TotalCharges",
    __import__("pyspark.sql.functions", fromlist=["regexp_replace"])
    .regexp_replace("TotalCharges", "^\\s*$", "0")
    .cast("double"),
)
silver = silver.withColumn(
    "churned",
    __import__("pyspark.sql.functions", fromlist=["when"])
    .when(silver.churned == "Yes", 1)
    .otherwise(0)
    .cast("int"),
)
silver.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.silver.telco_customers"
)
assert silver.select("customer_id").distinct().count() == 7043
print(f"wrote {catalog}.silver.telco_customers")
