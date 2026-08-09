import json
from pathlib import Path


def test_foundry_tools_are_read_only_and_allowlisted() -> None:
    contract = json.loads(Path("foundry/tools/tools.contract.json").read_text())
    assert contract["tools"]
    assert all(tool["mutates_data"] is False for tool in contract["tools"])
    assert {tool["name"] for tool in contract["tools"]} == {
        "get_customer_score",
        "get_customer_diff",
        "retrieve_customer_evidence",
        "retrieve_playbooks",
    }


def test_foundry_response_schema_matches_api_evidence_shape() -> None:
    schema = json.loads(Path("foundry/agents/assistant_response.schema.json").read_text())
    assert "entity_id" in schema["required"]
    assert schema["properties"]["evidence"]["items"]["type"] == "object"
    assert schema["additionalProperties"] is False
