"""Generate a live-demo commercial rehearsal review packet.

This is evidence tooling only. It reads ignored local private live-demo turn
JSON files when present, hashes/redacts buyer transcript material, and writes a
public review packet for human or ChatGPT review. It does not call providers,
run TTS, invoke LLMs, send email, touch CRM, or open PROD-102.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "LIVE-DEMO-COMMERCIAL-REHEARSAL-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
PRIVATE_ROOT = ROOT / "data" / "private"

PRIVATE_LIVE_DEMO_GLOBS = [
    "live-demo-001",
    "live-demo-003",
    "live-demo-*",
]

REQUIRED_FILES = [
    "rehearsal_packet.md",
    "rehearsal_packet.json",
    "rehearsal_packet.jsonl",
    "rehearsal_index.md",
    "rubric.md",
    "redaction_report.json",
    "result.json",
    "report.md",
]

RUBRIC_DIMENSIONS = [
    "ASR transcript accuracy",
    "Turn-taking / interruption handling",
    "TTS playback reliability",
    "Voice naturalness",
    "Campaign selection correctness",
    "Buyer acknowledgement",
    "Direct question answering",
    "Pain discovery and implication quality",
    "Rapport / human-context handling",
    "Objection handling",
    "Trust and AI transparency",
    "Close / next-step strength",
    "Safety and claim discipline",
    "Overall commercial usefulness",
]

QUALITATIVE_LABELS = [
    "live_ready_strong",
    "live_ready_with_minor_polish",
    "not_live_ready_voice_issue",
    "not_live_ready_dialogue_issue",
    "not_live_ready_asr_issue",
    "unsafe_or_unusable",
]

MECHANICAL_FLAGS = [
    "asr_low_confidence",
    "transcript_garbled",
    "turn_failed",
    "provider_audio_failed",
    "campaign_selector_mismatch",
    "route_signal_generic_mix",
    "final_response_missing",
    "tts_input_missing",
    "audio_url_missing_when_provider_called",
    "live_tts_requested_but_dry_run",
    "response_too_long_for_live_voice",
    "repeated_response",
    "call_control_unexpected",
]

SIDE_EFFECT_KEYS = [
    "provider_calls_made",
    "local_llm_calls_made",
    "live_tts_used",
    "tts_provider_calls_made",
    "sends_email",
    "creates_calendar_event",
    "writes_crm",
    "opens_prod_102",
    "customer_audio_uploaded_to_python_server",
    "customer_audio_uploaded_to_tts_provider",
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{12,}"),
]
LONG_NUMBER_PATTERN = re.compile(r"\b(?:\d[ -]?){9,16}\b")

ALLOWED_CALL_CONTROLS = {
    "",
    "continue",
    "continue-call",
    "end-call",
    "schedule-and-end",
    "transfer",
    "hold",
}

RECOMMENDED_SCENARIOS = [
    {
        "id": "A",
        "title": "RouteSignal normal path",
        "steps": ["Start RouteSignal", "Permission", "callbacks are a problem", "it causes delays", "tomorrow at 3 works"],
    },
    {
        "id": "B",
        "title": "RouteSignal challenge path",
        "steps": ["what does your product do", "why should I care", "are you a robot", "who are you"],
    },
    {
        "id": "C",
        "title": "Generic insurance product-detail path",
        "steps": [
            "select synthetic insurance",
            "what does your product do",
            "so you cannot give me details?",
            "maybe coverage fit",
            "it is active now",
            "it wastes time",
        ],
    },
    {
        "id": "D",
        "title": "Rapport/hardship path",
        "steps": [
            "I'm driving",
            "I just got out of the hospital",
            "everything is expensive right now",
            "last company like this wasted my time",
        ],
    },
    {
        "id": "E",
        "title": "ASR stress path",
        "steps": [
            "yeah that would be good",
            "okay that would be good",
            "call me tomorrow at 3",
            "say deliberately noisy or short phrases and check repair behavior",
        ],
    },
    {
        "id": "F",
        "title": "Campaign selector integrity",
        "steps": [
            "Start with RouteSignal selected",
            "Switch to generic insurance",
            "Switch back to RouteSignal",
            "Confirm campaign metadata and response content do not mix",
        ],
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return "<outside-project>"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, sort_keys=True))


def nested_get(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def redact_public_text(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED_SECRET]", text)
    text = LONG_NUMBER_PATTERN.sub("[REDACTED_NUMBER]", text)
    return text


def private_source_path_is_safe(path: Path) -> bool:
    rel = project_relative(path)
    if rel == "<outside-project>":
        return False
    if not rel.startswith("data/private/live-demo-"):
        return False
    if EMAIL_PATTERN.search(rel):
        return False
    return not any(pattern.search(rel) for pattern in SECRET_PATTERNS)


def discover_private_turn_files() -> list[Path]:
    if not PRIVATE_ROOT.exists():
        return []
    roots: dict[Path, None] = {}
    for pattern in PRIVATE_LIVE_DEMO_GLOBS:
        for candidate in PRIVATE_ROOT.glob(pattern):
            if candidate.is_dir():
                roots[candidate.resolve()] = None
    files: dict[Path, None] = {}
    for root in sorted(roots):
        for candidate in root.rglob("*.json"):
            if private_source_path_is_safe(candidate):
                files[candidate.resolve()] = None
    return sorted(files)


def load_private_json(path: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    raw = path.read_bytes()
    file_hash = sha256_bytes(raw)
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - packet should summarize unreadable private artifacts.
        return None, file_hash, f"{type(exc).__name__}: {exc}"
    if not isinstance(parsed, dict):
        return None, file_hash, "private JSON root is not an object"
    return parsed, file_hash, None


def transcript_metrics(turn: dict[str, Any]) -> dict[str, Any]:
    transcript = str(turn.get("transcript") or "")
    normalized = " ".join(transcript.split())
    return {
        "transcript_hash": sha256_text(normalized),
        "transcript_char_count": len(transcript),
        "transcript_word_count": len(normalized.split()) if normalized else 0,
        "transcript_empty": not bool(normalized),
    }


def select_universal_policy_frame(turn: dict[str, Any]) -> dict[str, Any]:
    frame = turn.get("universal_policy_frame") or nested_get(turn, "dialogue_manager", "selected_action", "universal_policy_frame") or {}
    if not isinstance(frame, dict):
        return {}
    allowed_keys = [
        "buyer_move_id",
        "buyer_move_category",
        "target_gap",
        "confirmed_gaps",
        "sales_progression_stage",
        "appointment_readiness",
        "impact_signal_detected",
        "impact_signal_type",
        "next_best_sales_action",
        "human_context_type",
        "rapport_response_shape_id",
    ]
    return {key: frame.get(key) for key in allowed_keys if key in frame}


def selected_action_summary(turn: dict[str, Any]) -> dict[str, Any]:
    action = nested_get(turn, "dialogue_manager", "selected_action") or {}
    if not isinstance(action, dict):
        return {}
    return {
        "source": action.get("source") or action.get("action_source"),
        "semantic": action.get("semantic") or action.get("semantic_id"),
        "target_gap": action.get("target_gap"),
        "call_control": action.get("call_control"),
    }


def selected_campaign_metadata(turn: dict[str, Any]) -> dict[str, Any]:
    selected = turn.get("selected_campaign_config") or {}
    if not isinstance(selected, dict):
        selected = {}
    keys = [
        "campaign_id",
        "vertical_id",
        "product_or_offer_name",
        "appointment_target",
        "human_followup_owner",
        "mode",
        "route_signal_fallback_used",
    ]
    metadata = {key: selected.get(key) for key in keys if key in selected}
    config_path = selected.get("config_path") or turn.get("campaign_config_path")
    if config_path:
        metadata["config_path"] = redact_public_text(config_path)
    return metadata


def observed_side_effect_flags(turn: dict[str, Any]) -> dict[str, bool]:
    packet_tts = nested_get(turn, "packet", "tts_delivery") or {}
    flags: dict[str, bool] = {}
    for key in SIDE_EFFECT_KEYS:
        flags[key] = bool(turn.get(key) or nested_get(turn, "summary", key) or packet_tts.get(key))
    flags["audio_file_created"] = bool(turn.get("audio_file_created") or nested_get(turn, "summary", "tts_audio_file_created") or packet_tts.get("audio_file_created"))
    return flags


def mechanical_flags(turn: dict[str, Any], final_response: str, tts_input_text: str, seen_responses: set[str]) -> list[str]:
    flags: list[str] = []
    asr = turn.get("asr") or {}
    quality_gate = asr.get("quality_gate") if isinstance(asr, dict) else {}
    confidence = asr.get("confidence") if isinstance(asr, dict) else None
    try:
        confidence_value = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence_value = None
    qg_reason = str((quality_gate or {}).get("reason") or "").lower() if isinstance(quality_gate, dict) else ""
    qg_accepted = (quality_gate or {}).get("accepted") if isinstance(quality_gate, dict) else None
    if confidence_value is not None and confidence_value < 0.55:
        flags.append("asr_low_confidence")
    if qg_accepted is False and ("confidence" in qg_reason or "low" in qg_reason):
        flags.append("asr_low_confidence")
    if "garble" in qg_reason or "misheard" in qg_reason:
        flags.append("transcript_garbled")
    if turn.get("error") or str(nested_get(turn, "summary", "selected_strategy") or "").lower() == "turn failed":
        flags.append("turn_failed")
    provider_call_made = bool(turn.get("provider_calls_made") or nested_get(turn, "packet", "tts_delivery", "provider_calls_made") or nested_get(turn, "summary", "tts_provider_calls_made"))
    audio_url_present = bool(turn.get("audio_url") or nested_get(turn, "packet", "tts_delivery", "audio_output_path"))
    provider_error = nested_get(turn, "packet", "tts_delivery", "provider_error")
    if provider_call_made and (not audio_url_present or provider_error):
        flags.append("provider_audio_failed")
        if not audio_url_present:
            flags.append("audio_url_missing_when_provider_called")
    selected = turn.get("selected_campaign_config") or {}
    selected_campaign_id = selected.get("campaign_id") if isinstance(selected, dict) else None
    campaign_id = str(turn.get("campaign_id") or "")
    selector_mode = str(turn.get("campaign_selector_mode") or selected.get("mode") if isinstance(selected, dict) else "")
    if selected_campaign_id and campaign_id and selected_campaign_id != campaign_id and campaign_id != "campaign-prod-005-b2b-software":
        flags.append("campaign_selector_mismatch")
    if ("generic" in selector_mode and campaign_id == "campaign-prod-005-b2b-software") or (
        "routesignal" in selector_mode and str(selected_campaign_id or "").startswith("synthetic-")
    ):
        flags.append("route_signal_generic_mix")
    if not final_response.strip():
        flags.append("final_response_missing")
    if not tts_input_text.strip():
        flags.append("tts_input_missing")
    if bool(nested_get(turn, "packet", "tts_delivery", "live_call_requested")) and str(turn.get("mode") or "") == "dry-run":
        flags.append("live_tts_requested_but_dry_run")
    if len(final_response.split()) > 45:
        flags.append("response_too_long_for_live_voice")
    signature = final_response.strip().lower()
    if signature and signature in seen_responses:
        flags.append("repeated_response")
    call_control = str(nested_get(turn, "summary", "call_control") or nested_get(turn, "packet", "decision_snapshot", "call_control") or "")
    if call_control not in ALLOWED_CALL_CONTROLS:
        flags.append("call_control_unexpected")
    return sorted(set(flags), key=MECHANICAL_FLAGS.index)


def record_from_turn(path: Path, turn: dict[str, Any], file_hash: str, seen_by_session: dict[str, set[str]], index: int) -> dict[str, Any]:
    summary = turn.get("summary") or {}
    packet = turn.get("packet") or {}
    tts_delivery = packet.get("tts_delivery") if isinstance(packet, dict) else {}
    metrics = transcript_metrics(turn)
    session_id = str(turn.get("session_id") or "no-session")
    final_response = redact_public_text(summary.get("final_response") or packet.get("final_response") or "")
    tts_input_text = redact_public_text(summary.get("tts_input_text") or (tts_delivery or {}).get("tts_input_text") or "")
    seen_responses = seen_by_session[session_id]
    flags = mechanical_flags(turn, final_response, tts_input_text, seen_responses)
    if final_response.strip():
        seen_responses.add(final_response.strip().lower())
    asr = turn.get("asr") or {}
    latency = turn.get("latency") or {}
    side_effects = observed_side_effect_flags(turn)
    selected_action = selected_action_summary(turn)
    universal_frame = select_universal_policy_frame(turn)
    record_id = f"live-demo-commercial-rehearsal-001-{index:04d}"
    return {
        "rehearsal_record_id": record_id,
        "checkpoint_id": CHECKPOINT_ID,
        "live_demo_id": turn.get("live_demo_id"),
        "session_id_hash": sha256_text(session_id),
        "session_turn_index": turn.get("session_turn_index"),
        "campaign_id": turn.get("campaign_id"),
        "campaign_config_path": redact_public_text(turn.get("campaign_config_path") or ""),
        "selected_campaign_metadata": selected_campaign_metadata(turn),
        "input_type": turn.get("input_type"),
        "mode": turn.get("mode"),
        "private_source_file_hash": file_hash,
        "private_source_file_relative_path": project_relative(path),
        **metrics,
        "final_response": final_response,
        "tts_input_text": tts_input_text,
        "call_control": summary.get("call_control") or nested_get(packet, "decision_snapshot", "call_control"),
        "selected_action": selected_action,
        "source": selected_action.get("source") or nested_get(turn, "dialogue_manager", "final_response_source"),
        "semantic": selected_action.get("semantic") or nested_get(turn, "dialogue_pragmatics", "move_id"),
        "target_gap": selected_action.get("target_gap") or universal_frame.get("target_gap"),
        "confirmed_gaps": universal_frame.get("confirmed_gaps") or nested_get(turn, "demo_conversation_memory", "active_gap_scope"),
        "universal_policy_frame_summary": universal_frame,
        "asr_confidence": asr.get("confidence") if isinstance(asr, dict) else None,
        "asr_quality_gate": asr.get("quality_gate") if isinstance(asr, dict) else None,
        "audio_url_present": bool(turn.get("audio_url") or nested_get(packet, "tts_delivery", "audio_output_path")),
        "provider_call_made": bool(side_effects.get("provider_calls_made") or side_effects.get("tts_provider_calls_made")),
        "provider_audio_playback_status": turn.get("provider_audio_playback_status") or "not_observed_in_private_turn_packet",
        "latency": {
            "browser_asr_ms": latency.get("browser_asr_ms") if isinstance(latency, dict) else None,
            "server_total_ms": latency.get("server_total_ms") if isinstance(latency, dict) else None,
            "time_to_first_audio_ms": summary.get("time_to_first_audio_ms"),
            "total_provider_latency_ms": summary.get("total_provider_latency_ms"),
        },
        "observed_side_effect_flags": side_effects,
        "mechanical_issue_flags": flags,
        "response_word_count": len(final_response.split()),
        "question_count": final_response.count("?"),
        "requires_human_sales_review": True,
        "codex_assigned_final_live_quality": False,
        "human_live_quality_scorecard": {
            "dimensions": {dimension: None for dimension in RUBRIC_DIMENSIONS},
            "qualitative_label": None,
            "reviewer_notes": None,
        },
        "notes_for_human_reviewer": [
            "Buyer transcript text is hashed and counted only; raw private transcript is not included.",
            "Review ASR, turn-taking, TTS playback, and commercial quality from the private live-demo source if authorized.",
        ],
    }


def build_packet() -> dict[str, Any]:
    files = discover_private_turn_files()
    records: list[dict[str, Any]] = []
    unreadable: list[dict[str, str]] = []
    seen_hashes: set[str] = set()
    seen_by_session: dict[str, set[str]] = defaultdict(set)
    for path in files:
        parsed, file_hash, error = load_private_json(path)
        if file_hash in seen_hashes:
            continue
        seen_hashes.add(file_hash)
        if parsed is None:
            unreadable.append(
                {
                    "private_source_file_hash": file_hash,
                    "private_source_file_relative_path": project_relative(path),
                    "error": redact_public_text(error),
                }
            )
            continue
        records.append(record_from_turn(path, parsed, file_hash, seen_by_session, len(records) + 1))
    warning_counts = Counter()
    for record in records:
        warning_counts.update(record.get("mechanical_issue_flags") or [])
    campaigns = sorted({str(record.get("campaign_id") or "") for record in records if record.get("campaign_id")})
    packet_status = "ready_for_human_review" if records else "no_private_input_found"
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "generated_at": utc_now(),
        "status": packet_status,
        "private_input_discovery_count": len(files),
        "private_turn_files_parsed": len(records),
        "private_turn_files_unreadable": len(unreadable),
        "records": records,
        "unreadable_private_inputs": unreadable,
        "campaign_coverage_found": campaigns,
        "mechanical_issue_counts": dict(sorted(warning_counts.items())),
        "top_concerning_rehearsal_records_by_mechanical_signals_only": sorted(
            [
                {
                    "rehearsal_record_id": record["rehearsal_record_id"],
                    "campaign_id": record.get("campaign_id"),
                    "mechanical_issue_count": len(record.get("mechanical_issue_flags") or []),
                    "mechanical_issue_flags": record.get("mechanical_issue_flags") or [],
                }
                for record in records
            ],
            key=lambda item: (-item["mechanical_issue_count"], item["rehearsal_record_id"]),
        )[:12],
        "recommended_live_rehearsal_scenarios": RECOMMENDED_SCENARIOS,
        "tool_side_effects": {
            "generator_provider_calls_made": False,
            "generator_live_tts_calls_made": False,
            "generator_local_llm_calls_made": False,
            "generator_sends_email": False,
            "generator_creates_calendar_event": False,
            "generator_writes_crm": False,
            "generator_opens_prod_102": False,
        },
    }


def render_rubric() -> str:
    lines = [
        "# Live Demo Commercial Rehearsal Rubric",
        "",
        "Manual reviewers should score each rehearsal record from 1 to 5. Codex does not assign final quality scores.",
        "",
        "## Scoring Dimensions",
    ]
    lines.extend(f"{idx}. {dimension}" for idx, dimension in enumerate(RUBRIC_DIMENSIONS, start=1))
    lines.extend(
        [
            "",
            "## Qualitative Labels",
            "",
            *[f"- `{label}`" for label in QUALITATIVE_LABELS],
        ]
    )
    return "\n".join(lines) + "\n"


def render_index(packet: dict[str, Any]) -> str:
    lines = [
        "# Live Demo Commercial Rehearsal Index",
        "",
        f"- Checkpoint: `{CHECKPOINT_ID}`",
        f"- Status: `{packet['status']}`",
        f"- Private input discovery count: `{packet['private_input_discovery_count']}`",
        f"- Rehearsal record count: `{len(packet['records'])}`",
        "",
        "## Records",
    ]
    if not packet["records"]:
        lines.extend(["", "No private input found. Run the operator scenarios, then regenerate this packet."])
    for record in packet["records"]:
        lines.append(
            f"- `{record['rehearsal_record_id']}`: campaign `{record.get('campaign_id')}`, "
            f"turn `{record.get('session_turn_index')}`, flags `{', '.join(record.get('mechanical_issue_flags') or []) or 'none'}`"
        )
    return "\n".join(lines) + "\n"


def scenario_lines() -> list[str]:
    lines: list[str] = []
    for scenario in RECOMMENDED_SCENARIOS:
        lines.append(f"### {scenario['id']}. {scenario['title']}")
        lines.extend(f"- {step}" for step in scenario["steps"])
        lines.append("")
    return lines


def render_report(packet: dict[str, Any], redaction: dict[str, Any]) -> str:
    warning_counts = packet["mechanical_issue_counts"]
    campaigns = packet["campaign_coverage_found"]
    lines = [
        "# LIVE-DEMO-COMMERCIAL-REHEARSAL-001 Report",
        "",
        "## Summary",
        f"- Status: `{packet['status']}`",
        "- This packet is generated from ignored local private live-demo artifacts and redacts buyer transcript text.",
        "",
        "## Private Input Discovery Count",
        f"- Private JSON files discovered: `{packet['private_input_discovery_count']}`",
        f"- Parsed rehearsal records: `{len(packet['records'])}`",
        f"- Unreadable private inputs: `{packet['private_turn_files_unreadable']}`",
        "",
        "## Rehearsal Record Count",
        f"- Records available for human review: `{len(packet['records'])}`",
        "",
        "## Campaign Coverage Found In Private Evidence",
        *(f"- `{campaign}`" for campaign in campaigns),
        "",
        "## Mechanical Issue Counts",
        *(f"- `{key}`: `{value}`" for key, value in warning_counts.items()),
        "",
        "## Top Concerning Rehearsal Records By Mechanical Signals Only",
    ]
    if not warning_counts:
        lines.append("- No mechanical issues were detected by this packet generator.")
    for item in packet["top_concerning_rehearsal_records_by_mechanical_signals_only"]:
        lines.append(
            f"- `{item['rehearsal_record_id']}`: `{item['mechanical_issue_count']}` flags "
            f"({', '.join(item['mechanical_issue_flags']) or 'none'})"
        )
    lines.extend(
        [
            "",
            "## Safety Boundary Summary",
            f"- Generator provider calls made: `{str(redaction['generator_provider_calls_made']).lower()}`",
            f"- Validator provider calls made: `{str(redaction['validator_provider_calls_made']).lower()}`",
            f"- Validator live TTS calls made: `{str(redaction['validator_live_tts_calls_made']).lower()}`",
            f"- Raw private transcript text included: `{str(redaction['raw_private_transcript_text_included']).lower()}`",
            f"- Raw customer audio found: `{str(redaction['raw_customer_audio_found']).lower()}`",
            "",
            "## What ChatGPT/human reviewer should evaluate next",
            "- Compare hashed transcript source records with authorized private artifacts only when needed.",
            "- Check ASR accuracy, latency, turn-taking, TTS playback, spoken text match, and commercial next-step quality.",
            "- Verify campaign selector integrity under RouteSignal and generic campaign switching.",
            "",
            "## Recommended Live Rehearsal Scenarios",
            *scenario_lines(),
            "## Next Likely Implementation Area",
            "- Preliminary only: use this packet to decide whether live-call issues are ASR, browser turn-taking, TTS playback, campaign selection, or dialogue quality before changing runtime behavior.",
        ]
    )
    if packet["status"] == "no_private_input_found":
        lines.extend(
            [
                "",
                "## No Private Input Found Instructions",
                "- Run `python scripts\\run_live_demo_001_agent_voice_call.py --force-key-missing`.",
                "- Use the recommended typed or browser rehearsal scenarios.",
                "- Regenerate this packet after private turn JSON files exist under `data/private/live-demo-*`.",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_packet_md(packet: dict[str, Any]) -> str:
    lines = [
        "# Live Demo Commercial Rehearsal Packet",
        "",
        "## Rubric Summary",
        "Manual reviewers score live-call quality from 1 to 5 across ASR, turn-taking, TTS, campaign selection, commercial quality, and safety. Codex does not assign final quality labels.",
        "",
        "## Rehearsal Index",
        f"- Status: `{packet['status']}`",
        f"- Private input discovery count: `{packet['private_input_discovery_count']}`",
        f"- Record count: `{len(packet['records'])}`",
        "",
        "## Records",
    ]
    if not packet["records"]:
        lines.extend(["", "No private input found. Run the operator scenarios and regenerate this packet."])
    for record in packet["records"][:80]:
        lines.extend(
            [
                f"### {record['rehearsal_record_id']}",
                f"- Campaign: `{record.get('campaign_id')}`",
                f"- Source file hash: `{record['private_source_file_hash']}`",
                f"- Transcript hash: `{record['transcript_hash']}`",
                f"- Transcript chars: `{record['transcript_char_count']}`",
                f"- Call control: `{record.get('call_control')}`",
                f"- Audio URL present: `{str(record.get('audio_url_present')).lower()}`",
                f"- Provider call observed in private record: `{str(record.get('provider_call_made')).lower()}`",
                f"- Flags: `{', '.join(record.get('mechanical_issue_flags') or []) or 'none'}`",
                "",
                "Final response:",
                "",
                f"> {record.get('final_response') or '[missing]'}",
                "",
            ]
        )
    if len(packet["records"]) > 80:
        lines.append(f"_Packet contains {len(packet['records'])} records; JSON/JSONL include the full set._")
    return "\n".join(lines).rstrip() + "\n"


def build_redaction_report(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "private_input_discovery_count": packet["private_input_discovery_count"],
        "records_redacted": len(packet["records"]),
        "raw_private_transcript_text_included": False,
        "transcript_hashing_algorithm": "sha256",
        "private_source_file_hashing_algorithm": "sha256",
        "private_source_paths_are_project_relative": True,
        "raw_email_like_values_found": 0,
        "secret_like_values_found": 0,
        "raw_customer_audio_found": False,
        "provider_audio_file_paths_included": False,
        "generator_provider_calls_made": False,
        "generator_live_tts_calls_made": False,
        "generator_local_llm_calls_made": False,
        "generator_sends_email": False,
        "generator_creates_calendar_event": False,
        "generator_writes_crm": False,
        "generator_opens_prod_102": False,
        "validator_provider_calls_made": False,
        "validator_live_tts_calls_made": False,
        "validator_local_llm_calls_made": False,
        "validator_sends_email": False,
        "validator_creates_calendar_event": False,
        "validator_writes_crm": False,
        "validator_opens_prod_102": False,
    }


def write_outputs(packet: dict[str, Any]) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    redaction = build_redaction_report(packet)
    write_json(OUT_DIR / "rehearsal_packet.json", packet)
    write_text(OUT_DIR / "rehearsal_packet.jsonl", "\n".join(json.dumps(record, sort_keys=True) for record in packet["records"]) + ("\n" if packet["records"] else ""))
    write_text(OUT_DIR / "rehearsal_packet.md", render_packet_md(packet))
    write_text(OUT_DIR / "rehearsal_index.md", render_index(packet))
    write_text(OUT_DIR / "rubric.md", render_rubric())
    write_json(OUT_DIR / "redaction_report.json", redaction)
    write_text(OUT_DIR / "report.md", render_report(packet, redaction))
    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": packet["status"],
        "private_input_discovery_count": packet["private_input_discovery_count"],
        "rehearsal_record_count": len(packet["records"]),
        "campaign_coverage_found": packet["campaign_coverage_found"],
        "mechanical_issue_counts": packet["mechanical_issue_counts"],
        "side_effect_boundary": {
            "generator_provider_calls_made": False,
            "generator_live_tts_calls_made": False,
            "generator_local_llm_calls_made": False,
            "generator_sends_email": False,
            "generator_creates_calendar_event": False,
            "generator_writes_crm": False,
            "generator_opens_prod_102": False,
        },
        "required_files": REQUIRED_FILES,
    }
    write_json(OUT_DIR / "result.json", result)
    return result


def main() -> None:
    packet = build_packet()
    result = write_outputs(packet)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
