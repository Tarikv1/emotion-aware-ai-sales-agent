#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_042_callcenteren_turn_pattern_playbook import (
    CHECKPOINT_ID,
    OUTPUT_DIR,
    PROD_013_PATTERN_BANK,
    PROD_014_SCENARIO_BANK,
    RAW_SOURCE_DIR,
    ROOT,
    build_payload,
    build_result,
    render_pattern_review_html,
    render_report,
    summarize_counts,
    write_json,
    write_text,
)


RESTRICTED_PARTS = {"private", "private-restricted"}


def resolve_path(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"PROD-042 path must stay inside project root: {path_text}") from exc
    if any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-042 path is restricted: {path_text}")
    return resolved


def default_output_paths(out_dir: Path) -> dict[str, Path]:
    return {
        "result": out_dir / "result.json",
        "report": out_dir / "report.md",
        "source_pattern_index": out_dir / "source_pattern_index.json",
        "raw_parse_summary": out_dir / "raw_parse_summary.json",
        "customer_move_patterns": out_dir / "customer_move_patterns.json",
        "agent_response_tactics": out_dir / "agent_response_tactics.json",
        "agent_response_quality_patterns": out_dir / "agent_response_quality_patterns.json",
        "customer_reaction_patterns": out_dir / "customer_reaction_patterns.json",
        "customer_state_transition_patterns": out_dir / "customer_state_transition_patterns.json",
        "next_best_action_patterns": out_dir / "next_best_action_patterns.json",
        "failure_patterns": out_dir / "failure_patterns.json",
        "recovery_patterns": out_dir / "recovery_patterns.json",
        "sales_playbook_rules": out_dir / "sales_playbook_rules.json",
        "evaluation_rules": out_dir / "evaluation_rules.json",
        "pattern_review_data": out_dir / "pattern_review_data.json",
        "pattern_review_html": out_dir / "pattern_review.html",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run PROD-042 CallCenterEN turn-level sales pattern playbook extraction.")
    parser.add_argument("--raw-source-dir", default=str(RAW_SOURCE_DIR), help="Raw CallCenterEN zip source directory.")
    parser.add_argument("--pattern-bank", default=str(PROD_013_PATTERN_BANK), help="PROD-013 pattern-bank path for cross-check.")
    parser.add_argument("--scenario-bank", default=str(PROD_014_SCENARIO_BANK), help="PROD-014 scenario-bank path for cross-check.")
    parser.add_argument("--out-dir", default=str(OUTPUT_DIR), help="Output directory for generated PROD-042 artifacts.")
    args = parser.parse_args()

    raw_source_dir = resolve_path(args.raw_source_dir)
    pattern_bank_path = resolve_path(args.pattern_bank)
    scenario_bank_path = resolve_path(args.scenario_bank)
    out_dir = resolve_path(args.out_dir)
    paths = default_output_paths(out_dir)

    artifacts, guard_substitutions = build_payload(
        raw_source_dir=raw_source_dir,
        pattern_bank_path=pattern_bank_path,
        scenario_bank_path=scenario_bank_path,
    )

    for key in (
        "source_pattern_index",
        "raw_parse_summary",
        "customer_move_patterns",
        "agent_response_tactics",
        "agent_response_quality_patterns",
        "customer_reaction_patterns",
        "customer_state_transition_patterns",
        "next_best_action_patterns",
        "failure_patterns",
        "recovery_patterns",
        "sales_playbook_rules",
        "evaluation_rules",
        "pattern_review_data",
    ):
        write_json(paths[key], artifacts[key])

    write_text(paths["pattern_review_html"], render_pattern_review_html(artifacts["pattern_review_data"]))

    summary = summarize_counts(
        parse_summary=artifacts["raw_parse_summary"],
        source_index=artifacts["source_pattern_index"],
        customer_moves=artifacts["customer_move_patterns"],
        tactics=artifacts["agent_response_tactics"],
        quality_patterns=artifacts["agent_response_quality_patterns"],
        reactions=artifacts["customer_reaction_patterns"],
        state_transitions=artifacts["customer_state_transition_patterns"],
        next_actions=artifacts["next_best_action_patterns"],
        failures=artifacts["failure_patterns"],
        recoveries=artifacts["recovery_patterns"],
        playbook=artifacts["sales_playbook_rules"],
        evaluation=artifacts["evaluation_rules"],
    )

    result = build_result(
        summary=summary,
        output_paths={
            "result_json": paths["result"],
            "report_md": paths["report"],
            "source_pattern_index_json": paths["source_pattern_index"],
            "raw_parse_summary_json": paths["raw_parse_summary"],
            "customer_move_patterns_json": paths["customer_move_patterns"],
            "agent_response_tactics_json": paths["agent_response_tactics"],
            "agent_response_quality_patterns_json": paths["agent_response_quality_patterns"],
            "customer_reaction_patterns_json": paths["customer_reaction_patterns"],
            "customer_state_transition_patterns_json": paths["customer_state_transition_patterns"],
            "next_best_action_patterns_json": paths["next_best_action_patterns"],
            "failure_patterns_json": paths["failure_patterns"],
            "recovery_patterns_json": paths["recovery_patterns"],
            "sales_playbook_rules_json": paths["sales_playbook_rules"],
            "evaluation_rules_json": paths["evaluation_rules"],
            "pattern_review_data_json": paths["pattern_review_data"],
            "pattern_review_html": paths["pattern_review_html"],
        },
    )
    write_json(paths["result"], result)

    write_text(
        paths["report"],
        render_report(
            result=result,
            parse_summary=artifacts["raw_parse_summary"],
            source_index=artifacts["source_pattern_index"],
            customer_moves=artifacts["customer_move_patterns"],
            tactics=artifacts["agent_response_tactics"],
            quality_patterns=artifacts["agent_response_quality_patterns"],
            reactions=artifacts["customer_reaction_patterns"],
            state_transitions=artifacts["customer_state_transition_patterns"],
            next_actions=artifacts["next_best_action_patterns"],
            failures=artifacts["failure_patterns"],
            recoveries=artifacts["recovery_patterns"],
            playbook=artifacts["sales_playbook_rules"],
            evaluation=artifacts["evaluation_rules"],
            guard_substitutions=guard_substitutions,
        ),
    )

    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

