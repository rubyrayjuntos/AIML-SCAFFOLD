from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from platform_core.contracts.models import ScoreResponse
from platform_core.settings.config import Settings


class ServingAdapterUnavailable(RuntimeError):
    """Raised when the local process is not configured for live serving."""


class ServingWorkspace(Protocol):
    def query_features(self, customer_id: str) -> dict[str, Any]: ...

    def query_endpoint(self, endpoint: str, features: dict[str, Any]) -> Any: ...

    def endpoint_version(self, endpoint: str) -> str: ...


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "as_dict"):
        return value.as_dict()
    return {}


def _prediction_value(response: Any) -> float:
    payload = _as_dict(response)
    predictions = payload.get("predictions", response)
    if isinstance(predictions, list):
        predictions = predictions[0] if predictions else None
    if isinstance(predictions, list):
        predictions = predictions[-1]
    if isinstance(predictions, dict):
        predictions = predictions.get("score", predictions.get("prediction"))
    if predictions is None:
        raise ServingAdapterUnavailable("Databricks serving response has no prediction")
    score = float(predictions)
    if not 0 <= score <= 1:
        raise ServingAdapterUnavailable("Databricks serving response is outside [0, 1]")
    return score


@dataclass
class DatabricksServingAdapter:
    workspace: ServingWorkspace
    settings: Settings

    @classmethod
    def from_settings(cls, settings: Settings) -> DatabricksServingAdapter:
        if not settings.databricks_sql_warehouse_id:
            raise ServingAdapterUnavailable("DATABRICKS_SQL_WAREHOUSE_ID is not configured")

        from databricks.sdk import WorkspaceClient

        return cls(
            workspace=_DatabricksWorkspace(
                WorkspaceClient(),
                catalog=settings.databricks_catalog,
                warehouse_id=settings.databricks_sql_warehouse_id,
            ),
            settings=settings,
        )

    def score(self, customer_id: str, request_id: str) -> ScoreResponse:
        features = self.workspace.query_features(customer_id)
        score = _prediction_value(
            self.workspace.query_endpoint(self.settings.model_serving_endpoint, features)
        )
        version = self.workspace.endpoint_version(self.settings.model_serving_endpoint)
        return ScoreResponse(
            entity_id=customer_id,
            score=score,
            drivers=features,
            model_version=version,
            served_version=version,
            feature_version=self.settings.feature_schema_version,
            feature_contract=self.settings.feature_contract,
            request_id=request_id,
        )


class _DatabricksWorkspace:
    def __init__(self, client: Any, *, catalog: str, warehouse_id: str) -> None:
        self.client = client
        self.catalog = catalog
        self.warehouse_id = warehouse_id

    def query_features(self, customer_id: str) -> dict[str, Any]:
        escaped_id = customer_id.replace("'", "''")
        statement = f"""
            SELECT tenure_months, MonthlyCharges, TotalCharges, SeniorCitizen,
                   Contract, InternetService, TechSupport
            FROM `{self.catalog}`.`gold`.churn_features
            WHERE customer_id = '{escaped_id}'
            LIMIT 1
        """
        response = self.client.statement_execution.execute_statement(
            warehouse_id=self.warehouse_id,
            statement=statement,
            catalog=self.catalog,
            schema="gold",
            wait_timeout="30s",
        )
        result = _as_dict(response).get("result", getattr(response, "result", None))
        rows = _as_dict(result).get("data_array", getattr(result, "data_array", None))
        if not rows:
            raise ServingAdapterUnavailable(f"No governed features found for {customer_id}")
        columns = [
            "tenure_months",
            "MonthlyCharges",
            "TotalCharges",
            "SeniorCitizen",
            "Contract",
            "InternetService",
            "TechSupport",
        ]
        return dict(zip(columns, rows[0], strict=True))

    def query_endpoint(self, endpoint: str, features: dict[str, Any]) -> Any:
        return self.client.serving_endpoints.query(
            name=endpoint,
            dataframe_records=[features],
        )

    def endpoint_version(self, endpoint: str) -> str:
        response = self.client.serving_endpoints.get(endpoint)
        payload = _as_dict(response)
        config = payload.get("config", {})
        entities = config.get("served_entities", [])
        if entities:
            version = entities[0].get("entity_version")
            if version:
                return str(version)
        raise ServingAdapterUnavailable(f"No served model version found for {endpoint}")
