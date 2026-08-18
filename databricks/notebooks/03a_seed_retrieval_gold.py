# Databricks notebook source
# ruff: noqa: F821
"""Seed the notes, tickets, and playbook gold tables retrieval indexes are built over.

Content is authored (not synthetic customers) and keyed to real customer_ids already
present in gold.churn_features/gold.churn_labels, per the same no-invented-customers
discipline the training workflow follows - there is no real notes/tickets source for
the Telco dataset, so this is the narrowest deviation from that rule the retrieval
capability can be proven with.
"""
from pyspark.sql import Row

dbutils.widgets.text("catalog", "mlworkflow_dev")
catalog = dbutils.widgets.get("catalog")

USAGE_DROP_CUSTOMER = "7590-VHVEG"  # verified real: used throughout this repo's tests/runbook

# Pick a real, distinct, stable-profile customer dynamically rather than hardcoding a
# second guessed ID - guarantees join-validity against gold.churn_features by
# construction. churn_features already carries churned (0/1, per 02_build_silver.py's
# transform) alongside tenure/Contract, so no join against churn_labels is needed.
features = spark.table(f"{catalog}.gold.churn_features")
stable_row = (
    features.where(
        (features.churned == 0)
        & (features.customer_id != USAGE_DROP_CUSTOMER)
        & (features.tenure_months >= 24)
        & (features.Contract == "Two year")
    )
    .select("customer_id")
    .limit(1)
    .collect()
)
assert stable_row, "no stable-profile customer found in gold.churn_features"
STABLE_CUSTOMER = stable_row[0]["customer_id"]

known_customers = {row["customer_id"] for row in features.select("customer_id").collect()}
assert USAGE_DROP_CUSTOMER in known_customers
assert STABLE_CUSTOMER in known_customers

notes = spark.createDataFrame(
    [
        Row(
            note_id="note-0001",
            customer_id=USAGE_DROP_CUSTOMER,
            created_at="2026-07-15",
            author="support-agent-12",
            note_text=(
                "Customer reported a significant drop in monthly usage over the last "
                "billing cycle and asked about switching to a lower-cost plan. Flagged "
                "as a usage-drop risk signal for the retention team."
            ),
        ),
        Row(
            note_id="note-0002",
            customer_id=STABLE_CUSTOMER,
            created_at="2026-06-02",
            author="support-agent-04",
            note_text=(
                "Long-tenured customer on a two-year contract, no recent complaints, "
                "consistent usage pattern. No retention action needed."
            ),
        ),
    ]
)
notes.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.gold.customer_notes"
)
spark.sql(
    f"ALTER TABLE {catalog}.gold.customer_notes "
    "SET TBLPROPERTIES (delta.enableChangeDataFeed = true)"
)

tickets = spark.createDataFrame(
    [
        Row(
            ticket_id="ticket-0001",
            customer_id=USAGE_DROP_CUSTOMER,
            created_at="2026-07-16",
            severity="medium",
            status="closed",
            description=(
                "Customer called in asking why their usage dropped and whether a "
                "cheaper plan was available. Agent explained plan options; customer "
                "did not commit to downgrading."
            ),
        ),
    ]
)
tickets.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.gold.support_tickets"
)
spark.sql(
    f"ALTER TABLE {catalog}.gold.support_tickets "
    "SET TBLPROPERTIES (delta.enableChangeDataFeed = true)"
)

playbooks = spark.createDataFrame(
    [
        Row(
            action_id="action-usage-drop-outreach",
            title="Proactive usage-drop outreach",
            description=(
                "For customers with a recent significant usage decline on a "
                "month-to-month contract, proactively offer a retention discount or "
                "plan review call before they churn."
            ),
            trigger_conditions="usage_drop",
            segment_applicability="month_to_month",
            plan_tier_applicability="any",
            expected_outcome="reduced churn risk via proactive engagement",
            steps=(
                "1. Identify usage-drop signal. 2. Offer plan review call. "
                "3. Present retention discount if eligible."
            ),
            owner="retention-team",
            version="1",
            effective_at="2026-01-01",
        ),
        Row(
            action_id="action-stable-checkin",
            title="Routine long-tenure check-in",
            description=(
                "For stable, long-tenured customers with no risk signals, a light-touch "
                "periodic check-in maintains satisfaction without over-contacting."
            ),
            trigger_conditions="none",
            segment_applicability="two_year_contract",
            plan_tier_applicability="any",
            expected_outcome="sustained satisfaction, no action required",
            steps="1. Send quarterly satisfaction survey. 2. No proactive outreach unless flagged.",
            owner="customer-success",
            version="1",
            effective_at="2026-01-01",
        ),
        Row(
            action_id="action-support-escalation",
            title="Escalate repeated support contact",
            description=(
                "Customers with multiple support tickets in a short window should be "
                "escalated to a senior agent regardless of usage pattern."
            ),
            trigger_conditions="repeated_tickets",
            segment_applicability="any",
            plan_tier_applicability="any",
            expected_outcome="faster resolution, reduced frustration-driven churn",
            steps="1. Detect >=2 tickets in 30 days. 2. Route to senior agent queue.",
            owner="support-team",
            version="1",
            effective_at="2026-01-01",
        ),
    ]
)
playbooks.write.mode("overwrite").option("overwriteSchema", True).saveAsTable(
    f"{catalog}.gold.recommended_actions"
)
spark.sql(
    f"ALTER TABLE {catalog}.gold.recommended_actions "
    "SET TBLPROPERTIES (delta.enableChangeDataFeed = true)"
)

assert (
    spark.table(f"{catalog}.gold.customer_notes")
    .where(f"customer_id = '{USAGE_DROP_CUSTOMER}'")
    .count()
    >= 1
)
print(
    f"seeded gold.customer_notes ({notes.count()} rows), "
    f"gold.support_tickets ({tickets.count()} rows), "
    f"gold.recommended_actions ({playbooks.count()} rows); "
    f"usage_drop_customer={USAGE_DROP_CUSTOMER} stable_customer={STABLE_CUSTOMER}"
)
