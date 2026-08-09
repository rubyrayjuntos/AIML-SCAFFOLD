# Databricks notebook source
# ruff: noqa: F821
"""Train, evaluate, register, and record lineage for the churn candidate."""

import json
import os
from datetime import datetime, timezone

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

dbutils.widgets.text("catalog", "mlworkflow_dev")
dbutils.widgets.text("environment", "dev")
dbutils.widgets.text("promotion_metric", "auc")
dbutils.widgets.text("minimum_improvement", "0.02")
dbutils.widgets.text("minimum_rows", "7043")
dbutils.widgets.text("feature_schema_version", "churn.features.v1")
dbutils.widgets.text("feature_contract", "churn_feature_contract_v1")
dbutils.widgets.text("git_sha", "local-dev")
catalog = dbutils.widgets.get("catalog")
environment = dbutils.widgets.get("environment")
promotion_metric = dbutils.widgets.get("promotion_metric")
minimum_improvement = float(dbutils.widgets.get("minimum_improvement"))
minimum_rows = int(dbutils.widgets.get("minimum_rows"))
feature_schema_version = dbutils.widgets.get("feature_schema_version")
feature_contract = dbutils.widgets.get("feature_contract")
git_sha = dbutils.widgets.get("git_sha")
features = spark.table(f"{catalog}.gold.churn_features")
row_count = features.select("customer_id").distinct().count()
assert row_count == minimum_rows, (
    f"data contract failed: expected {minimum_rows} customers, got {row_count}"
)

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

class_balance = {
    "positive_count": int(y.sum()),
    "negative_count": int((y == 0).sum()),
    "positive_rate": float(y.mean()),
}


def workflow_run_id() -> str:
    try:
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        run_id = context.currentRunId().get().id()
        return str(run_id)
    except Exception:
        return "interactive-run"

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
        {
            "task_type": "classification",
            "feature_schema_version": feature_schema_version,
            "feature_contract": feature_contract,
        }
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
            "feature_schema_version": feature_schema_version,
            "feature_contract": feature_contract,
            "trained_at": datetime.now(timezone.utc).isoformat(),  # noqa: UP017
            "class_balance": class_balance,
            "train_row_count": len(X_train),
            "test_row_count": len(X_test),
            "promotion_metric": promotion_metric,
            "minimum_improvement": minimum_improvement,
            "git_sha": git_sha,
            "workflow_run_id": workflow_run_id(),
        },
        "training_context.json",
    )
    mlflow.log_dict(
        {
            "metrics": metrics,
            "class_balance": class_balance,
            "train_row_count": len(X_train),
            "test_row_count": len(X_test),
            "data_quality_passed": row_count == minimum_rows,
            "promotion_metric": promotion_metric,
            "minimum_improvement": minimum_improvement,
        },
        "evaluation_summary.json",
    )
    signature = infer_signature(X_test, probabilities)
    mlflow.sklearn.log_model(
        pipeline,
        "model",
        pyfunc_predict_fn="predict_proba",
        signature=signature,
        input_example=X_test.head(1),
    )
    registered = mlflow.register_model(f"runs:/{run.info.run_id}/model", model_name)
    client = mlflow.tracking.MlflowClient()
    client.set_registered_model_alias(model_name, "challenger", registered.version)
    print(
        json.dumps(
            {
                "run_id": run.info.run_id,
                "version": registered.version,
                "model_name": model_name,
                "alias": "challenger",
                "feature_schema_version": feature_schema_version,
                "feature_contract": feature_contract,
                "source_row_count": row_count,
                "class_balance": class_balance,
                "train_row_count": len(X_train),
                "test_row_count": len(X_test),
                "promotion_metric": promotion_metric,
                "minimum_improvement": minimum_improvement,
                **metrics,
            }
        )
    )
