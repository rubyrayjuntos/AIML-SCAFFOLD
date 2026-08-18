from pathlib import Path

import yaml

WORKFLOW_FILES = [
    "platform-foundation-plan.yml",
    "platform-foundation-apply.yml",
]


def _run_steps_containing(workflow_path: Path, needle: str) -> list[str]:
    workflow = yaml.safe_load(workflow_path.read_text())
    matches = []
    for job in workflow["jobs"].values():
        for step in job["steps"]:
            run = step.get("run")
            if run and needle in run:
                matches.append(run)
    return matches


def test_state_pull_failures_are_never_masked() -> None:
    """Regression test for the autonomous-review fallback found in R3.2's PR.

    `terraform state pull` against a genuinely nonexistent backend key still
    exits 0 with a freshly-generated empty document - there is no "state
    does not exist" error case to gracefully degrade from. A `|| echo '{}'`
    (or any other fallback) after `state pull` therefore only serves to mask
    real failures (auth, network, backend outage, wrong credentials) as fake
    empty state, undermining independent state verification. See the R3.2
    plan's execution log for the live test that established this.
    """
    workflows_dir = Path(".github/workflows")
    found_any = False
    for filename in WORKFLOW_FILES:
        path = workflows_dir / filename
        assert path.exists(), f"expected workflow file missing: {path}"
        matches = _run_steps_containing(path, "state pull")
        assert matches, f"{filename} no longer calls `terraform state pull` - update this test"
        found_any = True
        for run in matches:
            state_pull_line = next(line for line in run.splitlines() if "state pull" in line)
            assert "||" not in state_pull_line, (
                f"{filename}: `state pull` must not have a `||` fallback - "
                f"it would mask a real failure as empty state: {state_pull_line!r}"
            )
    assert found_any
