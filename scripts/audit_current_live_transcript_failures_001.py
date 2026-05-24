#!/usr/bin/env python3
"""Audit current live-demo transcript artifacts without publishing raw private text."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "CURRENT-LIVE-TRANSCRIPT-FAILURE-AUDIT-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PRIVATE_ROOT = ROOT / "data" / "private"
CURRENT_RUNTIME_MARKER = "UNIVERSAL-CONVERSATION-POLICY-RUNTIME-001"

KNOWN_CURRENT_SESSION_IDS = {
    "8318356e-9217-40a4-b230-ee94b54a3d4a",
    "2d476e4f-ff95-44e1-9c42-72476b41676e",
    "fce64600-5d0c-4f99-80dc-5d5e431f6791",
    "1c635f63-314a-48cf-9257-313da0935f5d",
}

CLASSIFICATIONS = (
    "current_live_runtime_defect",
    "current_live_asr_near_miss_repair_defect",
    "current_live_direct_question_defect",
    "current_live_stop_detection_defect",
    "current_live_repeated_response_defect",
    "current_live_offer_scope_model_defect",
    "current_live_campaign_positioning_defect",
    "current_live_campaign_selector_issue",
    "current_live_tts_audio_issue",
    "current_live_latency_or_turn_taking_issue",
    "not_reproduced",
    "stale_or_unknown_version_artifact",
    "needs_human_review",
)

DIRECT_PRODUCT_PATTERNS = (
    "what are you guys selling",
    "what are you selling",
    "what do you guys sell",
    "what do you sell",
    "what is this product",
    "what is routesignal",
    "what exactly do you do",
    "what are you calling about",
    "what is your product offer",
    "what is your offer",
)

PROCESS_QUESTION_PATTERNS = (
    "how are you going to check that",
    "how would you check that",
    "how do you review that",
    "what would they look at",
    "what will the specialist do",
)

CALLBACK_NEAR_MISS_PATTERNS = (
    "colbert",
    "call bags",
    "call backs",
    "callback issue",
    "call back timing",
    "cold backs",
)

STOP_PATTERNS = (
    "bro stop",
    "bruh stop",
    "bra stop",
    "stop",
    "stop talking",
    "please stop",
)

STOP_NEGATIVE_CONTROLS = ("bus stop", "stop gap")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(text: str) -> str:
    return " ".join(
        "".join(ch.lower() if ch.isalnum() else " " for ch in str(text or "")).split()
    )


def sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def source_hash(path: Path) -> str:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    return sha256_short(str(rel).replace("\\", "/"))


def current_git_head() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True)
            .strip()
        )
    except Exception:
        return ""


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def iter_private_records() -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    for folder in sorted(PRIVATE_ROOT.glob("live-demo-*")):
        if not folder.is_dir():
            continue
        for path in folder.rglob("LIVE-DEMO-001-turn-*.json"):
            data = read_json(path)
            if data is not None:
                records.append((path, data))
    return records


def current_marker(record: dict[str, Any]) -> str:
    metadata = record.get("runtime_metadata") if isinstance(record.get("runtime_metadata"), dict) else {}
    return str(record.get("universal_policy_runtime_marker") or metadata.get("universal_policy_runtime_marker") or "")


def git_head(record: dict[str, Any]) -> str:
    metadata = record.get("runtime_metadata") if isinstance(record.get("runtime_metadata"), dict) else {}
    return str(record.get("git_head_short") or metadata.get("git_head_short") or "")


def select_current_records(records: list[tuple[Path, dict[str, Any]]]) -> tuple[list[tuple[Path, dict[str, Any]]], str]:
    head = current_git_head()
    marked = [(path, record) for path, record in records if current_marker(record) == CURRENT_RUNTIME_MARKER]
    current_head = [(path, record) for path, record in marked if head and git_head(record) == head]
    known = [
        (path, record)
        for path, record in current_head
        if str(record.get("session_id") or "") in KNOWN_CURRENT_SESSION_IDS
    ]
    selected = known or current_head or marked
    selected = sorted(selected, key=lambda item: item[0].stat().st_mtime, reverse=True)
    if known:
        basis = "known_current_session_ids_on_current_git_head"
    elif current_head:
        basis = "current_runtime_marker_and_current_git_head"
    elif marked:
        basis = "nearest_current_runtime_marker_available"
    else:
        basis = "no_current_runtime_marker_available"
    return selected, basis


def final_response(record: dict[str, Any]) -> str:
    summary = record.get("summary") if isinstance(record.get("summary"), dict) else {}
    return str(summary.get("final_response") or record.get("final_response") or "")


def call_control(record: dict[str, Any]) -> str:
    summary = record.get("summary") if isinstance(record.get("summary"), dict) else {}
    return str(summary.get("call_control") or record.get("call_control") or "")


def side_effect_flags(record: dict[str, Any]) -> dict[str, bool]:
    summary = record.get("summary") if isinstance(record.get("summary"), dict) else {}
    return {
        "provider_calls_made": bool(record.get("provider_calls_made") or summary.get("tts_provider_calls_made")),
        "local_llm_calls_made": bool(record.get("local_llm_calls_made")),
        "sends_email": bool(record.get("sends_email")),
        "creates_calendar_event": bool(record.get("creates_calendar_event")),
        "writes_crm": bool(record.get("writes_crm")),
        "opens_prod_102": bool(record.get("opens_prod_102")),
        "customer_audio_uploaded_to_python_server": bool(record.get("customer_audio_uploaded_to_python_server")),
        "customer_audio_uploaded_to_tts_provider": bool(record.get("customer_audio_uploaded_to_tts_provider")),
    }


def has_any(normalized: str, patterns: tuple[str, ...]) -> bool:
    return any(pattern in normalized for pattern in patterns)


def synthetic_hint(normalized: str) -> str:
    if has_any(normalized, DIRECT_PRODUCT_PATTERNS):
        return "synthetic_direct_product_question"
    if has_any(normalized, PROCESS_QUESTION_PATTERNS):
        return "synthetic_review_process_question"
    if has_any(normalized, CALLBACK_NEAR_MISS_PATTERNS):
        return "synthetic_callback_asr_near_miss"
    if normalized in STOP_PATTERNS or has_any(normalized, ("stop talking", "please stop")):
        return "synthetic_stop_request_variant"
    if "already told you" in normalized or "that wasn t my question" in normalized:
        return "synthetic_repeated_or_unanswered_challenge"
    if "current provider" in normalized or "what is your product offer" in normalized:
        return "synthetic_product_offer_difference_question"
    return "synthetic_live_turn_no_public_text"


def route_signal_answer_good(response_normalized: str) -> bool:
    product_terms = (
        "routesignal" in response_normalized
        and ("crm" in response_normalized or "workflow" in response_normalized)
        and ("inbound demo" in response_normalized or "follow up" in response_normalized or "handoff" in response_normalized)
    )
    return product_terms


def product_answer_good(record: dict[str, Any], response_normalized: str) -> bool:
    campaign_id = str(record.get("campaign_id") or "")
    if "routesignal" in campaign_id or campaign_id == "campaign-prod-005-b2b-software":
        return route_signal_answer_good(response_normalized)
    return (
        ("offer" in response_normalized or "fit check" in response_normalized or "review call" in response_normalized)
        and ("next step" in response_normalized or "specialist" in response_normalized or "human" in response_normalized)
    )


def prior_context(session_records: list[dict[str, Any]]) -> str:
    return " ".join(normalize(str(item.get("transcript") or "")) for item in session_records[-8:])


def classify_current_record(
    *,
    path: Path,
    record: dict[str, Any],
    session_records: list[dict[str, Any]],
    current_head: str,
) -> dict[str, Any]:
    transcript = str(record.get("transcript") or "")
    normalized = normalize(transcript)
    response = final_response(record)
    response_normalized = normalize(response)
    classifications: list[str] = []
    reasons: list[str] = []

    is_current = current_marker(record) == CURRENT_RUNTIME_MARKER and (not current_head or git_head(record) == current_head)
    if not is_current:
        classifications.append("stale_or_unknown_version_artifact")
        reasons.append("record lacks current runtime marker or current git head")
    elif not normalized:
        classifications.append("needs_human_review")
        reasons.append("record has no transcript text to classify")
    else:
        if has_any(normalized, DIRECT_PRODUCT_PATTERNS):
            if not product_answer_good(record, response_normalized):
                classifications.extend(["current_live_runtime_defect", "current_live_direct_question_defect"])
                reasons.append("direct product or offer question did not receive a product/offer answer first")
            if "review" in response_normalized and "product" not in response_normalized and not route_signal_answer_good(response_normalized):
                classifications.extend(["current_live_offer_scope_model_defect", "current_live_campaign_positioning_defect"])
                reasons.append("response over-centered review/appointment framing instead of offer value")

        if has_any(normalized, PROCESS_QUESTION_PATTERNS):
            process_good = (
                ("review" in response_normalized or "check" in response_normalized or "look at" in response_normalized)
                and not response_normalized.startswith("i m good thanks")
                and not response_normalized.startswith("im good thanks")
            )
            if not process_good:
                classifications.extend(["current_live_runtime_defect", "current_live_direct_question_defect"])
                reasons.append("review-process question was not answered directly")

        if has_any(normalized, CALLBACK_NEAR_MISS_PATTERNS):
            ambiguous = has_any(normalized, ("colbert", "call bags", "cold backs"))
            near_miss_good = (
                "did you mean callbacks" in response_normalized
                or "misheard" in response_normalized
                or ("callbacks" in response_normalized and "outside" not in response_normalized)
            )
            if ambiguous and not near_miss_good:
                classifications.extend(["current_live_runtime_defect", "current_live_asr_near_miss_repair_defect"])
                reasons.append("callback-like ASR near miss was not preserved or clarified")

        if (normalized in STOP_PATTERNS or has_any(normalized, ("stop talking", "please stop"))) and not has_any(normalized, STOP_NEGATIVE_CONTROLS):
            if call_control(record) != "end-call":
                classifications.extend(["current_live_runtime_defect", "current_live_stop_detection_defect"])
                reasons.append("stop-like ASR variant did not end the call")

        prior = prior_context(session_records)
        fully_captured = "callback" in prior and ("delay" in prior or "delays" in prior) and ("tomorrow" in prior or "3" in prior)
        if ("already told you" in normalized or "that wasn t my question" in normalized) and fully_captured:
            if "causing delays or extra work" in response_normalized or "is it causing" in response_normalized:
                classifications.extend(["current_live_runtime_defect", "current_live_repeated_response_defect"])
                reasons.append("agent repeated impact question after issue, impact, and callback time were already captured")

        selector = record.get("selected_campaign_config") if isinstance(record.get("selected_campaign_config"), dict) else {}
        selector_id = str(selector.get("campaign_id") or "")
        campaign_id = str(record.get("campaign_id") or "")
        if selector_id and campaign_id and selector_id != campaign_id and campaign_id != "live-demo-001-routesignal":
            classifications.extend(["current_live_runtime_defect", "current_live_campaign_selector_issue"])
            reasons.append("selected campaign metadata does not match record campaign id")

        if bool(record.get("live_tts_used") or record.get("tts_provider_calls_made")) and not bool(record.get("audio_file_created") or record.get("audio_url")):
            classifications.append("current_live_tts_audio_issue")
            reasons.append("live TTS/provider path did not produce an audio artifact")

        latency = record.get("latency") if isinstance(record.get("latency"), dict) else {}
        total_ms = latency.get("total_ms") or latency.get("total_provider_latency_ms")
        try:
            if total_ms is not None and float(total_ms) > 3500:
                classifications.append("current_live_latency_or_turn_taking_issue")
                reasons.append("turn latency exceeded live-call review threshold")
        except (TypeError, ValueError):
            pass

    if not classifications:
        classifications.append("not_reproduced")
        reasons.append("no deterministic current-live defect rule matched this record")

    return {
        "source_file_name": path.name,
        "source_path_hash": source_hash(path),
        "source_modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        "session_id": str(record.get("session_id") or ""),
        "session_turn_index": record.get("session_turn_index"),
        "campaign_id": str(record.get("campaign_id") or ""),
        "git_head_short": git_head(record),
        "runtime_marker": current_marker(record),
        "transcript_sha256_16": sha256_short(transcript),
        "response_sha256_16": sha256_short(response),
        "synthetic_replay_hint": synthetic_hint(normalized),
        "classifications": list(dict.fromkeys(classifications)),
        "classification_reasons": reasons,
        "call_control": call_control(record),
        "side_effect_flags": side_effect_flags(record),
    }


def audit() -> dict[str, Any]:
    all_records = iter_private_records()
    current_records, selection_basis = select_current_records(all_records)
    head = current_git_head()
    by_session: dict[str, list[tuple[Path, dict[str, Any]]]] = defaultdict(list)
    for path, record in current_records:
        by_session[str(record.get("session_id") or "")].append((path, record))

    audited_records: list[dict[str, Any]] = []
    classification_counts: Counter[str] = Counter()
    session_hits = {session_id: 0 for session_id in sorted(KNOWN_CURRENT_SESSION_IDS)}
    side_effects = Counter()

    for session_id, items in sorted(by_session.items()):
        ordered = sorted(items, key=lambda item: item[0].stat().st_mtime)
        session_history: list[dict[str, Any]] = []
        for path, record in ordered:
            if session_id in session_hits:
                session_hits[session_id] += 1
            item = classify_current_record(
                path=path,
                record=record,
                session_records=session_history,
                current_head=head,
            )
            audited_records.append(item)
            classification_counts.update(item["classifications"])
            for key, value in item["side_effect_flags"].items():
                if value:
                    side_effects[key] += 1
            session_history.append(record)

    audited_records.sort(key=lambda item: item["source_modified_utc"], reverse=True)
    current_defect_records = [
        record for record in audited_records if "current_live_runtime_defect" in record["classifications"]
    ]
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": "pass",
        "private_records_total": len(all_records),
        "selected_record_count": len(current_records),
        "selection_basis": selection_basis,
        "current_git_head_short": head,
        "known_current_session_hits": session_hits,
        "classification_counts": {label: classification_counts.get(label, 0) for label in CLASSIFICATIONS},
        "current_live_runtime_defect_count": len(current_defect_records),
        "current_live_direct_question_defect_count": classification_counts.get("current_live_direct_question_defect", 0),
        "current_live_asr_near_miss_repair_defect_count": classification_counts.get("current_live_asr_near_miss_repair_defect", 0),
        "current_live_offer_scope_model_defect_count": classification_counts.get("current_live_offer_scope_model_defect", 0),
        "current_live_stop_detection_defect_count": classification_counts.get("current_live_stop_detection_defect", 0),
        "campaign_selector_issue_count": classification_counts.get("current_live_campaign_selector_issue", 0),
        "tts_audio_issue_count": classification_counts.get("current_live_tts_audio_issue", 0),
        "latency_issue_count": classification_counts.get("current_live_latency_or_turn_taking_issue", 0),
        "side_effect_issue_counts": dict(sorted(side_effects.items())),
        "public_evidence_redaction": {
            "raw_private_transcripts_copied": False,
            "raw_private_responses_copied": False,
            "included_fields": [
                "session_id",
                "campaign_id",
                "runtime marker",
                "git head",
                "transcript and response hashes",
                "synthetic replay hints",
                "classification labels",
            ],
        },
        "records": audited_records,
    }
    return result


def write_outputs(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# {CHECKPOINT_ID}",
        "",
        "## Summary",
        f"- Status: `{result['status']}`",
        f"- Private records total: `{result['private_records_total']}`",
        f"- Selected current records: `{result['selected_record_count']}`",
        f"- Selection basis: `{result['selection_basis']}`",
        f"- Current git head: `{result['current_git_head_short']}`",
        f"- Current live runtime defect records: `{result['current_live_runtime_defect_count']}`",
        f"- Raw private transcripts copied: `false`",
        "",
        "## Requested Counts",
        f"- current_live_runtime_defect count: `{result['current_live_runtime_defect_count']}`",
        f"- current_live_direct_question_defect count: `{result['current_live_direct_question_defect_count']}`",
        f"- current_live_asr_near_miss_repair_defect count: `{result['current_live_asr_near_miss_repair_defect_count']}`",
        f"- current_live_offer_scope_model_defect count: `{result['current_live_offer_scope_model_defect_count']}`",
        f"- current_live_stop_detection_defect count: `{result['current_live_stop_detection_defect_count']}`",
        f"- campaign selector issue count: `{result['campaign_selector_issue_count']}`",
        f"- TTS/audio issue count: `{result['tts_audio_issue_count']}`",
        f"- latency issue count: `{result['latency_issue_count']}`",
        "",
        "## Classification Counts",
        *(
            f"- `{label}`: `{count}`"
            for label, count in result["classification_counts"].items()
        ),
        "",
        "## Known Session Coverage",
        *(
            f"- `{session_id}`: `{count}` records"
            for session_id, count in result["known_current_session_hits"].items()
        ),
        "",
        "## Sanitized Records",
    ]
    for record in result["records"]:
        lines.extend(
            [
                f"### {record['source_file_name']}",
                f"- Source path hash: `{record['source_path_hash']}`",
                f"- Session: `{record['session_id']}`",
                f"- Campaign: `{record['campaign_id']}`",
                f"- Transcript hash: `{record['transcript_sha256_16']}`",
                f"- Synthetic replay hint: `{record['synthetic_replay_hint']}`",
                f"- Classifications: `{', '.join(record['classifications'])}`",
                f"- Call control: `{record['call_control']}`",
                "",
            ]
        )
    (OUT_DIR / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result = audit()
    write_outputs(result)
    print(
        json.dumps(
            {
                "checkpoint_id": result["checkpoint_id"],
                "status": result["status"],
                "selected_record_count": result["selected_record_count"],
                "current_live_runtime_defect_count": result["current_live_runtime_defect_count"],
                "classification_counts": result["classification_counts"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
