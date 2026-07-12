#!/usr/bin/env python3
"""Guarded plan/live patcher for ELEVENLABS-040 detailed pricing control.

Default mode performs fresh live GET readback and writes sanitized plan-only
evidence. Provider writes require the exact confirm-provider-write token.
This command never runs simulations or outbound calls.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    import apply_elevenlabs_039_independent_test_hardening as guards
    from apply_elevenlabs_038_end_call_terminal_control import (
        active_kb_paths,
        get_prompt,
        json_request,
        multipart_update_file,
        summarize_tools,
        unrelated_tool_fingerprint,
    )
except ImportError as exc:  # pragma: no cover - import paths are environment-specific
    raise SystemExit(f"error: cannot import required guarded ElevenLabs helpers: {exc}") from exc


API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
CHECKPOINT_ID = "ELEVENLABS-040-detailed-pricing-control"
AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
AGENT_NAME = "web design"
CONFIRM_TOKEN = "confirm-provider-write"
SOURCE_EVIDENCE_ORIGIN = "repo_head_source_before_provider_write_not_network_capture"
TARGET_LLM = {
    "llm": "gpt-5.5",
    "temperature": 0.1,
    "thinking_budget": None,
    "reasoning_effort": "none",
}
TARGET_PRICE_VARIABLES = {
    "website_starting_price": "$500",
    "website_basic_site_range": "$900-$1,500",
    "website_light_feature_range": "$1,800-$3,000",
    "website_workflow_content_range": "$2,800-$4,500",
    "website_integration_heavy_range": "$4,000-$6,500",
    "website_premium_price_anchor": "$6,500",
}
APPROVED_DYNAMIC_PLACEHOLDER_VALUE_KEYS = set(TARGET_PRICE_VARIABLES) | {
    "website_price_disclosure_rule",
}
SENSITIVE_DYNAMIC_CONTEXT_KEYS = {
    "address",
    "business_address",
    "business_city",
    "business_email",
    "business_name",
    "business_phone",
    "business_type",
    "business",
    "city",
    "company",
    "company_name",
    "contact",
    "contact_email",
    "contact_name",
    "contact_phone",
    "customer_email",
    "customer_name",
    "customer_phone",
    "customer",
    "domain",
    "email",
    "owner",
    "owner_email",
    "owner_name",
    "owner_phone",
    "phone",
    "prospect_email",
    "prospect_name",
    "prospect_phone",
    "prospect",
    "service",
    "service_name",
    "service_type",
    "state",
    "website",
    "website_url",
}
SENSITIVE_DYNAMIC_CONTEXT_RE = re.compile(
    r"(?:business|company|contact|customer|prospect|owner).*(?:name|type|city|address|email|phone|website|domain)"
    r"|(?:city|address|email|phone|website|domain)$",
    re.IGNORECASE,
)
SECRET_LIKE_KEY_RE = re.compile(r"(?:authorization|auth|api[_-]?key|token|secret|cookie)", re.IGNORECASE)
JSON_STRING_PAIR_RE = re.compile(r'("(?P<key>[^"]+)"\s*:\s*)"(?P<value>(?:\\.|[^"\\])*)"')
BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+")
ERROR_FIELD_BOUNDARY_RE = re.compile(
    r"\b(?P<key>"
    r"business(?:_name|_type|_city|_address|_email|_phone)?|"
    r"company(?:_name|_type|_city|_address|_email|_phone)?|"
    r"customer(?:_name|_type|_city|_address|_email|_phone)?|"
    r"prospect(?:_name|_type|_city|_address|_email|_phone)?|"
    r"contact(?:_name|_type|_city|_address|_email|_phone)?|"
    r"owner(?:_name|_type|_city|_address|_email|_phone)?|"
    r"service(?:_name|_type)?|"
    r"city|address|email|phone|website|website_url|domain|"
    r"authorization|auth|api[_-]?key|token|secret|cookie|"
    r"type|message|error|detail|status|code|request_id"
    r")\b(?P<sep>\s*[:=]\s*)",
    re.IGNORECASE,
)
KB_DOCS = (
    "atlas_offer_facts.md",
    "atlas_price_scope_cost_drivers.md",
    "atlas_output_quality_rules.md",
)
KNOWN_KB_DOC_IDS = {
    "atlas_offer_facts.md": "HYTfB5s1Z8LzOw8oBADt",
    "atlas_price_scope_cost_drivers.md": "vGKk14CCzKqGW3GxgUqA",
    "atlas_output_quality_rules.md": "GS5wqgcUomoJmqWCEpP7",
}
KB_REQUEST_SOURCE_MARKERS = {
    "atlas_offer_facts.md": (
        "Quick Launch: `$500-$800`",
        "Essential Local: `{{website_basic_site_range}}`",
        "Integration Website: `{{website_integration_heavy_range}}`",
    ),
    "atlas_price_scope_cost_drivers.md": (
        "If support need is unclear, default to Essential Care",
        "Base Package Ladder",
        "{{website_integration_heavy_range}}",
    ),
    "atlas_output_quality_rules.md": (
        "Pricing Quote Discipline",
        "Never disclose a paid price before explicit buyer price intent.",
        "For care, quote exactly one relevant plan after ongoing-cost intent; default to Essential Care if support need is unclear.",
    ),
}
PROMPT_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
KB_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "atlas_web_studio"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def should_redact_dynamic_placeholder(key: str) -> bool:
    return key not in APPROVED_DYNAMIC_PLACEHOLDER_VALUE_KEYS


def should_redact_context_key(key: str) -> bool:
    normalized = key.strip().lower()
    return normalized in SENSITIVE_DYNAMIC_CONTEXT_KEYS or bool(SENSITIVE_DYNAMIC_CONTEXT_RE.fullmatch(normalized))


def redacted_dynamic_value(value: Any) -> Any:
    if value in (None, "", [], {}):
        return value
    return "[REDACTED_DYNAMIC_PLACEHOLDER]"


def sanitize(value: Any, *, key_hint: str = "", in_dynamic_placeholders: bool = False) -> Any:
    if in_dynamic_placeholders and should_redact_dynamic_placeholder(key_hint):
        return redacted_dynamic_value(value)
    if should_redact_context_key(key_hint):
        return redacted_dynamic_value(value)
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for raw_key, raw_value in value.items():
            key = str(raw_key)
            if key == "dynamic_variable_placeholders" and isinstance(raw_value, dict):
                clean[key] = {
                    str(placeholder_key): sanitize(
                        placeholder_value,
                        key_hint=str(placeholder_key),
                        in_dynamic_placeholders=True,
                    )
                    for placeholder_key, placeholder_value in raw_value.items()
                }
            else:
                clean[key] = sanitize(raw_value, key_hint=key)
        return guards.sanitize(clean)
    if isinstance(value, list):
        return [sanitize(item, key_hint=key_hint, in_dynamic_placeholders=in_dynamic_placeholders) for item in value]
    return guards.sanitize(value)


def redact_error_key_value(key: str, value: str) -> str | None:
    if SECRET_LIKE_KEY_RE.search(key):
        return "[REDACTED]"
    if should_redact_context_key(key):
        return "[REDACTED_DYNAMIC_PLACEHOLDER]"
    return None


def redact_json_string_pair(match: re.Match[str]) -> str:
    replacement = redact_error_key_value(match.group("key"), match.group("value"))
    if replacement is None:
        return match.group(0)
    return f'{match.group(1)}"{replacement}"'


def is_sensitive_error_key(key: str) -> bool:
    return SECRET_LIKE_KEY_RE.search(key) is not None or should_redact_context_key(key)


def redacted_error_value_for_key(key: str) -> str:
    if SECRET_LIKE_KEY_RE.search(key):
        return "[REDACTED]"
    return "[REDACTED_DYNAMIC_PLACEHOLDER]"


def find_error_value_end(text: str, start: int, next_boundary: int | None) -> int:
    limit = next_boundary if next_boundary is not None else len(text)
    delimiter_positions = [
        position
        for position in (text.find(delimiter, start, limit) for delimiter in (",", ";", "}", "]", "\n", "\r"))
        if position != -1
    ]
    if delimiter_positions:
        return min(delimiter_positions)
    return limit


def redact_bounded_error_fields(text: str) -> str:
    matches = list(ERROR_FIELD_BOUNDARY_RE.finditer(text))
    if not matches:
        return text
    chunks: list[str] = []
    cursor = 0
    for index, match in enumerate(matches):
        key = match.group("key")
        next_boundary = matches[index + 1].start() if index + 1 < len(matches) else None
        value_start = match.end()
        value_end = find_error_value_end(text, value_start, next_boundary)
        if not is_sensitive_error_key(key):
            continue
        value_segment = text[value_start:value_end]
        trailing_match = re.search(r"\s*$", value_segment)
        trailing = trailing_match.group(0) if trailing_match else ""
        chunks.append(text[cursor:value_start])
        chunks.append(redacted_error_value_for_key(key))
        chunks.append(trailing)
        cursor = value_end
    if cursor == 0:
        return text
    chunks.append(text[cursor:])
    return "".join(chunks)


def safe_evidence_error_message(exc: BaseException) -> str:
    text = str(exc)
    text = JSON_STRING_PAIR_RE.sub(redact_json_string_pair, text)
    text = redact_bounded_error_fields(text)
    text = BEARER_RE.sub("Bearer [REDACTED]", text)
    text = guards.sanitize(text)
    return str(text)[:1600]


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def current_source_evidence_commit() -> str:
    completed = git(["rev-parse", "HEAD"])
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "could not resolve git HEAD")
    commit = completed.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise RuntimeError(f"git HEAD is not a full 40-character commit: {commit!r}")
    return commit


def source_provenance_fields() -> dict[str, str]:
    return {
        "source_evidence_commit": current_source_evidence_commit(),
        "source_evidence_origin": SOURCE_EVIDENCE_ORIGIN,
    }


def repo_source_paths(target_kb_doc_names: tuple[str, ...]) -> list[str]:
    return [
        str(PROMPT_PATH.relative_to(ROOT)).replace("\\", "/"),
        *[
            str((KB_ROOT / name).relative_to(ROOT)).replace("\\", "/")
            for name in target_kb_doc_names
        ],
    ]


def assert_repo_sources_match_head(target_kb_doc_names: tuple[str, ...]) -> None:
    paths = repo_source_paths(target_kb_doc_names)
    completed = git(["diff", "--quiet", "HEAD", "--", *paths])
    if completed.returncode != 0:
        raise RuntimeError(f"repo source files differ from HEAD; refusing provider evidence for {paths}")


def source_file_evidence(source_path: Path, *, evidence_origin: str = SOURCE_EVIDENCE_ORIGIN) -> dict[str, Any]:
    source_text = source_path.read_text(encoding="utf-8")
    markers = KB_REQUEST_SOURCE_MARKERS[source_path.name]
    missing = [marker for marker in markers if marker not in source_text]
    if missing:
        raise ValueError(f"source evidence markers missing from {source_path.name}: {missing}")
    source_bytes = source_path.read_bytes()
    return {
        "evidence_origin": evidence_origin,
        "source_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_byte_length": len(source_bytes),
        "markers": list(markers),
    }


def request_source_evidence_by_id(requests: list[dict[str, Any]]) -> dict[str, Any]:
    evidence: dict[str, Any] = {}
    for request in requests:
        request_id = str(request.get("request_id", ""))
        if "source_evidence" in request:
            evidence[request_id] = request["source_evidence"]
        elif "body_canonical_json_sha256" in request:
            evidence[request_id] = {
                "evidence_origin": "sanitized_request_body_before_provider_write_not_network_capture",
                "body_canonical_json_sha256": request["body_canonical_json_sha256"],
            }
    return evidence


def target_kb_doc_arg(value: str) -> str:
    name = value.strip()
    if not name:
        raise argparse.ArgumentTypeError("--target-kb-doc cannot be empty")
    return name


def parse_target_kb_docs(values: list[str] | None) -> tuple[str, ...]:
    if values is None:
        return tuple(KB_DOCS)
    cleaned = [value.strip() for value in values]
    if not cleaned or any(not value for value in cleaned):
        raise ValueError("target KB doc list cannot be empty")
    unknown = [value for value in cleaned if value not in KNOWN_KB_DOC_IDS]
    if unknown:
        raise ValueError(f"unknown target KB doc names: {unknown}; allowed={list(KB_DOCS)}")
    duplicates = sorted({value for value in cleaned if cleaned.count(value) > 1})
    if duplicates:
        raise ValueError(f"duplicate target KB doc names: {duplicates}")
    return tuple(cleaned)


def planned_write_counts(requests: list[dict[str, Any]]) -> dict[str, int]:
    kb_count = sum(1 for request in requests if str(request.get("request_id", "")).startswith("update_kb_file::"))
    agent_count = sum(1 for request in requests if request.get("request_id") == "patch_agent::prompt_dynamic_variables")
    return {
        "planned_provider_write_count": len(requests),
        "planned_kb_write_count": kb_count,
        "planned_agent_patch_count": agent_count,
    }


def plan_payload(
    *,
    preflight: dict[str, Any],
    requests: list[dict[str, Any]],
    target_kb_doc_names: tuple[str, ...],
    provider_writes_allowed: bool,
    ledger_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    ledger = ledger_summary or {
        "provider_writes_made": False,
        "provider_write_attempt_count": 0,
        "provider_write_success_count": 0,
        "provider_write_attempts": [],
        "provider_write_successes": [],
    }
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "status": "planned",
        **source_provenance_fields(),
        "authorization_confirmed": provider_writes_allowed,
        "provider_writes_allowed": provider_writes_allowed,
        **ledger,
        **planned_write_counts(requests),
        "target_llm_preserved": TARGET_LLM,
        "target_price_variables": TARGET_PRICE_VARIABLES,
        "kb_documents_planned_for_in_place_update": list(target_kb_doc_names),
        "known_kb_document_ids": {name: KNOWN_KB_DOC_IDS[name] for name in target_kb_doc_names},
        "minimal_agent_patch_fields": ["conversation_config.agent.prompt.prompt", "conversation_config.agent.dynamic_variables"],
        "request_source_evidence_by_id": request_source_evidence_by_id(requests),
        "forbidden_operations": [
            "simulations",
            "outbound_calls",
            "new_knowledge_base_docs",
            "knowledge_base_reorder",
            "Analysis_updates",
            "Procedures_updates",
            "voice_updates",
            "LLM_updates",
            "first_message_updates",
            "phone_updates",
            "tool_updates",
            "MCP_updates",
            "unrelated_dynamic_variable_replacement",
        ],
        "preflight": sanitize(preflight),
    }


def empty_ledger_summary() -> dict[str, Any]:
    return {
        "provider_writes_made": False,
        "provider_write_attempt_count": 0,
        "provider_write_success_count": 0,
        "provider_write_attempts": [],
        "provider_write_successes": [],
    }


def patch_requests_payload(
    *,
    requests: list[dict[str, Any]],
    provider_writes_allowed: bool,
    ledger_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    ledger = ledger_summary or empty_ledger_summary()
    return {
        "checkpoint_id": CHECKPOINT_ID,
        **source_provenance_fields(),
        "provider_writes_allowed": provider_writes_allowed,
        **ledger,
        **planned_write_counts(requests),
        "requests": requests,
    }


def patch_result_payload(
    *,
    status: str,
    provider_writes_allowed: bool,
    requests: list[dict[str, Any]],
    ledger_summary: dict[str, Any] | None,
    error: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        **source_provenance_fields(),
        "status": status,
        "provider_writes_allowed": provider_writes_allowed,
        **(ledger_summary or empty_ledger_summary()),
        **planned_write_counts(requests),
        "simulations_run": False,
        "outbound_calls_made": False,
    }
    if error is not None:
        payload["error"] = error
    if status == "plan_only_missing_confirmation":
        payload["required_confirmation"] = CONFIRM_TOKEN
    return payload


def merged_dynamic_variables(agent: dict[str, Any]) -> dict[str, Any]:
    conversation_config = agent.get("conversation_config")
    if not isinstance(conversation_config, dict):
        raise ValueError("agent conversation_config must be an object")
    agent_config = conversation_config.get("agent")
    if not isinstance(agent_config, dict):
        raise ValueError("agent conversation_config.agent must be an object")
    dynamic = copy.deepcopy(agent_config.get("dynamic_variables") or {})
    if not isinstance(dynamic, dict):
        raise ValueError("agent dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("agent dynamic_variable_placeholders must be an object")
    placeholders.update(TARGET_PRICE_VARIABLES)
    dynamic["dynamic_variable_placeholders"] = placeholders
    return dynamic


def patch_body(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "conversation_config": {
            "agent": {
                "prompt": {"prompt": PROMPT_PATH.read_text(encoding="utf-8").strip()},
                "dynamic_variables": merged_dynamic_variables(agent),
            }
        }
    }


def collateral_state(agent: dict[str, Any]) -> dict[str, Any]:
    state = guards.protected_agent_state(copy.deepcopy(agent))
    agent_config = state["conversation_config"]["agent"]
    prompt = agent_config["prompt"]
    prompt.pop("prompt", None)
    dynamic = agent_config.get("dynamic_variables")
    if not isinstance(dynamic, dict):
        raise ValueError("protected dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("protected dynamic_variable_placeholders must be an object")
    for key in TARGET_PRICE_VARIABLES:
        placeholders.pop(key, None)
    return state


def kb_entries_by_name(agent: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = guards.kb_entries(agent)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        name = str(entry.get("name", "")).strip()
        grouped.setdefault(name, []).append(entry)
    duplicates = sorted(name for name, values in grouped.items() if len(values) > 1)
    if duplicates:
        raise ValueError(f"duplicate attached KB docs: {duplicates}")
    return {name: values[0] for name, values in grouped.items()}


def validate_target_llm(agent: dict[str, Any]) -> None:
    prompt = get_prompt(agent)
    actual = {
        "llm": prompt.get("llm"),
        "temperature": prompt.get("temperature"),
        "thinking_budget": prompt.get("thinking_budget"),
        "reasoning_effort": prompt.get("reasoning_effort"),
    }
    if actual != TARGET_LLM:
        raise ValueError(f"target LLM settings mismatch: expected {TARGET_LLM!r}, got {actual!r}")


def validate_preflight(agent: dict[str, Any], target_kb_doc_names: tuple[str, ...] | None = None) -> dict[str, Any]:
    target_names = parse_target_kb_docs(list(target_kb_doc_names) if target_kb_doc_names is not None else None)
    if agent.get("agent_id") != AGENT_ID or agent.get("name") != AGENT_NAME:
        raise ValueError("refusing unexpected ElevenLabs agent")
    prompt = get_prompt(agent)
    prompt_text = str(prompt.get("prompt", ""))
    if "Atlas Web Studio" not in prompt_text or "Mission: earn permission" not in prompt_text:
        raise ValueError("target prompt is missing required Atlas markers")
    validate_target_llm(agent)

    expected_kb_order = [path.name for path in active_kb_paths()]
    entries = guards.kb_entries(agent)
    names_in_order = [str(item.get("name", "")).strip() for item in entries]
    ids_in_order = guards.attachment_ids(entries)
    if names_in_order != expected_kb_order:
        raise ValueError(f"knowledge-base name/order mismatch: expected {expected_kb_order}, got {names_in_order}")
    if len(ids_in_order) != 17 or len(set(ids_in_order)) != 17:
        raise ValueError("live agent must have 17 unique KB attachment IDs")

    by_name = kb_entries_by_name(agent)
    target_docs: dict[str, dict[str, str]] = {}
    for name in target_names:
        entry = by_name.get(name)
        if not entry:
            raise ValueError(f"live agent missing target KB doc {name}")
        live_id = str(entry.get("id", "")).strip()
        expected_id = KNOWN_KB_DOC_IDS[name]
        if live_id != expected_id:
            raise ValueError(f"target KB doc {name} ID mismatch: expected {expected_id}, got {live_id}")
        source_path = KB_ROOT / name
        if not source_path.is_file():
            raise FileNotFoundError(str(source_path))
        target_docs[name] = {
            "id": live_id,
            "source_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        }

    tools = summarize_tools(agent)
    if tools.get("built_in_end_call_count") != 1:
        raise ValueError("live agent must have exactly one built-in end_call")
    if tools.get("duplicate_custom_or_server_end_call_count") != 0:
        raise ValueError("live agent has custom/server end_call duplicates")
    if not guards.procedures_inactive(agent):
        raise ValueError("live agent Procedures must be inactive")
    criteria = guards.analysis_criteria(agent)
    if len(criteria) != 30:
        raise ValueError(f"live agent must have 30 Analysis criteria, found {len(criteria)}")
    criteria_ids = [str(item.get("id", "")).strip() for item in criteria]
    if any(not item for item in criteria_ids) or len(set(criteria_ids)) != len(criteria_ids):
        raise ValueError("Analysis criterion IDs must be present and unique")

    dynamic = merged_dynamic_variables(agent)
    protected = {
        "knowledge_base_ids_in_order": ids_in_order,
        "unrelated_tool_fingerprint": sanitize(unrelated_tool_fingerprint(agent)),
        "analysis_criterion_ids_in_order": criteria_ids,
        "procedures_inactive": guards.procedures_inactive(agent),
        "collateral_state_sha256": canonical_sha256(collateral_state(agent)),
    }
    return {
        **protected,
        "knowledge_base_names_in_order": names_in_order,
        "target_kb_docs": target_docs,
        "tool_summary": sanitize(tools),
        "llm": TARGET_LLM,
        "dynamic_variable_placeholders_after_patch": sanitize(dynamic.get("dynamic_variable_placeholders", {})),
    }


def protected_fingerprint(agent: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {
        "knowledge_base_ids_in_order": preflight["knowledge_base_ids_in_order"],
        "unrelated_tool_fingerprint": preflight["unrelated_tool_fingerprint"],
        "analysis_criterion_ids_in_order": preflight["analysis_criterion_ids_in_order"],
        "procedures_inactive": preflight["procedures_inactive"],
        "collateral_state_sha256": canonical_sha256(collateral_state(agent)),
    }


def assert_fingerprint_matches(label: str, expected: dict[str, Any], actual: dict[str, Any]) -> None:
    if actual != expected:
        raise ValueError(f"{label} protected fingerprint mismatch: expected={sanitize(expected)!r}, actual={sanitize(actual)!r}")


class ProviderWriteLedger:
    def __init__(self) -> None:
        self.attempts: list[dict[str, Any]] = []
        self.successes: list[dict[str, Any]] = []

    def record_attempt(self, request: dict[str, Any]) -> None:
        self.attempts.append(
            {
                "request_id": request.get("request_id"),
                "method": request.get("method"),
                "endpoint": request.get("endpoint"),
                "attempted_at_utc": utc_now(),
            }
        )

    def record_success(self, request: dict[str, Any], response: dict[str, Any]) -> None:
        self.successes.append(
            {
                "request_id": request.get("request_id"),
                "status_code": response.get("status_code"),
                "response": sanitize(response.get("response")),
                "confirmed_at_utc": utc_now(),
            }
        )

    def summary(self) -> dict[str, Any]:
        return {
            "provider_writes_made": bool(self.attempts),
            "provider_write_attempt_count": len(self.attempts),
            "provider_write_success_count": len(self.successes),
            "provider_write_attempts": sanitize(self.attempts),
            "provider_write_successes": sanitize(self.successes),
        }

    def failure_payload(self, *, checkpoint_id: str, error: str) -> dict[str, Any]:
        return {
            "checkpoint_id": checkpoint_id,
            "status": "failed",
            **self.summary(),
            "error": error,
            "simulations_run": False,
            "outbound_calls_made": False,
        }


def attempt_provider_write(ledger: ProviderWriteLedger, request: dict[str, Any], operation: Any) -> dict[str, Any]:
    ledger.record_attempt(request)
    response = operation()
    ledger.record_success(request, response)
    return response


def patch_requests(agent: dict[str, Any], preflight: dict[str, Any], target_kb_doc_names: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
    target_names = parse_target_kb_docs(list(target_kb_doc_names) if target_kb_doc_names is not None else None)
    requests: list[dict[str, Any]] = []
    for name in target_names:
        doc = preflight["target_kb_docs"][name]
        source_path = KB_ROOT / name
        requests.append(
            {
                "request_id": f"update_kb_file::{name}",
                "method": "PATCH",
                "endpoint": f"/v1/convai/knowledge-base/{doc['id']}/update-file",
                "known_document_id": doc["id"],
                "content_type": "multipart/form-data",
                "source_path": doc["source_path"],
                "source_evidence": source_file_evidence(source_path),
            }
        )
    sanitized_body = sanitize(patch_body(agent))
    requests.append(
        {
            "request_id": "patch_agent::prompt_dynamic_variables",
            "method": "PATCH",
            "endpoint": f"/v1/convai/agents/{AGENT_ID}",
            "content_type": "application/json",
            "body": sanitized_body,
            "body_canonical_json_sha256": canonical_sha256(sanitized_body),
        }
    )
    return requests


def snapshot_payload(
    *,
    phase: str,
    agent: dict[str, Any] | None,
    preflight: dict[str, Any] | None,
    live_readback_at_utc: str | None = None,
    serialized_at_utc: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    serialized_at = serialized_at_utc or utc_now()
    payload: dict[str, Any] = {
        "checkpoint_id": CHECKPOINT_ID,
        "phase": phase,
        "captured_at_utc": live_readback_at_utc,
        "live_readback_at_utc": live_readback_at_utc,
        "live_readback_time_recorded": live_readback_at_utc is not None,
        "snapshot_serialized_at_utc": serialized_at,
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "simulations_run": False,
        "outbound_calls_made": False,
    }
    if agent is not None:
        payload["agent"] = sanitize(agent)
    if preflight is not None:
        payload["protected_fingerprint"] = sanitize(protected_fingerprint(agent or {}, preflight)) if agent else sanitize(preflight)
        payload["preflight"] = sanitize(preflight)
    if error is not None:
        payload["error"] = error
    return payload


def dynamic_variables_readback(agent: dict[str, Any]) -> dict[str, Any]:
    conversation_config = agent.get("conversation_config")
    if not isinstance(conversation_config, dict):
        raise ValueError("agent conversation_config must be an object")
    agent_config = conversation_config.get("agent")
    if not isinstance(agent_config, dict):
        raise ValueError("agent conversation_config.agent must be an object")
    dynamic = agent_config.get("dynamic_variables")
    if not isinstance(dynamic, dict):
        raise ValueError("agent dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("agent dynamic_variable_placeholders must be an object")
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "captured_at_utc": utc_now(),
        "agent_id": AGENT_ID,
        "dynamic_variables": sanitize(dynamic),
        "target_price_values_current": {key: placeholders.get(key) for key in TARGET_PRICE_VARIABLES},
        "target_price_values_planned": TARGET_PRICE_VARIABLES,
    }


def actual_dynamic_variable_placeholders(agent: dict[str, Any]) -> dict[str, Any]:
    conversation_config = agent.get("conversation_config")
    if not isinstance(conversation_config, dict):
        raise ValueError("agent conversation_config must be an object")
    agent_config = conversation_config.get("agent")
    if not isinstance(agent_config, dict):
        raise ValueError("agent conversation_config.agent must be an object")
    dynamic = agent_config.get("dynamic_variables")
    if not isinstance(dynamic, dict):
        raise ValueError("agent dynamic_variables must be an object")
    placeholders = dynamic.get("dynamic_variable_placeholders")
    if not isinstance(placeholders, dict):
        raise ValueError("agent dynamic_variable_placeholders must be an object")
    return placeholders


def write_plan_only_outputs(
    agent: dict[str, Any],
    preflight: dict[str, Any],
    requests: list[dict[str, Any]],
    status: str,
    *,
    live_readback_at_utc: str,
    target_kb_doc_names: tuple[str, ...],
) -> None:
    fingerprint = protected_fingerprint(agent, preflight)
    write_json(
        OUT_DIR / "live_agent_pre_patch_snapshot.json",
        snapshot_payload(phase="pre_patch", agent=agent, preflight=preflight, live_readback_at_utc=live_readback_at_utc),
    )
    write_json(
        OUT_DIR / "live_agent_patch_plan.json",
        plan_payload(
            preflight=preflight,
            requests=requests,
            target_kb_doc_names=target_kb_doc_names,
            provider_writes_allowed=False,
            ledger_summary=None,
        ),
    )
    write_json(
        OUT_DIR / "live_agent_patch_requests.json",
        patch_requests_payload(
            requests=requests,
            provider_writes_allowed=False,
            ledger_summary=None,
        ),
    )
    write_json(
        OUT_DIR / "live_agent_patch_result.json",
        patch_result_payload(
            status=status,
            provider_writes_allowed=False,
            requests=requests,
            ledger_summary=None,
        ),
    )
    write_json(
        OUT_DIR / "live_agent_post_patch_snapshot.json",
        snapshot_payload(phase="not_written", agent=agent, preflight=preflight, live_readback_at_utc=live_readback_at_utc),
    )
    write_json(OUT_DIR / "live_dynamic_variables_readback.json", dynamic_variables_readback(agent))
    write_json(OUT_DIR / "unrelated_tool_fingerprint_before.json", {"checkpoint_id": CHECKPOINT_ID, "fingerprint": fingerprint})
    write_json(OUT_DIR / "unrelated_tool_fingerprint_after.json", {"checkpoint_id": CHECKPOINT_ID, "fingerprint": fingerprint})


def write_provider_changes(
    *,
    api_key: str,
    agent: dict[str, Any],
    preflight: dict[str, Any],
    requests: list[dict[str, Any]],
    ledger: ProviderWriteLedger,
    target_kb_doc_names: tuple[str, ...],
) -> tuple[dict[str, Any], str]:
    expected_before = protected_fingerprint(agent, preflight)
    for request in requests:
        request_id = request["request_id"]
        if request_id.startswith("update_kb_file::"):
            name = request_id.split("::", 1)[1]
            source_path = KB_ROOT / name
            attempt_provider_write(
                ledger,
                request,
                lambda name=name, source_path=source_path: multipart_update_file(
                    api_key=api_key,
                    documentation_id=KNOWN_KB_DOC_IDS[name],
                    source_path=source_path,
                ),
            )
        elif request_id == "patch_agent::prompt_dynamic_variables":
            attempt_provider_write(
                ledger,
                request,
                lambda: json_request(
                    "PATCH",
                    f"/v1/convai/agents/{quote(AGENT_ID, safe='')}",
                    api_key=api_key,
                    body=patch_body(agent),
                ),
            )
        else:
            raise ValueError(f"unknown write request {request_id}")

    post = json_request("GET", f"/v1/convai/agents/{quote(AGENT_ID, safe='')}", api_key=api_key)["response"]
    post_live_readback_at_utc = utc_now()
    if not isinstance(post, dict):
        raise ValueError("post-patch agent GET response must be an object")
    post_preflight = validate_preflight(post, target_kb_doc_names)
    assert_fingerprint_matches("post-patch", expected_before, protected_fingerprint(post, post_preflight))
    if get_prompt(post).get("prompt") != PROMPT_PATH.read_text(encoding="utf-8").strip():
        raise ValueError("post-patch prompt does not exactly match repo prompt")
    placeholders = actual_dynamic_variable_placeholders(post)
    for key, expected in TARGET_PRICE_VARIABLES.items():
        if placeholders.get(key) != expected:
            raise ValueError(f"post-patch dynamic variable {key} mismatch")
    return post, post_live_readback_at_utc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guarded ELEVENLABS-040 Atlas pricing patcher; dry-run by default.")
    parser.add_argument("--confirm-provider-write", default=None, help=f"Exact token required for writes: {CONFIRM_TOKEN}")
    parser.add_argument(
        "--target-kb-doc",
        action="append",
        type=target_kb_doc_arg,
        default=None,
        metavar="NAME",
        help=f"Optional active KB doc name to patch; repeat to target a guarded subset. Default: all {len(KB_DOCS)} active target docs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        target_kb_doc_names = parse_target_kb_docs(args.target_kb_doc)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    try:
        assert_repo_sources_match_head(target_kb_doc_names)
    except RuntimeError as exc:
        print(f"error: {safe_evidence_error_message(exc)}", file=sys.stderr)
        return 2
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        print(f"error: {API_KEY_ENV_VAR} is required for fresh live GET preflight", file=sys.stderr)
        return 2

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ledger = ProviderWriteLedger()
    before_agent: dict[str, Any] | None = None
    before_preflight: dict[str, Any] | None = None
    before_live_readback_at_utc: str | None = None
    try:
        if not PROMPT_PATH.read_text(encoding="utf-8").strip():
            raise ValueError("repo prompt is empty")
        before_agent = json_request("GET", f"/v1/convai/agents/{quote(AGENT_ID, safe='')}", api_key=api_key)["response"]
        before_live_readback_at_utc = utc_now()
        if not isinstance(before_agent, dict):
            raise ValueError("agent GET response must be an object")
        before_preflight = validate_preflight(before_agent, target_kb_doc_names)
        requests = patch_requests(before_agent, before_preflight, target_kb_doc_names=target_kb_doc_names)
        authorization_confirmed = args.confirm_provider_write == CONFIRM_TOKEN
        if not authorization_confirmed:
            write_plan_only_outputs(
                before_agent,
                before_preflight,
                requests,
                "plan_only_missing_confirmation",
                live_readback_at_utc=before_live_readback_at_utc,
                target_kb_doc_names=target_kb_doc_names,
            )
            print(
                json.dumps(
                    {
                        "status": "plan_only_missing_confirmation",
                        "provider_writes_made": False,
                        **planned_write_counts(requests),
                        "plan": str(OUT_DIR / "live_agent_patch_plan.json"),
                    },
                    indent=2,
                )
            )
            return 0

        post_agent, post_live_readback_at_utc = write_provider_changes(
            api_key=api_key,
            agent=before_agent,
            preflight=before_preflight,
            requests=requests,
            ledger=ledger,
            target_kb_doc_names=target_kb_doc_names,
        )
        post_preflight = validate_preflight(post_agent, target_kb_doc_names)
        write_json(
            OUT_DIR / "live_agent_pre_patch_snapshot.json",
            snapshot_payload(phase="pre_patch", agent=before_agent, preflight=before_preflight, live_readback_at_utc=before_live_readback_at_utc),
        )
        write_json(
            OUT_DIR / "live_agent_patch_plan.json",
            plan_payload(
                preflight=before_preflight,
                requests=requests,
                target_kb_doc_names=target_kb_doc_names,
                provider_writes_allowed=True,
                ledger_summary=ledger.summary(),
            ),
        )
        write_json(
            OUT_DIR / "live_agent_patch_requests.json",
            patch_requests_payload(
                requests=requests,
                provider_writes_allowed=True,
                ledger_summary=ledger.summary(),
            ),
        )
        write_json(
            OUT_DIR / "live_agent_post_patch_snapshot.json",
            snapshot_payload(phase="post_patch", agent=post_agent, preflight=post_preflight, live_readback_at_utc=post_live_readback_at_utc),
        )
        write_json(OUT_DIR / "live_dynamic_variables_readback.json", dynamic_variables_readback(post_agent))
        write_json(OUT_DIR / "unrelated_tool_fingerprint_before.json", {"checkpoint_id": CHECKPOINT_ID, "fingerprint": protected_fingerprint(before_agent, before_preflight)})
        write_json(OUT_DIR / "unrelated_tool_fingerprint_after.json", {"checkpoint_id": CHECKPOINT_ID, "fingerprint": protected_fingerprint(post_agent, post_preflight)})
        write_json(
            OUT_DIR / "live_agent_patch_result.json",
            patch_result_payload(
                status="passed",
                provider_writes_allowed=True,
                requests=requests,
                ledger_summary=ledger.summary(),
            ),
        )
        print(json.dumps({"status": "passed", "provider_writes_made": True}, indent=2))
        return 0
    except Exception as exc:
        error = safe_evidence_error_message(exc)
        write_json(
            OUT_DIR / "live_agent_patch_result.json",
            patch_result_payload(
                status="failed",
                provider_writes_allowed=args.confirm_provider_write == CONFIRM_TOKEN,
                requests=requests if "requests" in locals() else [],
                ledger_summary=ledger.summary(),
                error=error,
            ),
        )
        write_json(
            OUT_DIR / "live_agent_post_patch_snapshot.json",
            snapshot_payload(phase="failed", agent=before_agent, preflight=before_preflight, live_readback_at_utc=before_live_readback_at_utc, error=error),
        )
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
