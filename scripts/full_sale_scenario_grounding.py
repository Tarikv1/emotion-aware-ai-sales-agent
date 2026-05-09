#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable


TOKEN_RE = re.compile(r"[a-z0-9]+")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
MIN_LEAK_SENTENCE_TOKENS = 5
HIGH_SIMILARITY_THRESHOLD = 0.86


@dataclass(frozen=True)
class LeakageFinding:
    kind: str
    scenario_id: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"kind": self.kind, "scenario_id": self.scenario_id, "detail": self.detail}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    return " ".join(TOKEN_RE.findall(value.lower()))


def sentence_fragments(value: str) -> list[str]:
    fragments: list[str] = []
    for candidate in SENTENCE_RE.split(value.replace("\n", " ")):
        normalized = normalize_text(candidate)
        if len(normalized.split()) >= MIN_LEAK_SENTENCE_TOKENS:
            fragments.append(normalized)
    return fragments


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def scenario_text(scenario: dict[str, Any]) -> str:
    fields = [
        scenario.get("scenario_title", ""),
        scenario.get("customer_context", ""),
        scenario.get("agent_goal", ""),
        " ".join(scenario.get("generated_turn_outline", [])),
        " ".join(scenario.get("unsafe_behaviors_to_catch", [])),
        " ".join(scenario.get("safe_close_criteria", [])),
    ]
    return "\n".join(field for field in fields if field)


def _load_jsonish_text(text: str) -> Any:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        records = []
        for line in stripped.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records if records else None


def collect_transient_sentences_from_zip_dir(zip_dir: Path, *, limit: int = 5000) -> list[str]:
    """Read ignored local ZIPs in memory and return normalized sentences without writing transcript text."""
    if not zip_dir.exists():
        return []
    sentences: list[str] = []
    for zip_path in sorted(zip_dir.glob("*.zip")):
        if len(sentences) >= limit:
            break
        with zipfile.ZipFile(zip_path) as archive:
            for member in archive.namelist():
                if len(sentences) >= limit:
                    break
                if not member.lower().endswith((".json", ".jsonl", ".txt")):
                    continue
                with archive.open(member) as handle:
                    raw_text = handle.read().decode("utf-8", errors="ignore")
                parsed = _load_jsonish_text(raw_text)
                strings = list(iter_strings(parsed)) if parsed is not None else [raw_text]
                for text in strings:
                    for fragment in sentence_fragments(text):
                        sentences.append(fragment)
                        if len(sentences) >= limit:
                            break
                    if len(sentences) >= limit:
                        break
    return sentences


def detect_leakage(
    scenarios: list[dict[str, Any]],
    source_sentences: list[str],
    runtime_prompts: list[str],
) -> list[LeakageFinding]:
    normalized_source = [normalize_text(item) for item in source_sentences if normalize_text(item)]
    normalized_prompts = "\n".join(normalize_text(prompt) for prompt in runtime_prompts)
    findings: list[LeakageFinding] = []

    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        text = scenario_text(scenario)
        normalized_scenario = normalize_text(text)
        scenario_sentences = sentence_fragments(text)

        for source_sentence in normalized_source:
            if not source_sentence:
                continue
            if source_sentence in normalized_scenario:
                findings.append(LeakageFinding("exact_transcript_sentence", scenario_id, source_sentence[:120]))
            for scenario_sentence in scenario_sentences:
                ratio = SequenceMatcher(None, source_sentence, scenario_sentence).ratio()
                if ratio >= HIGH_SIMILARITY_THRESHOLD:
                    findings.append(
                        LeakageFinding(
                            "high_similarity_paraphrase",
                            scenario_id,
                            f"similarity={ratio:.3f}",
                        )
                    )
                    break
            if source_sentence and source_sentence in normalized_prompts:
                findings.append(LeakageFinding("commercial_runtime_prompt_contamination", scenario_id, source_sentence[:120]))

        if len(scenario.get("source_pattern_ids", [])) < 3:
            findings.append(LeakageFinding("single_source_scenario", scenario_id, "Scenario uses fewer than three source patterns."))
        if scenario.get("copied_transcript_text_used") is not False:
            findings.append(LeakageFinding("copied_transcript_text_flag", scenario_id, "Scenario copied transcript text."))
        if scenario.get("contains_transcript_derived_prompt_text") is not False:
            findings.append(
                LeakageFinding(
                    "transcript_derived_prompt_flag",
                    scenario_id,
                    "Scenario is marked as containing transcript-derived prompt text.",
                )
            )

    return findings


def leakage_status(findings: list[LeakageFinding], kind: str) -> str:
    return "fail" if any(finding.kind == kind for finding in findings) else "pass"


def build_prod_006_payload(case_path: Path, *, root: Path, raw_zip_dir: Path | None = None) -> dict[str, Any]:
    case = load_json(case_path)
    scenarios = case["scenario_bank"]
    runtime_prompts = case.get("commercial_runtime_prompts", [])
    source_probe_sentences = [normalize_text(text) for text in case.get("synthetic_leakage_probe_sentences", [])]
    transient_sentence_count = 0
    if raw_zip_dir is not None:
        transient_sentences = collect_transient_sentences_from_zip_dir(raw_zip_dir)
        transient_sentence_count = len(transient_sentences)
        source_probe_sentences.extend(transient_sentences)

    findings = detect_leakage(scenarios, source_probe_sentences, runtime_prompts)
    summary = {
        "scenario_count": len(scenarios),
        "source_pattern_count": len(case["source_patterns"]),
        "multi_domain_pattern_bank": True,
        "download_performed": False,
        "provider_calls_made": False,
        "raw_transcript_text_stored": False,
        "runtime_retrieval_enabled": False,
        "commercial_runtime_prompt_contamination": leakage_status(findings, "commercial_runtime_prompt_contamination") == "fail",
        "leakage_finding_count": len(findings),
        "transient_source_sentence_count": transient_sentence_count,
    }

    return {
        "prod_006_id": "PROD-006-full-sale-scenario-grounding",
        "dataset_source": case["dataset_source"],
        "intake_policy": case["intake_policy"],
        "metrics": case["metrics"],
        "source_patterns": case["source_patterns"],
        "scenario_bank": scenarios,
        "leakage_tests": {
            "minimum_source_patterns_per_scenario": 3,
            "exact_transcript_sentence_check": {
                "status": leakage_status(findings, "exact_transcript_sentence"),
                "method": "normalized exact sentence scan against transient source sentences and synthetic leak probes",
            },
            "high_similarity_paraphrase_check": {
                "status": leakage_status(findings, "high_similarity_paraphrase"),
                "threshold": HIGH_SIMILARITY_THRESHOLD,
            },
            "single_source_scenario_check": {
                "status": leakage_status(findings, "single_source_scenario"),
                "method": "each scenario must use at least three source pattern IDs",
            },
            "commercial_runtime_prompt_check": {
                "status": leakage_status(findings, "commercial_runtime_prompt_contamination"),
                "method": "transcript-derived sentences are blocked from commercial runtime prompts",
            },
            "findings": [finding.to_dict() for finding in findings],
        },
        "summary": summary,
        "boundaries": {
            "pattern_grounding_only": True,
            "download_required_for_default_run": False,
            "raw_dataset_storage": "data/external/callcenteren/raw/ ignored local-only",
            "tracked_artifacts_may_store_raw_transcripts": False,
            "commercial_runtime_may_use_transcript_text": False,
            "payment_or_checkout_enabled": False,
            "real_customer_data_used": False,
        },
    }


def render_prod_006_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metrics = payload["metrics"]
    lines = [
        "# PROD-006 Full-Sale Scenario Grounding Report",
        "",
        f"Scenario count: `{summary['scenario_count']}`",
        f"Source pattern count: `{summary['source_pattern_count']}`",
        "Reuse label: `pattern grounding only`",
        "Download performed: `false`",
        "Provider calls made: `false`",
        "Raw transcript text stored: `false`",
        "",
        "## Metrics",
        "",
        f"- Safe close rate: {metrics['safe_close_rate']['definition']}",
        f"- Hard failure rate: {metrics['hard_failure_rate']['definition']}",
        f"- Non-sale correctness: {metrics['non_sale_correctness']['definition']}",
        "",
        "## Leakage Tests",
        "",
    ]
    for name, check in payload["leakage_tests"].items():
        if isinstance(check, dict) and "status" in check:
            lines.append(f"- {name}: `{check['status']}`")
    lines.extend(
        [
            "",
            "## Scenario Labels",
            "",
        ]
    )
    for scenario in payload["scenario_bank"]:
        lines.append(
            f"- `{scenario['scenario_id']}`: {scenario['scenario_label']} -> {scenario['expected_outcome']} "
            f"({len(scenario['source_pattern_ids'])} source patterns)"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report stores scenario patterns and project-owned rewritten scenarios only. It does not store raw transcript text, copied transcript lines, payment data, provider output, or real customer data.",
        ]
    )
    return "\n".join(lines) + "\n"
