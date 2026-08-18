import pytest

from platform_core.contracts.models import Evidence
from platform_core.settings.config import Settings
from scenarios.churn.retrieval import DatabricksRetrievalAdapter, RetrievalAdapterUnavailable

CORPUS = {
    ("notes_vs", "7590-VHVEG"): [["note-0001", "usage dropped significantly last cycle"]],
    ("notes_vs", "stable-customer-1"): [["note-0002", "consistent usage, no complaints"]],
    ("tickets_vs", "7590-VHVEG"): [["ticket-0001", "asked about switching to a cheaper plan"]],
    ("tickets_vs", "stable-customer-1"): [],
}

PLAYBOOKS = [
    ["action-usage-drop-outreach", "proactive outreach for customers with a usage drop"],
    ["action-stable-checkin", "routine check-in for long-tenured customers"],
]


class FakeRetrievalWorkspace:
    def query_index(self, index_name, *, columns, query_text, filters, num_results):
        if index_name == "playbooks_vs":
            assert filters is None
            return {"result": {"data_array": PLAYBOOKS}}
        assert filters is not None
        customer_id = filters["customer_id"]
        return {"result": {"data_array": CORPUS.get((index_name, customer_id), [])}}


def _adapter() -> DatabricksRetrievalAdapter:
    return DatabricksRetrievalAdapter(
        workspace=FakeRetrievalWorkspace(),
        settings=Settings(
            databricks_sql_warehouse_id="warehouse-1",
            databricks_catalog="mlworkflow_dev",
            vector_search_endpoint="churn-retrieval-endpoint",
        ),
    )


def test_retrieve_customer_evidence_returns_usage_drop_note_and_ticket() -> None:
    evidence = _adapter().retrieve_customer_evidence("7590-VHVEG")

    assert all(isinstance(item, Evidence) for item in evidence)
    excerpts = [item.excerpt for item in evidence]
    assert any("usage dropped" in excerpt for excerpt in excerpts)
    assert any("cheaper plan" in excerpt for excerpt in excerpts)
    source_types = {item.source_type for item in evidence}
    assert source_types == {"note", "ticket"}


def test_retrieve_customer_evidence_does_not_leak_another_customers_notes() -> None:
    evidence = _adapter().retrieve_customer_evidence("stable-customer-1")

    excerpts = [item.excerpt for item in evidence]
    assert not any("usage dropped" in excerpt for excerpt in excerpts)
    assert any("consistent usage" in excerpt for excerpt in excerpts)


def test_retrieve_playbooks_returns_usage_drop_action_by_content() -> None:
    evidence = _adapter().retrieve_playbooks("customer usage dropped, on month-to-month plan")

    assert all(item.source_type == "playbook" for item in evidence)
    excerpts = [item.excerpt for item in evidence]
    assert any("usage drop" in excerpt for excerpt in excerpts)


def test_from_settings_unavailable_without_vector_search_endpoint() -> None:
    with pytest.raises(RetrievalAdapterUnavailable):
        DatabricksRetrievalAdapter.from_settings(
            Settings(databricks_sql_warehouse_id="warehouse-1", vector_search_endpoint="")
        )


def test_from_settings_unavailable_without_warehouse_id() -> None:
    with pytest.raises(RetrievalAdapterUnavailable):
        DatabricksRetrievalAdapter.from_settings(
            Settings(
                databricks_sql_warehouse_id=None,
                vector_search_endpoint="churn-retrieval-endpoint",
            )
        )
