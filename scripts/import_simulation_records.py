#!/usr/bin/env python3
import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "db" / "sqlite_schema.sql"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def bool_int(value) -> int:
    return 1 if value else 0


def execute_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    ensure_column(conn, "leads", "customer_type", "TEXT")
    ensure_column(conn, "call_sessions", "campaign_id", "TEXT")


def ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def clear_tables(conn: sqlite3.Connection) -> None:
    for table in [
        "escalations",
        "appointments",
        "call_outcomes",
        "turn_decisions",
        "qualification_answers",
        "call_sessions",
        "leads",
        "sales_campaigns",
    ]:
        conn.execute(f"DELETE FROM {table}")


def insert_records(conn: sqlite3.Connection, records: dict) -> None:
    for campaign in records.get("sales_campaigns", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO sales_campaigns (
              campaign_id, client_name, product_name, product_category,
              customer_type, country_or_region, language, approved_opening,
              qualification_questions_json, allowed_claims_json,
              forbidden_claims_json, required_disclosures_json,
              escalation_triggers_json, scheduling_goal, human_handoff_role,
              compliance_notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                campaign["campaign_id"],
                campaign.get("client_name"),
                campaign.get("product_name"),
                campaign.get("product_category"),
                campaign.get("customer_type"),
                campaign.get("country_or_region"),
                campaign.get("language"),
                campaign.get("approved_opening"),
                dump_json(campaign.get("qualification_questions", [])),
                dump_json(campaign.get("allowed_claims", [])),
                dump_json(campaign.get("forbidden_claims", [])),
                dump_json(campaign.get("required_disclosures", [])),
                dump_json(campaign.get("escalation_triggers", [])),
                campaign.get("scheduling_goal"),
                campaign.get("human_handoff_role"),
                campaign.get("compliance_notes"),
                campaign.get("created_at"),
                campaign.get("updated_at"),
            ),
        )

    for lead in records.get("leads", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO leads (
              lead_id, customer_type, full_name, phone_number, email, company_name, role_title,
              source, region, language, contact_status, consent_status,
              do_not_call, do_not_call_reason, preferred_contact_time,
              owner_user_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead["lead_id"],
                lead.get("customer_type", "unknown"),
                lead.get("full_name"),
                lead.get("phone_number"),
                lead.get("email"),
                lead.get("company_name"),
                lead.get("role_title"),
                lead.get("source"),
                lead.get("region"),
                lead.get("language"),
                lead.get("contact_status"),
                lead.get("consent_status"),
                bool_int(lead.get("do_not_call")),
                lead.get("do_not_call_reason"),
                lead.get("preferred_contact_time"),
                lead.get("owner_user_id"),
                lead.get("created_at"),
                lead.get("updated_at"),
            ),
        )

    for session in records.get("call_sessions", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO call_sessions (
              call_id, campaign_id, lead_id, channel, started_at, ended_at, call_status,
              current_stage, current_interest_state, current_emotion_label,
              current_strategy, confidence, transcript_storage_mode,
              transcript_text, call_summary, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["call_id"],
                session.get("campaign_id"),
                session["lead_id"],
                session.get("channel"),
                session.get("started_at"),
                session.get("ended_at"),
                session.get("call_status"),
                session.get("current_stage"),
                session.get("current_interest_state"),
                session.get("current_emotion_label"),
                session.get("current_strategy"),
                session.get("confidence"),
                session.get("transcript_storage_mode"),
                session.get("transcript_text"),
                session.get("call_summary"),
                session.get("created_by"),
                session.get("created_at"),
            ),
        )

    for answer in records.get("qualification_answers", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO qualification_answers (
              answer_id, call_id, lead_id, stage, question_text, answer_text,
              normalized_answer_json, detected_emotion, interest_state_after_answer,
              selected_strategy, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                answer["answer_id"],
                answer["call_id"],
                answer["lead_id"],
                answer.get("stage"),
                answer.get("question_text"),
                answer.get("answer_text"),
                dump_json(answer.get("normalized_answer")),
                answer.get("detected_emotion"),
                answer.get("interest_state_after_answer"),
                answer.get("selected_strategy"),
                answer.get("confidence"),
                answer.get("created_at"),
            ),
        )

    for decision in records.get("turn_decisions", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO turn_decisions (
              decision_id, call_id, lead_id, turn_index, stage, detected_emotion,
              interest_state, selected_strategy, next_action, agent_response,
              confidence, rationale, guardrail_flags_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision["decision_id"],
                decision["call_id"],
                decision["lead_id"],
                decision.get("turn_index"),
                decision.get("stage"),
                decision.get("detected_emotion"),
                decision.get("interest_state"),
                decision.get("selected_strategy"),
                decision.get("next_action"),
                decision.get("agent_response"),
                decision.get("confidence"),
                decision.get("rationale"),
                dump_json(decision.get("guardrail_flags", [])),
                decision.get("created_at"),
            ),
        )

    for outcome in records.get("call_outcomes", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO call_outcomes (
              outcome_id, call_id, lead_id, call_status, interest_state,
              selected_strategy, appointment_scheduled, appointment_time,
              escalation_reason, call_summary, next_action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                outcome["outcome_id"],
                outcome["call_id"],
                outcome["lead_id"],
                outcome.get("call_status"),
                outcome.get("interest_state"),
                outcome.get("selected_strategy"),
                bool_int(outcome.get("appointment_scheduled")),
                outcome.get("appointment_time"),
                outcome.get("escalation_reason"),
                outcome.get("call_summary"),
                outcome.get("next_action"),
                outcome.get("created_at"),
            ),
        )

    for appointment in records.get("appointments", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO appointments (
              appointment_id, lead_id, call_id, scheduled_time, timezone,
              assigned_sales_agent_id, appointment_status, confirmation_text,
              calendar_event_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                appointment["appointment_id"],
                appointment["lead_id"],
                appointment["call_id"],
                appointment.get("scheduled_time"),
                appointment.get("timezone"),
                appointment.get("assigned_sales_agent_id"),
                appointment.get("appointment_status"),
                appointment.get("confirmation_text"),
                appointment.get("calendar_event_id"),
                appointment.get("created_at"),
                appointment.get("updated_at"),
            ),
        )

    for escalation in records.get("escalations", []):
        conn.execute(
            """
            INSERT OR REPLACE INTO escalations (
              escalation_id, lead_id, call_id, escalation_reason, severity,
              assigned_to, status, notes, created_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                escalation["escalation_id"],
                escalation["lead_id"],
                escalation["call_id"],
                escalation.get("escalation_reason"),
                escalation.get("severity"),
                escalation.get("assigned_to"),
                escalation.get("status"),
                escalation.get("notes"),
                escalation.get("created_at"),
                escalation.get("resolved_at"),
            ),
        )


def query_rows(conn: sqlite3.Connection, sql: str, params=()) -> list[sqlite3.Row]:
    return conn.execute(sql, params).fetchall()


def table_count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def build_report(conn: sqlite3.Connection, db_path: Path, records_path: Path) -> str:
    tables = [
        "leads",
        "sales_campaigns",
        "call_sessions",
        "qualification_answers",
        "turn_decisions",
        "call_outcomes",
        "appointments",
        "escalations",
    ]
    interested = query_rows(
        conn,
        """
        SELECT leads.lead_id, leads.role_title, call_outcomes.next_action
        FROM leads
        JOIN call_outcomes ON call_outcomes.lead_id = leads.lead_id
        WHERE call_outcomes.interest_state = 'interested'
        ORDER BY leads.lead_id
        """,
    )
    do_not_call = query_rows(
        conn,
        """
        SELECT lead_id, role_title, do_not_call_reason
        FROM leads
        WHERE do_not_call = 1
        ORDER BY lead_id
        """,
    )
    appointments = query_rows(
        conn,
        """
        SELECT appointment_id, lead_id, scheduled_time, appointment_status
        FROM appointments
        ORDER BY appointment_id
        """,
    )
    escalations = query_rows(
        conn,
        """
        SELECT escalation_id, lead_id, escalation_reason, status
        FROM escalations
        ORDER BY escalation_id
        """,
    )
    sample_turns = query_rows(
        conn,
        """
        SELECT turn_index, stage, interest_state, selected_strategy, next_action
        FROM turn_decisions
        WHERE call_id = 'call-prod-001-c01'
        ORDER BY turn_index
        """,
    )

    lines = [
        "# PROD-001 SQLite Import Report",
        "",
        f"- Database: `{db_path.as_posix()}`",
        f"- Source records: `{records_path.as_posix()}`",
        "- Data source: synthetic product simulation records",
        "",
        "## Table Counts",
        "",
    ]
    lines.extend(f"- `{table}`: {table_count(conn, table)}" for table in tables)

    campaigns = query_rows(
        conn,
        """
        SELECT campaign_id, product_name, product_category, customer_type
        FROM sales_campaigns
        ORDER BY campaign_id
        """,
    )
    lines.extend(["", "## Campaigns", ""])
    lines.extend(
        f"- `{row['campaign_id']}`: {row['product_name']} / `{row['product_category']}` / `{row['customer_type']}`"
        for row in campaigns
    )

    lines.extend(["", "## Interested Leads", ""])
    lines.extend(f"- `{row['lead_id']}` ({row['role_title']}): {row['next_action']}" for row in interested)

    lines.extend(["", "## Do-Not-Call Leads", ""])
    lines.extend(f"- `{row['lead_id']}` ({row['role_title']}): {row['do_not_call_reason']}" for row in do_not_call)

    lines.extend(["", "## Appointments", ""])
    lines.extend(
        f"- `{row['appointment_id']}` for `{row['lead_id']}` at `{row['scheduled_time']}`: `{row['appointment_status']}`"
        for row in appointments
    )

    lines.extend(["", "## Escalations", ""])
    lines.extend(
        f"- `{row['escalation_id']}` for `{row['lead_id']}`: {row['escalation_reason']} (`{row['status']}`)"
        for row in escalations
    )

    lines.extend(["", "## Sample Turn Decisions For `call-prod-001-c01`", ""])
    lines.extend(
        f"- Turn {row['turn_index']} `{row['stage']}`: `{row['interest_state']}` / `{row['selected_strategy']}` -> `{row['next_action']}`"
        for row in sample_turns
    )

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Import synthetic simulation records into a local SQLite database.")
    parser.add_argument("--records", required=True, help="Path to database-shaped JSON records.")
    parser.add_argument("--db", required=True, help="Path to the SQLite database to create or update.")
    parser.add_argument("--schema", default=str(DEFAULT_SCHEMA), help="Path to the SQLite schema SQL file.")
    parser.add_argument("--report-out", help="Optional path to write a markdown import/query report.")
    parser.add_argument("--reset", action="store_true", help="Clear existing rows in known tables before importing.")
    args = parser.parse_args()

    records_path = Path(args.records)
    db_path = Path(args.db)
    schema_path = Path(args.schema)
    records = load_json(records_path)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        execute_schema(conn, schema_path)
        if args.reset:
            clear_tables(conn)
        insert_records(conn, records)
        conn.commit()

        if args.report_out:
            report_path = Path(args.report_out)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(build_report(conn, db_path, records_path), encoding="utf-8")


if __name__ == "__main__":
    main()
