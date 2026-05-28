from __future__ import annotations

import json
from pathlib import Path
from typing import Any


TRAINING_DIR = Path(__file__).resolve().parent / "training"
LIVE_ACTION_CONTRACT_PATH = TRAINING_DIR / "qwen_live_action_contract.json"
UNCERTAINTY_POLICY_PATH = TRAINING_DIR / "qwen_buyer_facing_uncertainty_policy.json"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def live_action_contract() -> dict[str, Any]:
    return _read_json(LIVE_ACTION_CONTRACT_PATH)


def buyer_facing_uncertainty_policy() -> dict[str, Any]:
    return _read_json(UNCERTAINTY_POLICY_PATH)


def default_available_action_ids() -> list[str]:
    action_space = live_action_contract().get("action_space")
    if not isinstance(action_space, dict):
        return []
    action_ids = action_space.get("semantic_reusable_action_ids")
    return [str(item) for item in action_ids or [] if isinstance(item, str)]


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _compact_fact_summaries(value: dict[str, str] | None) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): " ".join(str(text).split())[:240] for key, text in sorted(value.items())}


def _compact_uncertainty_rules(value: dict[str, Any] | None) -> list[dict[str, str]]:
    policy = value if isinstance(value, dict) else buyer_facing_uncertainty_policy()
    mappings = policy.get("mappings") if isinstance(policy.get("mappings"), list) else []
    compact: list[dict[str, str]] = []
    for item in mappings:
        if not isinstance(item, dict):
            continue
        internal = item.get("internal")
        buyer_facing = item.get("buyer_facing")
        if isinstance(internal, str) and isinstance(buyer_facing, str):
            compact.append({"internal": internal, "buyer_facing": buyer_facing})
    return compact


def render_live_action_prompt(
    *,
    sanitized_buyer_utterance: str,
    last_agent_response: str = "",
    memory_ledger_summary: dict[str, Any] | None = None,
    available_action_ids: list[str] | None = None,
    approved_campaign_fact_ids: list[str] | None = None,
    approved_campaign_fact_summaries: dict[str, str] | None = None,
    buyer_facing_uncertainty_rules: dict[str, Any] | None = None,
    safety_constraints: list[str] | None = None,
    replan_instruction: str | None = None,
) -> str:
    """Render the disabled live-action prompt contract without calling a model."""

    action_ids = available_action_ids or default_available_action_ids()
    required_fields = live_action_contract().get("required_fields") or [
        "action_id",
        "slots",
        "memory_updates",
        "uncertainty",
        "say",
    ]
    constraints = safety_constraints or [
        "no fake side effects",
        "no unsupported facts",
        "no internal language in say",
        "preserve buyer wording, and/or, negation, voice, and not-team corrections",
        "if unsure, ask a natural clarification",
    ]
    context = {
        "buyer": " ".join(str(sanitized_buyer_utterance or "").split()),
        "last_agent_response": " ".join(str(last_agent_response or "").split()),
        "memory": memory_ledger_summary or {},
        "action_ids": action_ids,
        "approved_fact_ids": approved_campaign_fact_ids or [],
        "approved_fact_summaries": _compact_fact_summaries(approved_campaign_fact_summaries),
        "uncertainty_rules": _compact_uncertainty_rules(buyer_facing_uncertainty_rules),
        "safety_constraints": constraints,
    }
    lines = [
        "You are the LLM conversation brain for a sales call.",
        "Choose the next conversational move and buyer-facing wording.",
        "Return exactly one small JSON object. No markdown. No reasoning.",
        f"Required fields: {', '.join(str(field) for field in required_fields)}.",
        "Use one action_id from the provided semantic action_ids. Slots are open.",
        "Do not output full compact planner JSON, schema explanation, route labels, or policy language.",
        "Do not claim product facts unless supported by approved_fact_summaries.",
        "Do not claim email, calendar, CRM, purchase, ticket, TTS, or other side effects happened.",
        "If uncertain, set uncertainty and ask a natural buyer-facing clarification in say.",
        "Preserve the buyer's wording and avoid loops using memory.",
    ]
    if replan_instruction:
        lines.extend(
            [
                "Replan instruction:",
                replan_instruction,
                "Do not repeat the prior question or response. Use known memory and move forward.",
            ]
        )
    lines.extend(["Context:", _json(context)])
    return "\n".join(lines)
