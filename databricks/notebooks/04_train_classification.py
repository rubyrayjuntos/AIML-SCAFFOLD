# Databricks notebook source
# ruff: noqa: F821
"""Train, evaluate, register, and record lineage for the churn candidate."""

import json
import os
from datetime import UTC, datetime

import mlflow
import mlflow.sklearn
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

dbutils.widgets.text("catalog", "mlworkflow_dev")
dbutils.widgets.text("environment", "dev")
catalog = dbutils.widgets.get("catalog")
environment = dbutils.widgets.get("environment")
features = spark.table(f"{catalog}.gold.churn_features")
row_count = features.select("customer_id").distinct().count()
assert row_count == 7043, f"data contract failed: expected 7043 customers, got {row_count}"

model_name = f"{catalog}.ml.churn_classifier"
feature_columns = [
    "tenure_months",
    "MonthlyCharges",
    "TotalCharges",
    "SeniorCitizen",
    "Contract",
    "InternetService",
    "TechSupport",
]
frame = features.select("customer_id", *feature_columns, "churned").toPandas()
X = frame[feature_columns]
y = frame["churned"].astype(int)
categorical = ["Contract", "InternetService", "TechSupport"]
numeric = [column for column in feature_columns if column not in categorical]
preprocessor = ColumnTransformer(
    [
        ("numeric", StandardScaler(), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical),
    ]
)
model = LogisticRegression(max_iter=500, class_weight="balanced")
pipeline = __import__("sklearn.pipeline", fromlist=["Pipeline"]).Pipeline(
    [("preprocess", preprocessor), ("model", model)]
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "databricks"))
mlflow.set_registry_uri(os.getenv("MLFLOW_REGISTRY_URI", "databricks-uc"))
mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT_NAME", "/Shared/enterprise-ml-workflow"))
with mlflow.start_run(run_name="churn-logistic-regression") as run:
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    probabilities = pipeline.predict_proba(X_test)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "f1": float(f1_score(y_test, predictions)),
        "auc": float(roc_auc_score(y_test, probabilities)),
    }
    mlflow.log_params(
        {"task_type": "classification", "feature_schema_version": "churn.features.v1"}
    )
    mlflow.log_metrics(metrics)
    mlflow.set_tags(
        {
            "source_dataset": f"{catalog}.gold.churn_features",
            "source_row_count": str(row_count),
            "environment": environment,
            "workflow_stage": "training",
        }
    )
    mlflow.log_dict(
        {
            "feature_table": f"{catalog}.gold.churn_features",
            "label_table": f"{catalog}.gold.churn_labels",
            "row_count": row_count,
            "feature_schema_version": "churn.features.v1",
            "trained_at": datetime.now(UTC).isoformat(),
        },
        "training_context.json",
    )
    mlflow.sklearn.log_model(pipeline, "model")
    registered = mlflow.register_model(f"runs:/{run.info.run_id}/model", model_name)
    print(json.dumps({"run_id": run.info.run_id, "version": registered.version, **metrics}))
