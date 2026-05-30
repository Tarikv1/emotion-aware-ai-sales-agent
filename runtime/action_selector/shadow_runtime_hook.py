from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
IMPORT_CONFIG_PATH = Path(__file__).resolve().parent / "shadow_runtime_import_config.json"
ENV_GATE = "ACTION_SELECTOR_RUNTIME_SHADOW_IMPORT_ENABLED"
PUBLIC_EVIDENCE_ENV_GATE = "ACTION_SELECTOR_PUBLIC_EVIDENCE_WRITE_ENABLED"
PRIVATE_LOCAL_LOG_ENV_GATE = "ACTION_SELECTOR_PRIVATE_LOCAL_LOG_ENABLED"

FALSE_RUNTIME_FLAGS = {
    "should_not_change_runtime": True,
    "live_runtime_wiring_allowed": False,
    "selector_control_allowed": False,
    "response_text_changed": False,
    "runtime_behavior_changed": False,
    "side_effects_allowed": False,
    "memory_mutation_allowed": False,
    "provider_calls_made": False,
    "openai_api_calls_made": False,
    "ultravox_calls_made": False,
    "elevenlabs_calls_made": False,
    "local_llm_calls_made": False,
    "ollama_calls_made": False,
    "tts_calls_made": False,
    "buyer_facing_text_generated": False,
    "audio_data_used": False,
    "raw_private_data": False,
}

PUBLIC_FORBIDDEN_RECORD_KEYS = {
    "candidate_response",
    "response_text",
    "agent_response",
    "final_response",
    "audio",
    "audio_path",
    "audio_file",
    "wav_path",
    "mp3_path",
    "raw_url",
}


def _env_enabled(name: str, env: dict | None = None) -> bool:
    source = os.environ if env is None else env
    return str(source.get(name) or "") == "1"


def should_run_action_selector_runtime_shadow_import(env: dict | None = None) -> bool:
    return _env_enabled(ENV_GATE, env)


def should_run_action_selector_shadow_logging(env: dict | None = None) -> bool:
    return should_run_action_selector_runtime_shadow_import(env)


def load_shadow_runtime_import_config() -> dict[str, Any]:
    try:
        payload = json.loads(IMPORT_CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _disabled_response(reason: str) -> dict[str, Any]:
    return {
        "enabled": False,
        "reason": reason,
        "record": None,
        "runtime_metadata_extraction_supported": True,
        "output_written": False,
        **FALSE_RUNTIME_FLAGS,
    }


def _safe_mode(turn_context: dict[str, Any], config: dict[str, Any]) -> str:
    requested = str(turn_context.get("mode") or "").strip()
    if requested == "offline_replay_shadow":
        requested = "offline_sanitized_replay"
    allowed = set(config.get("allowed_modes") or [])
    if requested in allowed and requested != "disabled_noop":
        return requested
    return "runtime_shadow_read_only"


def _resolved_output_path(value: Any) -> Path | None:
    if not str(value or "").strip():
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = ROOT / path
    try:
        return path.resolve()
    except OSError:
        return None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _private_source(value: Any) -> bool:
    source = str(value or "").replace("\\", "/").casefold()
    return "data/private" in source or "private-restricted" in source


def _contains_forbidden_record_key(payload: Any) -> bool:
    if isinstance(payload, dict):
        if PUBLIC_FORBIDDEN_RECORD_KEYS & set(payload):
            return True
        return any(_contains_forbidden_record_key(value) for value in payload.values())
    if isinstance(payload, list):
        return any(_contains_forbidden_record_key(value) for value in payload)
    return False


def _public_context_allowed(turn_context: dict[str, Any]) -> bool:
    if turn_context.get("sanitized") is not True:
        return False
    if turn_context.get("raw_private_data") is not False:
        return False
    sanitized_text = str(turn_context.get("buyer_utterance_text_sanitized") or "").strip()
    if not sanitized_text:
        return False
    if _private_source(turn_context.get("evidence_source") or turn_context.get("source_file")):
        return False
    return True


def _public_record_allowed(record: dict[str, Any]) -> bool:
    if record.get("raw_private_data") is not False or record.get("public_evidence_sanitized") is not True:
        return False
    if str(record.get("mode") or "") != "offline_sanitized_replay":
        return False
    if record.get("validation_errors"):
        return False
    if _private_source(record.get("evidence_source")):
        return False
    if _contains_forbidden_record_key(record):
        return False
    if not str(record.get("buyer_utterance_text_sanitized") or "").strip():
        return False
    return True


def _public_write_allowed(
    record: dict[str, Any],
    turn_context: dict[str, Any],
    output_path: Path,
    env: dict | None = None,
) -> bool:
    if not should_run_action_selector_runtime_shadow_import(env):
        return False
    if not _env_enabled(PUBLIC_EVIDENCE_ENV_GATE, env):
        return False
    if not _public_context_allowed(turn_context):
        return False
    if not _public_record_allowed(record):
        return False
    generated_root = ROOT / "research" / "experiments" / "generated"
    return _is_relative_to(output_path, generated_root)


def _private_write_allowed(output_path: Path, env: dict | None = None) -> bool:
    if not _env_enabled(PRIVATE_LOCAL_LOG_ENV_GATE, env):
        return False
    return _is_relative_to(output_path, ROOT / "local_artifacts")


def _append_if_safe(record: dict[str, Any], turn_context: dict[str, Any], env: dict | None = None) -> bool:
    output_path = _resolved_output_path(turn_context.get("output_path"))
    if output_path is None:
        return False
    if not (_public_write_allowed(record, turn_context, output_path, env) or _private_write_allowed(output_path, env)):
        return False
    from runtime.action_selector.shadow_runtime_logger import append_shadow_record_jsonl

    append_shadow_record_jsonl(output_path, record)
    return True


def _runtime_response(record: dict[str, Any], *, output_written: bool) -> dict[str, Any]:
    record.update(FALSE_RUNTIME_FLAGS)
    return {
        "enabled": True,
        "reason": "read_only_shadow_record_built_in_memory_only",
        "record": record,
        "runtime_metadata_extraction_supported": True,
        "output_written": output_written,
        **FALSE_RUNTIME_FLAGS,
    }


def maybe_log_action_selector_shadow_turn(turn_context: dict) -> dict:
    if not should_run_action_selector_runtime_shadow_import():
        return _disabled_response(f"{ENV_GATE}_not_set")
    try:
        config = load_shadow_runtime_import_config()
        context = deepcopy(turn_context) if isinstance(turn_context, dict) else {}
        mode = _safe_mode(context, config)
        from runtime.action_selector.shadow_runtime_logger import run_shadow_selector_read_only

        record = run_shadow_selector_read_only(
            context,
            expected_action_id=str(context.get("expected_action_id") or ""),
            mode=mode,
        )
        output_written = _append_if_safe(record, context)
        return _runtime_response(record, output_written=output_written)
    except Exception as exc:
        return {
            "enabled": True,
            "reason": f"runtime_shadow_import_failed:{type(exc).__name__}",
            "record": None,
            "runtime_metadata_extraction_supported": False,
            "output_written": False,
            "error_type": type(exc).__name__,
            **FALSE_RUNTIME_FLAGS,
        }
