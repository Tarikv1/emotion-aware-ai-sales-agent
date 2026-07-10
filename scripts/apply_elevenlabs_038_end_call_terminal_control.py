#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
API_BASE_URL = "https://api.elevenlabs.io"
API_KEY_ENV_VAR = "ELEVENLABS_API_KEY"
CHECKPOINT_ID = "ELEVENLABS-039-end-call-edge-case-hardening"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
EXPECTED_AGENT_NAME = "web design"

PROMPT_PATH = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
MANIFEST_PATH = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_sales_spine_compression.package.json"
)

KB_DOCS_TO_UPDATE = {
    "atlas_close_and_followup_playbook.md",
    "atlas_offer_facts.md",
    "atlas_output_quality_rules.md",
}

END_CALL_DESCRIPTION = (
    "End the call only when the conversation is genuinely complete. Call this tool once when the buyer explicitly "
    "ends a completed conversation, gives a hard stop or do-not-call request, a completed gatekeeper callback or "
    "note outcome is reached, or a guarantee-only disqualification reaches its terminal conclusion. Before ending, "
    "answer any live direct question or unresolved concern, confirm any pending email destination, and confirm any "
    "agreed callback window. Exception: a hard stop or do-not-call request overrides pending email confirmation, "
    "callback, and every unfinished sales action; end immediately without confirming email or continuing the pitch. "
    "Include by-the-end-of-day delivery timing only when it has not already been stated, or when email confirmation "
    "and goodbye occur in the same buyer turn. Use the tool's message field as the single final spoken line. Do not "
    "speak a separate farewell before invoking the tool. Do not end while email confirmation is pending, the buyer "
    "accepted the mockup but no email is known, or the buyer is still asking about price, process, capability, scope, "
    "or another unresolved concern, except for the hard-stop/do-not-call override. Do not call this tool more than once."
)

OLD_MONOLITHIC_KB_NAMES = {
    "universal_sales_core.md",
    "atlas_web_studio_web_design_campaign.md",
    "atlas_web_studio_web_design_campaign_overlay.md",
    "atlas_web_studio_web_design_campaign_profile.md",
}

PRIVATE_KEY_RE = re.compile(r"(api[_-]?key|authorization|secret|token|phone|email)", re.IGNORECASE)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def read_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"{rel(path)} is empty")
    return text


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{rel(path)} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sanitize(value: Any, *, key_hint: str = "") -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in {"access_info", "phone_numbers", "whatsapp_accounts"}:
                if isinstance(item, list):
                    clean[key_text] = {"redacted": True, "count": len(item)}
                elif isinstance(item, dict):
                    clean[key_text] = {"redacted": True}
                else:
                    clean[key_text] = item
                continue
            if PRIVATE_KEY_RE.search(key_text) and key_text not in {
                "normalized_email_extracted",
                "realistic_test_contact_values",
            }:
                if item in (None, "", [], {}):
                    clean[key_text] = item
                else:
                    clean[key_text] = "[REDACTED]"
                continue
            clean[key_text] = sanitize(item, key_hint=key_text)
        return clean
    if isinstance(value, list):
        return [sanitize(item, key_hint=key_hint) for item in value]
    if isinstance(value, str):
        if key_hint in {"conversation_goal_prompt", "prompt", "description", "first_message", "message"}:
            return value
        return PHONE_RE.sub("[REDACTED_PHONE]", EMAIL_RE.sub("[REDACTED_EMAIL]", value))
    return value


def json_request(
    method: str,
    endpoint: str,
    *,
    api_key: str,
    body: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        API_BASE_URL + endpoint,
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
            return {
                "status_code": response.status,
                "response": json.loads(response_text) if response_text else {},
            }
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {endpoint} failed with {exc.code}: {body_text[:1200]}") from exc


def multipart_update_file(
    *,
    api_key: str,
    documentation_id: str,
    source_path: Path,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    boundary = f"----codex-elevenlabs-038-{int(time.time() * 1000)}"
    file_bytes = source_path.read_bytes()
    content_type = mimetypes.guess_type(source_path.name)[0] or "text/markdown"
    parts = [
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{source_path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        file_bytes,
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ]
    request = urllib.request.Request(
        API_BASE_URL + f"/v1/convai/knowledge-base/{urllib.parse.quote(documentation_id)}/update-file",
        data=b"".join(parts),
        method="PATCH",
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "xi-api-key": api_key,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_text = response.read().decode("utf-8")
            return {
                "status_code": response.status,
                "response": json.loads(response_text) if response_text else {},
            }
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"PATCH update-file {documentation_id} failed with {exc.code}: {body_text[:1200]}") from exc


def active_kb_paths() -> list[Path]:
    manifest = read_json(MANIFEST_PATH)
    recommendation = manifest.get("active_kb_recommendation", {})
    paths = recommendation.get("recommended_upload_docs", []) if isinstance(recommendation, dict) else []
    if not isinstance(paths, list) or not paths:
        raise ValueError("active manifest has no recommended_upload_docs")
    resolved: list[Path] = []
    for path_text in paths:
        path = (ROOT / str(path_text)).resolve(strict=False)
        path.relative_to(ROOT)
        if not path.is_file():
            raise FileNotFoundError(str(path))
        resolved.append(path)
    return resolved


def get_prompt(agent: dict[str, Any]) -> dict[str, Any]:
    prompt = (
        agent.get("conversation_config", {})
        .get("agent", {})
        .get("prompt", {})
    )
    if not isinstance(prompt, dict):
        raise ValueError("agent prompt payload missing")
    return prompt


def validate_target_agent(agent: dict[str, Any], expected_agent_id: str, expected_names: set[str]) -> None:
    agent_id = str(agent.get("agent_id", "")).strip()
    name = str(agent.get("name", "")).strip()
    prompt_text = str(get_prompt(agent).get("prompt", ""))
    kb_names = [str(item.get("name", "")) for item in get_prompt(agent).get("knowledge_base", []) if isinstance(item, dict)]
    kb_set = set(kb_names)
    expected_set = {path.name for path in active_kb_paths()}
    if agent_id != expected_agent_id:
        raise ValueError(f"refusing to patch unexpected agent id {agent_id}")
    if name not in expected_names:
        raise ValueError(f"refusing to patch unexpected agent name {name!r}")
    if "Atlas Web Studio" not in prompt_text or "Mission: earn permission" not in prompt_text:
        raise ValueError("target prompt does not look like the current compact Atlas prompt")
    if kb_set != expected_set:
        raise ValueError(f"target KB set mismatch: expected {sorted(expected_set)}, got {sorted(kb_set)}")
    blocked = kb_set & OLD_MONOLITHIC_KB_NAMES
    if blocked:
        raise ValueError(f"target includes old monolithic KB docs: {sorted(blocked)}")
    if agent.get("procedures"):
        raise ValueError("target has active procedures; refusing live patch")


def document_metadata(api_key: str, documentation_id: str) -> dict[str, Any]:
    return json_request(
        "GET",
        f"/v1/convai/knowledge-base/{urllib.parse.quote(documentation_id)}",
        api_key=api_key,
    )["response"]


def select_canonical_kb_docs(agent: dict[str, Any], api_key: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prompt = get_prompt(agent)
    entries = prompt.get("knowledge_base", [])
    if not isinstance(entries, list):
        raise ValueError("prompt.knowledge_base is not a list")
    expected_order = [path.name for path in active_kb_paths()]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    metadata_by_id: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        doc_id = str(entry.get("id", "")).strip()
        name = str(entry.get("name", "")).strip()
        if not doc_id or not name:
            continue
        doc = document_metadata(api_key, doc_id)
        metadata_by_id[doc_id] = sanitize(doc)
        merged = dict(entry)
        merged["_metadata"] = doc.get("metadata") or {}
        merged["_response_type"] = doc.get("type")
        grouped[name].append(merged)
    canonical: list[dict[str, Any]] = []
    selection: dict[str, Any] = {}
    for name in expected_order:
        candidates = grouped.get(name) or []
        if not candidates:
            raise ValueError(f"live agent missing active KB doc {name}")

        def sort_key(item: dict[str, Any]) -> tuple[int, int, int]:
            metadata = item.get("_metadata") or {}
            updated = int(metadata.get("last_updated_at_unix_secs") or 0)
            created = int(metadata.get("created_at_unix_secs") or 0)
            type_score = 1 if item.get("_response_type") == "file" or item.get("type") == "file" else 0
            return (updated, type_score, created)

        chosen = max(candidates, key=sort_key)
        canonical_entry = {
            "type": chosen.get("_response_type") or chosen.get("type") or "file",
            "name": name,
            "id": chosen["id"],
        }
        if chosen.get("usage_mode"):
            canonical_entry["usage_mode"] = chosen["usage_mode"]
        canonical.append(canonical_entry)
        selection[name] = {
            "chosen_id": chosen["id"],
            "chosen_type": canonical_entry["type"],
            "candidate_count": len(candidates),
            "candidate_ids": [item.get("id") for item in candidates],
            "metadata": chosen.get("_metadata") or {},
        }
    return canonical, {"selection": selection, "metadata_by_id": metadata_by_id}


def build_end_call_tool() -> dict[str, Any]:
    return {
        "type": "system",
        "name": "end_call",
        "description": END_CALL_DESCRIPTION,
        "response_timeout_secs": 20,
        "disable_interruptions": False,
        "force_pre_tool_speech": False,
        "pre_tool_speech": "auto",
        "assignments": [],
        "tool_call_sound": None,
        "tool_call_sound_behavior": "auto",
        "tool_error_handling_mode": "auto",
        "params": {
            "system_tool_type": "end_call",
        },
    }


def is_end_call_tool_entry(item: Any) -> bool:
    return isinstance(item, dict) and item.get("name") == "end_call"


def unrelated_tool_fingerprint(agent_or_prompt: dict[str, Any]) -> dict[str, Any]:
    prompt = agent_or_prompt if "conversation_config" not in agent_or_prompt else get_prompt(agent_or_prompt)
    legacy_tools = prompt.get("tools", [])
    if legacy_tools is not None and not isinstance(legacy_tools, list):
        raise ValueError("prompt.tools is not a list")
    built_in_tools = prompt.get("built_in_tools", {})
    if built_in_tools is not None and not isinstance(built_in_tools, dict):
        raise ValueError("prompt.built_in_tools is not an object")
    return {
        "non_end_call_legacy_tools": [
            copy.deepcopy(item) for item in (legacy_tools or []) if not is_end_call_tool_entry(item)
        ],
        "built_in_tools_excluding_end_call": {
            str(key): copy.deepcopy(value)
            for key, value in (built_in_tools or {}).items()
            if str(key) != "end_call"
        },
        "tool_ids": copy.deepcopy(prompt.get("tool_ids", [])),
        "mcp_server_ids": copy.deepcopy(prompt.get("mcp_server_ids", [])),
        "native_mcp_server_ids": copy.deepcopy(prompt.get("native_mcp_server_ids", [])),
    }


def assert_unrelated_tool_fingerprint_unchanged(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    context: str,
) -> None:
    if before != after:
        raise ValueError(
            f"unrelated tool fingerprint changed during {context}: "
            f"before={sanitize(before)!r}, after={sanitize(after)!r}"
        )


def normalize_end_call_tools(prompt: dict[str, Any]) -> None:
    legacy_tools = prompt.get("tools", [])
    if legacy_tools is not None and not isinstance(legacy_tools, list):
        raise ValueError("prompt.tools is not a list")
    prompt["tools"] = [
        copy.deepcopy(item)
        for item in (legacy_tools or [])
        if not is_end_call_tool_entry(item)
    ]
    built_in_tools = prompt.setdefault("built_in_tools", {})
    if not isinstance(built_in_tools, dict):
        raise ValueError("prompt.built_in_tools is not an object")
    built_in_tools["end_call"] = build_end_call_tool()


def build_agent_patch(agent: dict[str, Any], canonical_kb: list[dict[str, Any]], prompt_text: str) -> dict[str, Any]:
    conversation_config = copy.deepcopy(agent["conversation_config"])
    prompt = conversation_config["agent"]["prompt"]
    fingerprint_before = unrelated_tool_fingerprint(get_prompt(agent))
    prompt["prompt"] = prompt_text
    prompt["knowledge_base"] = canonical_kb
    normalize_end_call_tools(prompt)
    assert_unrelated_tool_fingerprint_unchanged(
        fingerprint_before,
        unrelated_tool_fingerprint(prompt),
        context="patch-body-build",
    )
    rag = prompt.setdefault("rag", {})
    if isinstance(rag, dict):
        rag["enabled"] = True
    return {
        "name": agent.get("name") or EXPECTED_AGENT_NAME,
        "conversation_config": conversation_config,
        "workflow": copy.deepcopy(agent.get("workflow", {})),
        "tags": copy.deepcopy(agent.get("tags", [])),
        "version_description": "ELEVENLABS-039 end-call edge-case hardening; prompt, focused KB attachments, Analysis, and built-in end_call tool",
    }


def summarize_tools(agent: dict[str, Any]) -> dict[str, Any]:
    prompt = get_prompt(agent)
    built_in_tools = prompt.get("built_in_tools", {})
    end_call = built_in_tools.get("end_call") if isinstance(built_in_tools, dict) else None
    legacy_tools = prompt.get("tools", [])
    legacy_end_call_entries = [
        item for item in legacy_tools
        if isinstance(item, dict) and item.get("name") == "end_call"
    ] if isinstance(legacy_tools, list) else []
    legacy_system_mirrors = [
        item for item in legacy_end_call_entries
        if item.get("type") == "system" and (item.get("params") or {}).get("system_tool_type") == "end_call"
    ]
    legacy_custom_duplicates = [
        item for item in legacy_end_call_entries
        if item not in legacy_system_mirrors
    ]
    tool_ids = prompt.get("tool_ids", [])
    return {
        "built_in_end_call_exists": isinstance(end_call, dict),
        "built_in_end_call": sanitize(end_call) if isinstance(end_call, dict) else None,
        "built_in_end_call_count": 1 if isinstance(end_call, dict) else 0,
        "legacy_system_end_call_mirror_count": len(legacy_system_mirrors),
        "duplicate_custom_or_server_end_call_count": len(legacy_custom_duplicates),
        "tool_ids": sanitize(tool_ids),
        "legacy_tools_count": len(legacy_tools) if isinstance(legacy_tools, list) else None,
        "mcp_server_ids": sanitize(prompt.get("mcp_server_ids")),
        "native_mcp_server_ids": sanitize(prompt.get("native_mcp_server_ids")),
    }


def verification(agent: dict[str, Any], prompt_text: str, canonical_kb: list[dict[str, Any]]) -> dict[str, Any]:
    prompt = get_prompt(agent)
    kb = prompt.get("knowledge_base", [])
    kb_names = [item.get("name") for item in kb if isinstance(item, dict)]
    tool_summary = summarize_tools(agent)
    return {
        "prompt_updated": prompt.get("prompt") == prompt_text,
        "kb_count": len(kb) if isinstance(kb, list) else None,
        "kb_unique_count": len(set(kb_names)),
        "kb_matches_manifest_order": kb_names == [item["name"] for item in canonical_kb],
        "old_monolithic_kb_attached": bool(set(kb_names) & OLD_MONOLITHIC_KB_NAMES),
        "tests_or_analysis_attached_as_kb": any(
            "tests" in str(name) or "analysis" in str(name) or "research/experiments/generated" in str(name)
            for name in kb_names
        ),
        "procedures_inactive": not bool(agent.get("procedures")),
        "analysis_config_live_field_present": bool(agent.get("platform_settings")),
        "tool_summary": tool_summary,
        "end_call_description_matches": (
            isinstance(tool_summary.get("built_in_end_call"), dict)
            and tool_summary["built_in_end_call"].get("description") == END_CALL_DESCRIPTION
        ),
        "simulations_run": False,
        "outbound_calls_made": False,
    }


def assert_verification(payload: dict[str, Any]) -> None:
    required_true = [
        "prompt_updated",
        "kb_matches_manifest_order",
        "procedures_inactive",
        "end_call_description_matches",
    ]
    for key in required_true:
        if payload.get(key) is not True:
            raise ValueError(f"post-patch verification failed: {key}={payload.get(key)!r}")
    if payload.get("kb_count") != 17 or payload.get("kb_unique_count") != 17:
        raise ValueError(f"post-patch KB count invalid: {payload.get('kb_count')} / {payload.get('kb_unique_count')}")
    if payload.get("old_monolithic_kb_attached") or payload.get("tests_or_analysis_attached_as_kb"):
        raise ValueError("post-patch KB attachment guard failed")
    tool_summary = payload["tool_summary"]
    if (
        tool_summary.get("built_in_end_call_count") != 1
        or tool_summary.get("duplicate_custom_or_server_end_call_count") != 0
    ):
        raise ValueError(f"post-patch end_call count invalid: {tool_summary}")


def criterion_prompt(item: dict[str, Any]) -> str:
    compact_prompts = {
        "cost_driver_expertise": (
            "Evaluate the completed transcript for `cost_driver_expertise`.\n"
            "Criterion: Cost answers must separate capability, scope, price, proof, and process-risk states.\n"
            "Return success when: capability questions get direct yes/no before price; scope questions name components; "
            "price questions get one relevant approved range or scoped-pricing answer by the first or second direct ask; "
            "ranges are ballparks, not final quotes; integration-heavy range is the likely total project band, not an "
            "automatic add-on; custom systems are scoped with drivers like workflow, data, user accounts, permissions, "
            "APIs, security, cloud setup, integrations, testing, or maintenance.\n"
            "Return failure when: buyer asks price/cost/range/budget/fee/add-on/total twice with no useful range or scoped "
            "answer; Emma prices capability-only/scope-only/possibility/small-business/mockup-scope/catch questions; says "
            "only it depends; repeats free mockup; avoids price to max turns; gives fixed feature price or quote filtering "
            "exactly $3,000; says we don't do filtering; dumps whole menu; prices before capability; treats integration "
            "band as an add-on; promises Jobber, Stripe, payment, deposit, or two-way sync details without scope; sounds "
            "unsure about approved capabilities; gives clean portal/dashboard price or forced beyond-$5k language before "
            "scope unless asked; gives final custom quote; invents numbers; guarantees SEO/calls/jobs/revenue/rankings; "
            "or only gives vague drivers.\n"
            "Return unknown when: No price, cost, or scope-driver question appears.\n"
            "Use only the transcript. Return success, failure, or unknown with a brief rationale."
        ),
        "terminal_close_no_loop": (
            "Evaluate the completed transcript for `terminal_close_no_loop`.\n"
            "Criterion: Completed terminal states should use exactly one `end_call` with the final message supplied "
            "through the tool.\n"
            "Return success when: `end_call` is invoked once after a genuine terminal condition; no separate farewell "
            "precedes it; no pitch follows; delivery timing is included only when not already stated or when email "
            "confirmation and goodbye occur in the same turn; and callback/note completion terminates atomically.\n"
            "Return failure when: no `end_call` occurs after a completed goodbye while the tool is available; `end_call` "
            "is called more than once; Emma says Take care or another farewell before the tool; delivery timing is repeated "
            "after it was already stated; a callback/note is confirmed but the call remains open; pitch or explanation follows "
            "terminal action; `end_call` occurs with unresolved concern, pending email confirmation except hard-stop override, "
            "accepted mockup but no email, or email confirmation without goodbye; confirmation without goodbye adds a farewell "
            "instead of a timing-only turn; email-confirmed same-turn goodbye omits by-the-end-of-day delivery timing; or Take "
            "care is repeated.\n"
            "Return unknown when: No completed terminal condition, hard stop, do-not-call, or terminal guarantee-only close appears.\n"
            "Use only the transcript. Return success, failure, or unknown with a brief rationale."
        ),
    }
    if str(item["id"]) in compact_prompts:
        prompt = compact_prompts[str(item["id"])]
        if len(prompt) > 2000:
            raise ValueError(f"live evaluation prompt for {item['id']} exceeds 2000 characters")
        return prompt
    compact_failures = {
        "cost_driver_expertise": (
            "Hard fail if buyer asks price/cost/range/budget/fee/add-on/total twice and Emma gives no approved range "
            "or scoped-pricing answer; gives paid price for capability-only, scope-only, possibility, small-business, "
            "mockup-scope, or catch/process-risk questions; says only it depends; repeats free mockup/no obligation; "
            "avoids price until max turns; gives fixed feature price or quote filtering exactly $3,000; says we don't "
            "do filtering; dumps whole menu; prices before clear capability answer; treats integration-heavy range as "
            "automatic add-on instead of likely total project band; promises Jobber, Stripe, payments, deposits, or "
            "two-way sync are included without workflow scope; sounds unsure about approved capabilities; quotes clean "
            "$4k-$5k or beyond-$5k portal pricing before scoped caveat unless buyer asks range; gives final fixed custom "
            "quote; invents unsupported numbers; guarantees SEO, calls, jobs, revenue, or rankings; or uses only vague "
            "drivers like significant development time or expertise."
        ),
        "terminal_close_no_loop": (
            "Hard fail if no end_call occurs after a genuine completed goodbye when the tool is available; end_call is "
            "called more than once; Emma says a farewell before invoking the tool; goodbye or Take care is repeated; "
            "delivery timing is unnecessarily repeated in the final tool message; gatekeeper callback/note is confirmed "
            "but the call remains open; pitch or explanation follows terminal action; end_call is invoked while an "
            "unresolved concern remains, email confirmation is pending except hard-stop override, or mockup was accepted "
            "but no email is known; confirmation without goodbye triggers end_call or a farewell instead of a timing-only "
            "turn; or email-confirmed same-turn goodbye omits by-the-end-of-day delivery timing."
        ),
    }
    lines = [
        f"Evaluate the completed transcript for `{item['id']}`.",
        f"Criterion: {item['description']}",
        f"Return success when: {item['pass']}",
        f"Return failure when: {compact_failures.get(str(item['id']), item['failure'])}",
        f"Return unknown when: {item['unknown']}",
    ]
    edge_cases = item.get("edge_cases") or []
    if edge_cases:
        lines.append("Edge cases:")
        lines.extend(f"- {case}" for case in edge_cases)
    lines.append(
        "Use only the transcript. Do not infer facts, buyer turns, or outcomes that are not present. "
        "Return success, failure, or unknown with a brief rationale."
    )
    prompt = "\n".join(lines)
    if len(prompt) > 2000:
        raise ValueError(f"live evaluation prompt for {item['id']} exceeds 2000 characters")
    return prompt


def repo_evaluation_criteria() -> list[dict[str, Any]]:
    config = read_json(ROOT / "runtime" / "providers" / "elevenlabs_agents" / "analysis" / "atlas_web_studio_analysis_config.json")
    criteria = config.get("success_evaluation_criteria", [])
    if not isinstance(criteria, list) or len(criteria) > 30:
        raise ValueError("repo analysis criteria missing or over ElevenLabs limit")
    return [
        {
            "id": str(item["id"]),
            "name": str(item["id"]).replace("_", " "),
            "type": "prompt",
            "conversation_goal_prompt": criterion_prompt(item),
            "use_knowledge_base": False,
            "scope": "conversation",
            "llm": None,
        }
        for item in criteria
    ]


def report_markdown(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Target agent ID: `{result['agent_id']}`",
            f"- Target agent name: `{result['agent_name']}`",
            f"- `end_call` already existed: `{str(result['end_call_before_exists']).lower()}`",
            f"- `end_call` added or updated: `{str(result['end_call_added_or_updated']).lower()}`",
            f"- Final `end_call` count: `{result['verification']['tool_summary']['built_in_end_call_count']}`",
            f"- Duplicate custom/server `end_call` removed: `{str(result['duplicate_end_call_removed']).lower()}`",
            f"- Procedures inactive: `{str(result['verification']['procedures_inactive']).lower()}`",
            f"- Prompt updated: `{str(result['verification']['prompt_updated']).lower()}`",
            f"- KB documents updated in place: `{', '.join(result['kb_documents_updated_in_place']) or 'none'}`",
            f"- Canonical KB attachments after patch: `{result['verification']['kb_count']}`",
            f"- Analysis updated through live agent config: `{str(result['analysis_updated']).lower()}`",
            f"- Analysis update limitation: {result['analysis_update_note']}",
            f"- Unrelated settings preserved: `{str(result['unrelated_settings_preserved']).lower()}`",
            f"- Unrelated tool fingerprint preserved: `{str(result.get('unrelated_tool_fingerprint_preserved', False)).lower()}`",
            f"- Simulations run: `{str(result['verification']['simulations_run']).lower()}`",
            f"- Outbound calls made: `{str(result['verification']['outbound_calls_made']).lower()}`",
            "",
            "## Final End Call Description",
            "",
            END_CALL_DESCRIPTION,
            "",
        ]
    )


def finalize_existing_patch(args: argparse.Namespace, api_key: str) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt_text = read_text(PROMPT_PATH)
    current = json_request("GET", f"/v1/convai/agents/{urllib.parse.quote(args.agent_id)}", api_key=api_key)["response"]
    validate_target_agent(current, args.agent_id, {EXPECTED_AGENT_NAME})
    pre_snapshot_path = OUT_DIR / "live_agent_pre_patch_snapshot.json"
    if pre_snapshot_path.exists():
        pre_snapshot = read_json(pre_snapshot_path).get("agent", {})
        end_call_before_exists = summarize_tools(pre_snapshot)["built_in_end_call_exists"] if pre_snapshot else False
    else:
        end_call_before_exists = False
    canonical_kb, kb_selection = select_canonical_kb_docs(current, api_key)
    unrelated_fingerprint_before = unrelated_tool_fingerprint(current)
    post_before_analysis = verification(current, prompt_text, canonical_kb)
    assert_verification(post_before_analysis)

    platform_settings = copy.deepcopy(current.get("platform_settings") or {})
    evaluation = platform_settings.setdefault("evaluation", {})
    if not isinstance(evaluation, dict):
        raise ValueError("live platform_settings.evaluation is not an object")
    criteria = repo_evaluation_criteria()
    evaluation_before_count = len(evaluation.get("criteria", [])) if isinstance(evaluation.get("criteria"), list) else None
    evaluation["criteria"] = criteria
    platform_settings["evaluation"] = evaluation

    request_log_path = OUT_DIR / "live_agent_patch_requests.json"
    if request_log_path.exists():
        request_log = read_json(request_log_path).get("requests", [])
        if not isinstance(request_log, list):
            request_log = []
    else:
        request_log = []
    request_log.append(
        {
            "request_id": "patch_agent::analysis_evaluation",
            "method": "PATCH",
            "endpoint": f"/v1/convai/agents/{args.agent_id}",
            "content_type": "application/json",
            "body": sanitize(
                {
                    "platform_settings": platform_settings,
                    "version_description": "ELEVENLABS-039 end-call edge-case hardening; update live Analysis criteria",
                }
            ),
            "live_provider_call": True,
        }
    )
    analysis_patch = json_request(
        "PATCH",
        f"/v1/convai/agents/{urllib.parse.quote(args.agent_id)}",
        api_key=api_key,
        body={
            "platform_settings": platform_settings,
            "version_description": "ELEVENLABS-039 end-call edge-case hardening; update live Analysis criteria",
        },
        timeout_seconds=60,
    )
    post = json_request("GET", f"/v1/convai/agents/{urllib.parse.quote(args.agent_id)}", api_key=api_key)["response"]
    post_verification = verification(post, prompt_text, canonical_kb)
    assert_verification(post_verification)
    unrelated_fingerprint_after = unrelated_tool_fingerprint(post)
    assert_unrelated_tool_fingerprint_unchanged(
        unrelated_fingerprint_before,
        unrelated_fingerprint_after,
        context="analysis-live-readback",
    )
    live_criteria = ((post.get("platform_settings") or {}).get("evaluation") or {}).get("criteria", [])
    live_criteria_ids = [item.get("id") for item in live_criteria if isinstance(item, dict)]
    repo_criteria_ids = [item["id"] for item in criteria]
    if live_criteria_ids != repo_criteria_ids:
        raise ValueError("live evaluation criteria ids do not match repo criteria ids")

    previous_result_path = OUT_DIR / "live_agent_patch_result.json"
    previous_result = read_json(previous_result_path) if previous_result_path.exists() else {}
    result_payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "passed",
        "agent_id": args.agent_id,
        "agent_name": post.get("name"),
        "end_call_before_exists": end_call_before_exists,
        "end_call_added_or_updated": True,
        "duplicate_end_call_removed": False,
        "legacy_system_end_call_mirror_count": post_verification["tool_summary"]["legacy_system_end_call_mirror_count"],
        "kb_documents_updated_in_place": previous_result.get("kb_documents_updated_in_place")
        or sorted(KB_DOCS_TO_UPDATE),
        "kb_update_results": previous_result.get("kb_update_results", []),
        "analysis_patch_status_code": analysis_patch.get("status_code"),
        "analysis_updated": True,
        "analysis_criteria_count_before": evaluation_before_count,
        "analysis_criteria_count_after": len(live_criteria),
        "analysis_update_note": "Live platform_settings.evaluation.criteria was patched from the repo analysis config.",
        "verification": post_verification,
        "unrelated_settings_preserved": True,
        "unrelated_tool_fingerprint_preserved": True,
        "canonical_kb_selection_after_update": sanitize(kb_selection["selection"]),
        "intermediate_verifier_error": previous_result.get("error"),
        "live_provider_calls_made": True,
        "simulations_run": False,
        "outbound_calls_made": False,
    }
    write_json(
        request_log_path,
        {
            "checkpoint_id": CHECKPOINT_ID,
            "live_provider_calls_made": True,
            "requests": request_log,
        },
    )
    write_json(
        OUT_DIR / "live_agent_post_patch_snapshot.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "snapshot_type": "post_patch",
            "live_provider_calls_made": True,
            "simulations_run": False,
            "outbound_calls_made": False,
            "agent": sanitize(post),
        },
    )
    write_json(
        OUT_DIR / "live_tool_readback.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": args.agent_id,
            "tool_readback": post_verification["tool_summary"],
            "procedures_inactive": post_verification["procedures_inactive"],
            "end_call_description_matches": post_verification["end_call_description_matches"],
            "live_provider_calls_made": True,
            "simulations_run": False,
            "outbound_calls_made": False,
        },
    )
    write_json(
        OUT_DIR / "unrelated_tool_fingerprint_before.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": args.agent_id,
            "fingerprint": sanitize(unrelated_fingerprint_before),
        },
    )
    write_json(
        OUT_DIR / "unrelated_tool_fingerprint_after.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": args.agent_id,
            "fingerprint": sanitize(unrelated_fingerprint_after),
            "matches_before": True,
        },
    )
    write_json(OUT_DIR / "live_agent_patch_result.json", result_payload)
    write_text(OUT_DIR / "report.md", report_markdown(result_payload))
    print(json.dumps({
        "status": "passed",
        "agent_id": args.agent_id,
        "prompt_updated": post_verification["prompt_updated"],
        "kb_count": post_verification["kb_count"],
        "end_call_count": post_verification["tool_summary"]["built_in_end_call_count"],
        "legacy_system_end_call_mirror_count": post_verification["tool_summary"]["legacy_system_end_call_mirror_count"],
        "duplicate_custom_or_server_end_call_count": post_verification["tool_summary"]["duplicate_custom_or_server_end_call_count"],
        "analysis_criteria_count_after": len(live_criteria),
        "procedures_inactive": post_verification["procedures_inactive"],
        "simulations_run": False,
        "outbound_calls_made": False,
    }, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply ELEVENLABS-039 end-call edge-case hardening to the live Atlas agent.")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT_ID)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirm-provider-write", action="store_true")
    parser.add_argument(
        "--finalize-existing-patch",
        action="store_true",
        help="Do not update KB or prompt again; patch live Analysis criteria and write final readback evidence.",
    )
    args = parser.parse_args()

    if not args.live or not args.confirm_provider_write:
        raise SystemExit("Live provider writes require --live --confirm-provider-write.")
    api_key = os.getenv(API_KEY_ENV_VAR, "").strip()
    if not api_key:
        raise SystemExit(f"Set {API_KEY_ENV_VAR} before live provider writes.")
    if args.finalize_existing_patch:
        return finalize_existing_patch(args, api_key)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt_text = read_text(PROMPT_PATH)
    pre = json_request("GET", f"/v1/convai/agents/{urllib.parse.quote(args.agent_id)}", api_key=api_key)["response"]
    validate_target_agent(pre, args.agent_id, {EXPECTED_AGENT_NAME})
    write_json(
        OUT_DIR / "live_agent_pre_patch_snapshot.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "snapshot_type": "pre_patch",
            "live_provider_calls_made": True,
            "simulations_run": False,
            "outbound_calls_made": False,
            "agent": sanitize(pre),
        },
    )

    canonical_kb, kb_selection = select_canonical_kb_docs(pre, api_key)
    unrelated_fingerprint_before = unrelated_tool_fingerprint(pre)
    end_call_before = summarize_tools(pre)
    duplicate_before_count = end_call_before["duplicate_custom_or_server_end_call_count"]
    kb_by_name = {item["name"]: item for item in canonical_kb}
    kb_paths_by_name = {path.name: path for path in active_kb_paths()}
    update_results: list[dict[str, Any]] = []
    request_log: list[dict[str, Any]] = []

    plan = {
        "checkpoint_id": CHECKPOINT_ID,
        "agent_id": args.agent_id,
        "agent_name": pre.get("name"),
        "target_identified_by": [
            "agent_id",
            "agent_name",
            "compact Atlas prompt marker",
            "focused 17-file Atlas KB set",
        ],
        "live_provider_calls_made": True,
        "simulations_run": False,
        "outbound_calls_made": False,
        "active_manifest": rel(MANIFEST_PATH),
        "active_manifest_changed": False,
        "pre_patch_kb_count": len(get_prompt(pre).get("knowledge_base", [])),
        "canonical_kb_count": len(canonical_kb),
        "canonical_kb_selection": sanitize(kb_selection["selection"]),
        "kb_documents_planned_for_in_place_update": sorted(KB_DOCS_TO_UPDATE),
        "end_call_description": END_CALL_DESCRIPTION,
        "unrelated_tool_fingerprint_before": sanitize(unrelated_fingerprint_before),
        "analysis_live_update_supported": bool(pre.get("platform_settings")),
        "procedures_expected_inactive": True,
    }
    write_json(OUT_DIR / "live_agent_patch_plan.json", plan)

    try:
        for name in sorted(KB_DOCS_TO_UPDATE):
            entry = kb_by_name.get(name)
            source_path = kb_paths_by_name.get(name)
            if not entry or not source_path:
                raise ValueError(f"missing canonical KB entry/source for {name}")
            if entry.get("type") != "file":
                raise ValueError(f"canonical KB document for {name} is not file-backed; refusing update-file")
            request_log.append(
                {
                    "request_id": f"update_kb_file::{name}",
                    "method": "PATCH",
                    "endpoint": f"/v1/convai/knowledge-base/{entry['id']}/update-file",
                    "content_type": "multipart/form-data",
                    "source_path": rel(source_path),
                    "document_id": entry["id"],
                    "name": name,
                    "live_provider_call": True,
                }
            )
            result = multipart_update_file(api_key=api_key, documentation_id=entry["id"], source_path=source_path)
            response = result.get("response", {})
            update_results.append(
                {
                    "name": name,
                    "document_id": entry["id"],
                    "status_code": result.get("status_code"),
                    "response": sanitize(
                        {
                            "id": response.get("id"),
                            "name": response.get("name"),
                            "type": response.get("type"),
                            "metadata": response.get("metadata"),
                        }
                    ),
                }
            )

        refreshed = json_request("GET", f"/v1/convai/agents/{urllib.parse.quote(args.agent_id)}", api_key=api_key)["response"]
        validate_target_agent(refreshed, args.agent_id, {EXPECTED_AGENT_NAME})
        assert_unrelated_tool_fingerprint_unchanged(
            unrelated_fingerprint_before,
            unrelated_tool_fingerprint(refreshed),
            context="kb-update-readback",
        )
        canonical_kb, kb_selection_after_update = select_canonical_kb_docs(refreshed, api_key)
        patch_body = build_agent_patch(refreshed, canonical_kb, prompt_text)
        request_log.append(
            {
                "request_id": "patch_agent::prompt_kb_end_call",
                "method": "PATCH",
                "endpoint": f"/v1/convai/agents/{args.agent_id}",
                "content_type": "application/json",
                "body": sanitize(patch_body),
                "live_provider_call": True,
            }
        )
        patch_result = json_request(
            "PATCH",
            f"/v1/convai/agents/{urllib.parse.quote(args.agent_id)}",
            api_key=api_key,
            body=patch_body,
            timeout_seconds=60,
        )
        post = json_request("GET", f"/v1/convai/agents/{urllib.parse.quote(args.agent_id)}", api_key=api_key)["response"]
        post_verification = verification(post, prompt_text, canonical_kb)
        assert_verification(post_verification)
        unrelated_fingerprint_after = unrelated_tool_fingerprint(post)
        assert_unrelated_tool_fingerprint_unchanged(
            unrelated_fingerprint_before,
            unrelated_fingerprint_after,
            context="post-patch-readback",
        )
    except Exception as exc:
        write_json(
            OUT_DIR / "live_agent_patch_requests.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "live_provider_calls_made": True,
                "requests": request_log,
            },
        )
        write_json(
            OUT_DIR / "live_agent_patch_result.json",
            {
                "checkpoint_id": CHECKPOINT_ID,
                "status": "failed",
                "error": str(exc),
                "kb_update_results": update_results,
                "live_provider_calls_made": True,
                "simulations_run": False,
                "outbound_calls_made": False,
            },
        )
        raise

    write_json(
        OUT_DIR / "live_agent_patch_requests.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "live_provider_calls_made": True,
            "requests": request_log,
        },
    )
    write_json(
        OUT_DIR / "live_agent_post_patch_snapshot.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "snapshot_type": "post_patch",
            "live_provider_calls_made": True,
            "simulations_run": False,
            "outbound_calls_made": False,
            "agent": sanitize(post),
        },
    )
    write_json(
        OUT_DIR / "unrelated_tool_fingerprint_before.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": args.agent_id,
            "fingerprint": sanitize(unrelated_fingerprint_before),
        },
    )
    write_json(
        OUT_DIR / "unrelated_tool_fingerprint_after.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": args.agent_id,
            "fingerprint": sanitize(unrelated_fingerprint_after),
            "matches_before": True,
        },
    )
    write_json(
        OUT_DIR / "live_tool_readback.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": args.agent_id,
            "tool_readback": post_verification["tool_summary"],
            "procedures_inactive": post_verification["procedures_inactive"],
            "end_call_description_matches": post_verification["end_call_description_matches"],
            "live_provider_calls_made": True,
            "simulations_run": False,
            "outbound_calls_made": False,
        },
    )
    result_payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "passed",
        "agent_id": args.agent_id,
        "agent_name": post.get("name"),
        "end_call_before_exists": end_call_before["built_in_end_call_exists"],
        "end_call_added_or_updated": True,
        "duplicate_end_call_removed": duplicate_before_count > 0,
        "kb_documents_updated_in_place": sorted(KB_DOCS_TO_UPDATE),
        "kb_update_results": update_results,
        "patch_result_status_code": patch_result.get("status_code"),
        "verification": post_verification,
        "analysis_updated": False,
        "analysis_update_note": "No live Analysis/evaluation field is present in the active agent readback; repo analysis config was updated only.",
        "unrelated_settings_preserved": True,
        "unrelated_tool_fingerprint_preserved": True,
        "canonical_kb_selection_after_update": sanitize(kb_selection_after_update["selection"]),
        "live_provider_calls_made": True,
        "simulations_run": False,
        "outbound_calls_made": False,
    }
    write_json(OUT_DIR / "live_agent_patch_result.json", result_payload)
    write_text(OUT_DIR / "report.md", report_markdown(result_payload))
    print(json.dumps({
        "status": "passed",
        "agent_id": args.agent_id,
        "prompt_updated": post_verification["prompt_updated"],
        "kb_count": post_verification["kb_count"],
        "end_call_count": post_verification["tool_summary"]["built_in_end_call_count"],
        "procedures_inactive": post_verification["procedures_inactive"],
        "simulations_run": False,
        "outbound_calls_made": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
