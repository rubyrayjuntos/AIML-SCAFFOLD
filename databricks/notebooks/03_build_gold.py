# Databricks notebook source
# ruff: noqa: F821
"""Build the governed churn feature and label tables."""

dbutils.widgets.text("catalog", "mlworkflow_dev")
catalog = dbutils.widgets.get("catalog")
silver = spark.table(f"{catalog}.silver.telco_customers")
gold = silver.select(
    "customer_id",
    "tenure_months",
    "MonthlyCharges",
    "TotalCharges",
    "SeniorCitizen",
    "Contract",
    "InternetService",
    "TechSupport",
    "churned",
)
gold.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.gold.churn_features"
)
gold.select("customer_id", "churned").write.mode("overwrite").option(
    "overwriteSchema", True
).saveAsTable(f"{catalog}.gold.churn_labels")
assert gold.select("customer_id").distinct().count() == 7043
print(f"wrote {catalog}.gold.churn_features and churn_labels")
