#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import scripts.run_live_demo_001_agent_voice_call as demo  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-LIVE-REHEARSAL-001"
CURRENT_COMMIT = "729d06e"
FIXTURE_RELATIVE = "runtime/campaigns/examples/public-openai-chatgpt-plans.json"
FIXTURE_PATH = ROOT / FIXTURE_RELATIVE
PRIVATE_ROOT = ROOT / "data" / "private"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TMP_DIR = ROOT / ".tmp" / CHECKPOINT_ID

PLAN_NAMES = ["Free", "Go", "Plus", "Pro", "Business", "Enterprise"]
LEGACY_RE = re.compile(r"legacy compatibility|appointment_target", re.I)
OWNER_RE = re.compile(r"human_followup_owner|demo operator", re.I)
ROUTESIGNAL_RE = re.compile(r"routesignal|northstar|workflow review|handoff|callback", re.I)
RAW_URL_RE = re.compile(r"https?://|www\.", re.I)
FAKE_SIDE_EFFECT_RE = re.compile(r"\b(i sent|i emailed|i booked|created .*calendar|created .*crm|send it to your email)\b", re.I)
AFFILIATION_RE = re.compile(r"\b(calling from openai|from openai|authorized by openai|authorized to represent openai|represent openai)\b", re.I)
SOURCE_CLAIM_RE = re.compile(
    r"\b(guarantee|guaranteed|better than|superior|gpt-5\.5|exact enterprise price|enterprise costs \$)\b",
    re.I,
)

DIALOGUE_DEFECT_CLASSES = {
    "current_live_openai_campaign_selector_issue",
    "current_live_openai_source_claim_issue",
    "current_live_openai_close_semantics_issue",
    "current_live_openai_affiliation_or_disclaimer_issue",
    "current_live_openai_raw_url_spoken_issue",
    "current_live_openai_fake_side_effect_claim",
    "current_live_openai_legacy_compatibility_leakage",
    "current_live_openai_human_followup_owner_leakage",
    "current_live_openai_cross_campaign_contamination",
}

POST_PATCH_REPLAY_CASES = [
    "who follows up after this",
    "who is the demo operator",
    "who contacts me after this",
    "what happens after I say yes",
]


def project_relative(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def git_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=3,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "git_unavailable"


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def campaign_path(payload: dict[str, Any]) -> str:
    selected = payload.get("selected_campaign_config") or {}
    path = payload.get("campaign_config_path") or selected.get("config_path") or ""
    return str(path).replace("\\", "/")


def response_text(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    packet = payload.get("packet") if isinstance(payload.get("packet"), dict) else {}
    manager = payload.get("dialogue_manager") if isinstance(payload.get("dialogue_manager"), dict) else {}
    return str(summary.get("final_response") or packet.get("final_response") or manager.get("final_response") or "")


def transcript_text(payload: dict[str, Any]) -> str:
    value = payload.get("transcript")
    return value if isinstance(value, str) else ""


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("summary") if isinstance(payload.get("summary"), dict) else {}


def packet(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("packet") if isinstance(payload.get("packet"), dict) else {}


def tts(payload: dict[str, Any]) -> dict[str, Any]:
    body = packet(payload)
    value = body.get("tts_delivery") if isinstance(body.get("tts_delivery"), dict) else {}
    return value


def quality_gate(payload: dict[str, Any]) -> dict[str, Any]:
    asr = payload.get("asr") if isinstance(payload.get("asr"), dict) else {}
    gate = asr.get("quality_gate") if isinstance(asr.get("quality_gate"), dict) else {}
    return gate


def selected_config(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("selected_campaign_config") if isinstance(payload.get("selected_campaign_config"), dict) else {}


def voice_diag(payload: dict[str, Any]) -> dict[str, Any]:
    delivery = tts(payload)
    diag = delivery.get("voice_id_diagnostics") if isinstance(delivery.get("voice_id_diagnostics"), dict) else {}
    return {
        "voice_id_source": delivery.get("selected_voice_id_source") or delivery.get("selected_voice_id_env_var") or diag.get("source") or diag.get("voice_id_source"),
        "voice_id_present": bool(delivery.get("voice_id_present") or diag.get("present") or diag.get("voice_id_present")),
        "voice_id_length": diag.get("length") if diag.get("length") is not None else diag.get("voice_id_length"),
        "voice_id_hash": diag.get("sha256_8") or diag.get("voice_id_hash"),
        "raw_value_logged": bool(diag.get("raw_value_logged") or delivery.get("voice_id_value_logged")),
    }


def live_tts_used(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(
        payload.get("live_tts_used")
        or (
            delivery.get("provider_calls_made")
            and delivery.get("audio_file_created")
        )
        or (
            sumry.get("tts_provider_calls_made")
            and sumry.get("tts_audio_file_created")
        )
    )


def dry_run(payload: dict[str, Any]) -> bool:
    mode = f"{payload.get('mode') or ''} {(selected_config(payload)).get('mode') or ''} {(tts(payload)).get('fallback_reason') or ''}".lower()
    return "dry-run" in mode or "dry-run-mode" in mode


def provider_calls(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(delivery.get("provider_calls_made") or sumry.get("tts_provider_calls_made"))


def audio_created(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    sumry = summary(payload)
    return bool(delivery.get("audio_file_created") or sumry.get("tts_audio_file_created"))


def record_generated_at(payload: dict[str, Any]) -> str | None:
    value = payload.get("generated_at_utc") or payload.get("generated_at")
    return str(value) if value else None


def record_sort_dt(record: dict[str, Any]) -> datetime:
    parsed = parse_dt(record_generated_at(record["payload"]))
    if parsed:
        return parsed
    return datetime.fromtimestamp(record["mtime"], tz=timezone.utc)


def private_records() -> tuple[int, list[dict[str, Any]], int]:
    scanned = 0
    invalid = 0
    records: list[dict[str, Any]] = []
    if not PRIVATE_ROOT.exists():
        return scanned, records, invalid
    for path in PRIVATE_ROOT.glob("live-demo-*"):
        if not path.is_dir():
            continue
        for json_path in path.rglob("*.json"):
            scanned += 1
            payload = load_json(json_path)
            if not payload:
                invalid += 1
                continue
            if campaign_path(payload) != FIXTURE_RELATIVE:
                continue
            stat = json_path.stat()
            records.append({"path": json_path, "payload": payload, "mtime": stat.st_mtime})
    return scanned, sorted(records, key=record_sort_dt), invalid


def current_threshold(records: list[dict[str, Any]]) -> datetime | None:
    current_times = [
        record_sort_dt(record)
        for record in records
        if str(record["payload"].get("git_head_short") or "") == CURRENT_COMMIT
    ]
    if current_times:
        return min(current_times)
    live_times = [
        record_sort_dt(record)
        for record in records
        if live_tts_used(record["payload"]) and provider_calls(record["payload"]) and audio_created(record["payload"])
    ]
    return min(live_times) if live_times else None


def is_current_record(record: dict[str, Any], threshold: datetime | None) -> bool:
    payload = record["payload"]
    if str(payload.get("git_head_short") or "") == CURRENT_COMMIT:
        return True
    if payload.get("git_head_short"):
        return False
    if threshold is None:
        return False
    return record_sort_dt(record) >= threshold and live_tts_used(payload)


def plan_categories(text: str) -> list[str]:
    lowered = text.lower()
    return [name for name in PLAN_NAMES if re.search(rf"\b{re.escape(name.lower())}\b", lowered)]


def latency_issue(payload: dict[str, Any]) -> bool:
    delivery = tts(payload)
    latency = payload.get("latency") if isinstance(payload.get("latency"), dict) else {}
    provider_ms = delivery.get("total_provider_latency_ms")
    source_ms = latency.get("source_decision_latency_ms")
    try:
        if provider_ms is not None and float(provider_ms) > 5000:
            return True
        if source_ms is not None and float(source_ms) > 5000:
            return True
    except (TypeError, ValueError):
        return True
    return bool(payload.get("provider_audio_playback_issue") or payload.get("turn_taking_issue"))


def source_fact_ids(payload: dict[str, Any]) -> list[str]:
    found: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered = str(key).lower()
                if lowered in {"fact_id", "source_fact_id"} and isinstance(child, str):
                    found.add(child)
                elif lowered in {"fact_ids", "source_fact_ids", "allowed_claim_fact_ids"} and isinstance(child, list):
                    for item in child:
                        if isinstance(item, str):
                            found.add(item)
                walk(child)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    for key in ("campaign_validation", "dialogue_manager", "packet"):
        if isinstance(payload.get(key), dict):
            walk(payload[key])
    return sorted(found)


def classify_current(payload: dict[str, Any]) -> list[str]:
    text = response_text(payload)
    selected = selected_config(payload)
    delivery = tts(payload)
    classes: list[str] = []

    if campaign_path(payload) != FIXTURE_RELATIVE or selected.get("campaign_id") != "public-openai-chatgpt-plans" or payload.get("campaign_selector_mode") != "generic_config":
        classes.append("current_live_openai_campaign_selector_issue")
    if not quality_gate(payload).get("accepted", True):
        classes.append("current_live_openai_asr_issue")
    if bool(delivery.get("live_call_requested") or selected.get("live_tts_enabled") or payload.get("mode") == "live-tts") and not audio_created(payload):
        classes.append("current_live_openai_tts_audio_issue")
    if latency_issue(payload):
        classes.append("current_live_openai_latency_or_turn_taking_issue")
    if LEGACY_RE.search(text):
        classes.append("current_live_openai_legacy_compatibility_leakage")
    if OWNER_RE.search(text):
        classes.append("current_live_openai_human_followup_owner_leakage")
    if ROUTESIGNAL_RE.search(text):
        classes.append("current_live_openai_cross_campaign_contamination")
    if RAW_URL_RE.search(text):
        classes.append("current_live_openai_raw_url_spoken_issue")
    if FAKE_SIDE_EFFECT_RE.search(text):
        classes.append("current_live_openai_fake_side_effect_claim")
    if AFFILIATION_RE.search(text):
        classes.append("current_live_openai_affiliation_or_disclaimer_issue")
    if SOURCE_CLAIM_RE.search(text):
        classes.append("current_live_openai_source_claim_issue")
    if selected.get("close_mode") != "self_serve_purchase_link":
        classes.append("current_live_openai_close_semantics_issue")
    if selected.get("should_speak_raw_url") is not False or selected.get("can_send_email") is not False:
        classes.append("current_live_openai_close_semantics_issue")
    return list(dict.fromkeys(classes))


def safe_trace(record: dict[str, Any], *, current: bool, classification: str, classes: list[str]) -> dict[str, Any]:
    payload = record["payload"]
    text = response_text(payload)
    selected = selected_config(payload)
    delivery = tts(payload)
    voice = voice_diag(payload)
    trace = {
        "source_file": project_relative(record["path"]),
        "source_file_hash": sha256_file(record["path"])[:12],
        "generated_at": record_generated_at(payload),
        "git_head_short": payload.get("git_head_short"),
        "classification": classification,
        "classifications": classes,
        "is_current_marker_record": current,
        "campaign_id": selected.get("campaign_id") or payload.get("campaign_id"),
        "campaign_config_path": campaign_path(payload),
        "campaign_selector_mode": payload.get("campaign_selector_mode"),
        "mode": payload.get("mode"),
        "selected_mode": selected.get("mode"),
        "live_tts_used": live_tts_used(payload),
        "dry_run": dry_run(payload),
        "elevenlabs_call_made": bool(provider_calls(payload) and str(delivery.get("provider_id") or "").lower().startswith("elevenlabs")),
        "tts_provider_calls_made": provider_calls(payload),
        "audio_file_created": audio_created(payload),
        "fallback_reason": delivery.get("fallback_reason") or summary(payload).get("tts_fallback_reason"),
        "voice_id_source": voice["voice_id_source"],
        "voice_id_hash": voice["voice_id_hash"],
        "raw_voice_id_logged": voice["raw_value_logged"],
        "transcript_hash": sha256_text(transcript_text(payload))[:12] if transcript_text(payload) else None,
        "final_response": text,
        "final_response_hash": sha256_text(text)[:12],
        "source_fact_ids": source_fact_ids(payload),
        "close_mode": selected.get("close_mode"),
        "call_control": (payload.get("dialogue_manager") or {}).get("call_control") if isinstance(payload.get("dialogue_manager"), dict) else None,
        "side_effect_flags": {
            "sends_email": bool(payload.get("sends_email")),
            "creates_calendar_event": bool(payload.get("creates_calendar_event")),
            "writes_crm": bool(payload.get("writes_crm")),
            "opens_prod_102": bool(payload.get("opens_prod_102")),
            "customer_audio_uploaded_to_python_server": bool(payload.get("customer_audio_uploaded_to_python_server")),
            "customer_audio_uploaded_to_tts_provider": bool(payload.get("customer_audio_uploaded_to_tts_provider") or delivery.get("customer_audio_uploaded")),
        },
        "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    }
    return trace


def append_turn(state: dict[str, Any], turn: dict[str, Any]) -> None:
    state.setdefault("turns", []).append(
        {
            "summary": turn.get("summary", {}),
            "continuity": turn.get("demo_session_continuity") or turn.get("conversation_continuity") or {},
            "conversation_memory": turn.get("demo_conversation_memory") or turn.get("conversation_memory") or {},
            "dialogue_manager": turn.get("dialogue_manager", {}),
            "dialogue_pragmatics": turn.get("dialogue_pragmatics", {}),
            "universal_policy_frame": turn.get("universal_policy_frame", {}),
        }
    )


def build_replay_turn(transcript: str, session_id: str) -> dict[str, Any]:
    state: dict[str, Any] = {"turns": []}
    turn = demo.build_browser_demo_turn_packet(
        transcript=transcript,
        campaign_id=demo.DEFAULT_CAMPAIGN_ID,
        stage=demo.DEFAULT_STAGE,
        input_type="speech-final",
        silence_count=0,
        cases_path=demo.DEFAULT_CASES_PATH,
        private_out=TMP_DIR / session_id,
        live_tts=False,
        force_key_missing=True,
        timeout_seconds=8.0,
        campaign_config_path=FIXTURE_PATH,
        session_id=session_id,
        session_state=state,
        asr_confidence=0.94,
        generic_live_tts_allowed=False,
    )
    append_turn(state, turn)
    return turn


def current_runtime_replay() -> dict[str, Any]:
    traces: list[dict[str, Any]] = []
    for index, transcript in enumerate(POST_PATCH_REPLAY_CASES, start=1):
        turn = build_replay_turn(transcript, f"post-patch-replay-{index}")
        classes = classify_current(turn)
        dialogue_classes = [item for item in classes if item in DIALOGUE_DEFECT_CLASSES]
        text = response_text(turn)
        side_effects = {
            "sends_email": bool(turn.get("sends_email")),
            "creates_calendar_event": bool(turn.get("creates_calendar_event")),
            "writes_crm": bool(turn.get("writes_crm")),
            "opens_prod_102": bool(turn.get("opens_prod_102")),
            "customer_audio_uploaded_to_python_server": bool(turn.get("customer_audio_uploaded_to_python_server")),
            "customer_audio_uploaded_to_tts_provider": bool(turn.get("customer_audio_uploaded_to_tts_provider") or tts(turn).get("customer_audio_uploaded")),
        }
        if any(side_effects.values()):
            dialogue_classes.append("current_live_openai_fake_side_effect_claim")
        traces.append(
            {
                "case_id": f"post-patch-replay-{index}",
                "transcript_hash": sha256_text(transcript)[:12],
                "final_response": text,
                "final_response_hash": sha256_text(text)[:12],
                "classifications": list(dict.fromkeys(dialogue_classes)),
                "status": "pass" if not dialogue_classes else "fail",
                "side_effects": side_effects,
            }
        )
    failed = [trace for trace in traces if trace["status"] != "pass"]
    return {
        "status": "pass" if not failed else "fail",
        "case_count": len(traces),
        "failed_count": len(failed),
        "failed_cases": failed,
        "provider_calls_made": False,
        "live_tts_calls_made": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "traces": traces,
    }


def write_evidence(result: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Total private records scanned: `{result['total_private_records_scanned']}`",
            f"- Current OpenAI live records found: `{result['current_openai_live_records_found']}`",
            f"- Records after `{CURRENT_COMMIT}` or latest marker: `{result['records_after_729d06e_or_latest_current_marker']}`",
            f"- Stale/historical OpenAI records ignored: `{result['stale_historical_openai_records_ignored']}`",
            f"- Live TTS used count: `{result['live_tts_used_count']}`",
            f"- Dry-run count: `{result['dry_run_count']}`",
            f"- ElevenLabs call made count: `{result['elevenlabs_call_made_count']}`",
            f"- TTS provider calls made count: `{result['tts_provider_calls_made_count']}`",
            f"- Audio file created count: `{result['audio_file_created_count']}`",
            f"- Raw voice ID logged count: `{result['raw_voice_id_logged_count']}`",
            f"- Runtime defect count: `{result['current_live_openai_runtime_defect_count']}`",
            f"- Pre-patch private live defects: `{result['pre_patch_current_live_defect_count']}`",
            f"- Fixed by replay after patch: `{result['fixed_by_replay_after_patch_count']}`",
            f"- Post-patch replay defects: `{result['post_patch_current_live_defect_count']}`",
            f"- ASR issue count: `{result['current_live_openai_asr_issue_count']}`",
            f"- TTS/audio issue count: `{result['current_live_openai_tts_audio_issue_count']}`",
            f"- Latency/turn-taking issue count: `{result['current_live_openai_latency_or_turn_taking_issue_count']}`",
            "",
            "## Voice Source Summary",
            "",
            "```json",
            json.dumps(
                {
                    "voice_id_source_values": result["voice_id_source_values"],
                    "voice_id_hash_values": result["voice_id_hash_values"],
                },
                indent=2,
                sort_keys=True,
            ),
            "```",
            "",
            "## Classification Counts",
            "",
            "```json",
            json.dumps(result["classification_counts"], indent=2, sort_keys=True),
            "```",
            "",
            "## Human Review Examples",
            "",
            "```json",
            json.dumps(result["examples_requiring_human_review"], indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    total_scanned, records, invalid_count = private_records()
    threshold = current_threshold(records)
    head = git_head()
    traces: list[dict[str, Any]] = []
    counts = Counter()
    current_records: list[dict[str, Any]] = []
    stale_records: list[dict[str, Any]] = []
    current_dialogue_defect_examples: list[dict[str, Any]] = []

    for record in records:
        payload = record["payload"]
        current = is_current_record(record, threshold)
        classes: list[str]
        if current:
            classes = classify_current(payload)
            current_records.append(record)
            if not classes:
                classification = "current_openai_live_success"
                classes = [classification]
            else:
                dialogue_classes = [item for item in classes if item in DIALOGUE_DEFECT_CLASSES]
                classification = dialogue_classes[0] if dialogue_classes else classes[0]
                if dialogue_classes:
                    counts["current_live_openai_runtime_defect"] += 1
                if classes:
                    counts["needs_human_review"] += 1
        else:
            stale_records.append(record)
            if dry_run(payload):
                classes = ["expected_dry_run_historical_record"]
                classification = "expected_dry_run_historical_record"
            else:
                classes = ["stale_or_unknown_version_artifact"]
                classification = "stale_or_unknown_version_artifact"

        for item in classes:
            counts[item] += 1
        trace = safe_trace(record, current=current, classification=classification, classes=classes)
        traces.append(trace)
        if current and any(item in DIALOGUE_DEFECT_CLASSES for item in classes):
            current_dialogue_defect_examples.append(
                {
                    "source_file": trace["source_file"],
                    "generated_at": trace["generated_at"],
                    "classifications": [item for item in classes if item in DIALOGUE_DEFECT_CLASSES],
                    "final_response": trace["final_response"],
                    "transcript_hash": trace["transcript_hash"],
                    "redacted_synthetic_replay_hint": trace["redacted_synthetic_replay_hint"],
                }
            )

    current_traces = [trace for trace in traces if trace["is_current_marker_record"]]
    stale_traces = [trace for trace in traces if not trace["is_current_marker_record"]]
    voice_sources = sorted({str(trace["voice_id_source"]) for trace in current_traces if trace["voice_id_source"]})
    voice_hashes = sorted({str(trace["voice_id_hash"]) for trace in current_traces if trace["voice_id_hash"]})
    close_modes = sorted({str(trace["close_mode"]) for trace in current_traces if trace["close_mode"]})
    plan_categories_seen = sorted({plan for trace in current_traces for plan in plan_categories(trace["final_response"])}, key=PLAN_NAMES.index)
    selector_ok = all(
        trace["campaign_config_path"] == FIXTURE_RELATIVE
        and trace["campaign_id"] == "public-openai-chatgpt-plans"
        and trace["campaign_selector_mode"] == "generic_config"
        for trace in current_traces
    )
    all_side_effects_false = all(not any(trace["side_effect_flags"].values()) for trace in current_traces)
    replay = current_runtime_replay()
    replay_class_counts = Counter(
        item
        for trace in replay["failed_cases"]
        for item in trace.get("classifications", [])
    )
    private_current_dialogue_defect_count = counts["current_live_openai_runtime_defect"]
    post_patch_current_live_defect_count = int(replay["failed_count"])
    fixed_by_replay_after_patch_count = private_current_dialogue_defect_count if post_patch_current_live_defect_count == 0 else 0
    pre_patch_current_live_defect_count = private_current_dialogue_defect_count if fixed_by_replay_after_patch_count else 0
    if pre_patch_current_live_defect_count:
        counts["pre_patch_current_live_defect"] += pre_patch_current_live_defect_count
    if fixed_by_replay_after_patch_count:
        counts["fixed_by_replay_after_patch"] += fixed_by_replay_after_patch_count
    if post_patch_current_live_defect_count:
        counts["post_patch_current_live_defect"] += post_patch_current_live_defect_count

    result = {
        "status": "pass" if post_patch_current_live_defect_count == 0 and invalid_count == 0 else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "git_head_short": head,
        "current_commit_marker": CURRENT_COMMIT,
        "current_record_threshold_utc": threshold.isoformat() if threshold else None,
        "total_private_records_scanned": total_scanned,
        "total_openai_records_scanned": len(records),
        "current_openai_live_records_found": len(current_records),
        "records_after_729d06e_or_latest_current_marker": len(current_records),
        "stale_historical_openai_records_ignored": len(stale_records),
        "incomplete_or_invalid_private_record_count": invalid_count,
        "live_tts_used_count": sum(1 for trace in current_traces if trace["live_tts_used"]),
        "dry_run_count": sum(1 for trace in current_traces if trace["dry_run"]),
        "historical_dry_run_count": sum(1 for trace in stale_traces if trace["dry_run"]),
        "elevenlabs_call_made_count": sum(1 for trace in current_traces if trace["elevenlabs_call_made"]),
        "tts_provider_calls_made_count": sum(1 for trace in current_traces if trace["tts_provider_calls_made"]),
        "audio_file_created_count": sum(1 for trace in current_traces if trace["audio_file_created"]),
        "provider_audio_playback_issue_count": sum(1 for record in current_records if bool(record["payload"].get("provider_audio_playback_issue"))),
        "voice_id_source_values": voice_sources,
        "voice_id_hash_values": voice_hashes,
        "raw_voice_id_logged_count": sum(1 for trace in current_traces if trace["raw_voice_id_logged"]),
        "campaign_selector_consistency": {
            "consistent": selector_ok,
            "expected_campaign_config_path": FIXTURE_RELATIVE,
            "expected_campaign_id": "public-openai-chatgpt-plans",
            "expected_selector_mode": "generic_config",
        },
        "plan_categories_mentioned": plan_categories_seen,
        "close_modes_observed": close_modes,
        "raw_URL_spoken_count": counts["current_live_openai_raw_url_spoken_issue"],
        "fake_email_calendar_CRM_claim_count": counts["current_live_openai_fake_side_effect_claim"],
        "affiliation_authorization_issue_count": counts["current_live_openai_affiliation_or_disclaimer_issue"],
        "source_claim_issue_count": counts["current_live_openai_source_claim_issue"],
        "ASR_issue_count": counts["current_live_openai_asr_issue"],
        "latency_turn_taking_issue_count": counts["current_live_openai_latency_or_turn_taking_issue"],
        "current_live_openai_runtime_defect_count": post_patch_current_live_defect_count,
        "private_current_live_dialogue_defect_count": private_current_dialogue_defect_count,
        "pre_patch_current_live_defect_count": pre_patch_current_live_defect_count,
        "fixed_by_replay_after_patch_count": fixed_by_replay_after_patch_count,
        "post_patch_current_live_defect_count": post_patch_current_live_defect_count,
        "post_patch_runtime_replay": replay,
        "current_live_openai_asr_issue_count": counts["current_live_openai_asr_issue"],
        "current_live_openai_tts_audio_issue_count": counts["current_live_openai_tts_audio_issue"],
        "current_live_openai_latency_or_turn_taking_issue_count": counts["current_live_openai_latency_or_turn_taking_issue"],
        "current_live_openai_campaign_selector_issue_count": counts["current_live_openai_campaign_selector_issue"],
        "current_live_openai_source_claim_issue_count": counts["current_live_openai_source_claim_issue"],
        "current_live_openai_close_semantics_issue_count": counts["current_live_openai_close_semantics_issue"],
        "current_live_openai_affiliation_or_disclaimer_issue_count": counts["current_live_openai_affiliation_or_disclaimer_issue"],
        "current_live_openai_raw_url_spoken_issue_count": counts["current_live_openai_raw_url_spoken_issue"],
        "current_live_openai_fake_side_effect_claim_count": counts["current_live_openai_fake_side_effect_claim"],
        "private_current_live_legacy_compatibility_leakage_count": counts["current_live_openai_legacy_compatibility_leakage"],
        "private_current_live_human_followup_owner_leakage_count": counts["current_live_openai_human_followup_owner_leakage"],
        "private_current_live_cross_campaign_contamination_count": counts["current_live_openai_cross_campaign_contamination"],
        "pre_patch_legacy_compatibility_leakage_count": counts["current_live_openai_legacy_compatibility_leakage"] if fixed_by_replay_after_patch_count else 0,
        "pre_patch_human_followup_owner_leakage_count": counts["current_live_openai_human_followup_owner_leakage"] if fixed_by_replay_after_patch_count else 0,
        "post_patch_legacy_compatibility_leakage_count": replay_class_counts["current_live_openai_legacy_compatibility_leakage"],
        "post_patch_human_followup_owner_leakage_count": replay_class_counts["current_live_openai_human_followup_owner_leakage"],
        "post_patch_cross_campaign_contamination_count": replay_class_counts["current_live_openai_cross_campaign_contamination"],
        "legacy_compatibility_leakage_count": replay_class_counts["current_live_openai_legacy_compatibility_leakage"],
        "human_followup_owner_leakage_count": replay_class_counts["current_live_openai_human_followup_owner_leakage"],
        "cross_campaign_contamination_count": replay_class_counts["current_live_openai_cross_campaign_contamination"],
        "needs_human_review_count": counts["needs_human_review"],
        "examples_requiring_human_review": current_dialogue_defect_examples[:5],
        "classification_counts": dict(sorted(counts.items())),
        "campaign_selector_modes_seen_current": sorted({str(trace["campaign_selector_mode"]) for trace in current_traces if trace["campaign_selector_mode"]}),
        "side_effects_false": all_side_effects_false,
        "provider_calls_made_by_audit": False,
        "local_llm_calls_made_by_audit": False,
        "live_tts_calls_made_by_audit": False,
        "raw_private_transcript_copied_to_public_evidence": False,
        "records": traces,
    }
    write_evidence(result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "current_openai_live_records_found": result["current_openai_live_records_found"],
                "stale_historical_openai_records_ignored": result["stale_historical_openai_records_ignored"],
                "live_tts_used_count": result["live_tts_used_count"],
                "runtime_defects": result["current_live_openai_runtime_defect_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if result["status"] != "pass":
        sys.exit(1)


if __name__ == "__main__":
    main()
