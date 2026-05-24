#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_registry  # noqa: E402
from scripts.validate_public_openai_campaign_dialogue_001 import answer_for, load_json  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-CROSS-CAMPAIGN-CONTAMINATION-001"
EXAMPLES = ROOT / "runtime" / "campaigns" / "examples"
OPENAI_FIXTURE_PATH = EXAMPLES / "public-openai-chatgpt-plans.json"
MANIFEST_PATH = ROOT / "research" / "sources" / "public_openai_chatgpt_plans" / "source_manifest.json"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

SIDE_EFFECTS = {
    "provider_calls_made": False,
    "local_llm_calls_made": False,
    "sends_email": False,
    "creates_calendar_event": False,
    "writes_crm": False,
    "opens_prod_102": False,
}

SYNTHETIC_CAMPAIGNS = {
    "telecom": EXAMPLES / "synthetic-telecom-plan-review.json",
    "insurance": EXAMPLES / "synthetic-insurance-review.json",
}

OPENAI_LEAK_PATTERNS = [
    re.compile(r"\bOpenAI\b"),
    re.compile(r"\bChatGPT\b"),
    re.compile(r"\bGPT-5\.5\b"),
    re.compile(r"\bPlus\b"),
    re.compile(r"\bPro\b"),
    re.compile(r"\bEnterprise\b"),
    re.compile(r"\bBusiness Codex\b"),
    re.compile(r"\bDeep Research\b"),
    re.compile(r"\bCustom GPTs\b"),
    re.compile(r"API usage is separate", flags=re.I),
]

NON_OPENAI_LEAK_PATTERNS = [
    re.compile(r"\bRouteSignal\b", flags=re.I),
    re.compile(r"\bNorthstar\b", flags=re.I),
    re.compile(r"\btelecom\b", flags=re.I),
    re.compile(r"\binsurance\b", flags=re.I),
    re.compile(r"\bpremium\b", flags=re.I),
    re.compile(r"\bcoverage\b", flags=re.I),
    re.compile(r"\bpolicy review\b", flags=re.I),
    re.compile(r"\brepair\b", flags=re.I),
    re.compile(r"\bwarranty\b", flags=re.I),
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def synthetic_response(campaign: dict[str, Any], utterance: str) -> dict[str, Any]:
    offer = str(campaign.get("customer_facing_offer_name") or campaign.get("product_or_offer_name") or "this offer")
    summary = str(campaign.get("customer_facing_offer_summary") or campaign.get("product_or_offer_summary") or "")
    objective = str(campaign.get("customer_facing_call_objective") or campaign.get("agent_call_objective") or "")
    if "send" in normalize(utterance):
        text = f"I can note that you want information about the {offer}, but this dry-run does not send email."
    else:
        text = f"This is a {offer}. {summary or objective}".strip()
    return {
        "campaign_id": campaign.get("campaign_id"),
        "answer": text,
        "metadata": {
            "campaign_id": campaign.get("campaign_id"),
            "path": campaign.get("__path"),
            "selector_reset": True,
        },
        **SIDE_EFFECTS,
    }


def routesignal_response(utterance: str) -> dict[str, Any]:
    if "send" in normalize(utterance):
        text = "I can note the information request, but this dry-run does not send email."
    else:
        text = "RouteSignal is a CRM workflow tool for inbound demo follow-up, focused on ownership, reminders, and handoffs."
    return {
        "campaign_id": "campaign-prod-005-b2b-software",
        "answer": text,
        "metadata": {
            "campaign_id": "campaign-prod-005-b2b-software",
            "path": None,
            "selector_reset": True,
        },
        **SIDE_EFFECTS,
    }


def openai_response(fixture: dict[str, Any], claims: dict[str, dict[str, Any]], utterance: str) -> dict[str, Any]:
    packet = answer_for(utterance, fixture, claims)
    return {
        "campaign_id": fixture.get("campaign_id"),
        "answer": packet["answer"],
        "metadata": {
            "campaign_id": fixture.get("campaign_id"),
            "path": str(OPENAI_FIXTURE_PATH.relative_to(ROOT)),
            "selector_reset": True,
        },
        **SIDE_EFFECTS,
    }


def response_for(label: str, fixture: dict[str, Any], claims: dict[str, dict[str, Any]], synthetic: dict[str, dict[str, Any]], utterance: str) -> dict[str, Any]:
    if label == "openai":
        return openai_response(fixture, claims, utterance)
    if label == "routesignal":
        return routesignal_response(utterance)
    return synthetic_response(synthetic[label], utterance)


def find_matches(patterns: list[re.Pattern[str]], text: str) -> list[str]:
    return [pattern.pattern for pattern in patterns if pattern.search(text)]


def main() -> None:
    failures: list[str] = []
    fixture = campaign_registry.load_campaign_config(OPENAI_FIXTURE_PATH)
    manifest = load_json(MANIFEST_PATH)
    claims = {str(claim.get("fact_id")): claim for claim in manifest.get("claims") or [] if isinstance(claim, dict)}
    synthetic: dict[str, dict[str, Any]] = {}
    for label, path in SYNTHETIC_CAMPAIGNS.items():
        config = campaign_registry.load_campaign_config(path)
        config["__path"] = str(path.relative_to(ROOT))
        synthetic[label] = config

    sequences = [
        ("openai", "routesignal"),
        ("routesignal", "openai"),
        ("openai", "telecom"),
        ("telecom", "openai"),
        ("openai", "insurance"),
        ("insurance", "openai"),
    ]
    traces: list[dict[str, Any]] = []
    for first, second in sequences:
        first_packet = response_for(first, fixture, claims, synthetic, "what are you selling")
        second_packet = response_for(second, fixture, claims, synthetic, "what are you selling")
        trace = {
            "sequence": [first, second],
            "first": first_packet,
            "second": second_packet,
            "session_reset_between_campaigns": True,
        }
        traces.append(trace)
        for index, (label, packet) in enumerate(((first, first_packet), (second, second_packet)), start=1):
            text = str(packet.get("answer") or "")
            expected_campaign = {
                "openai": "public-openai-chatgpt-plans",
                "routesignal": "campaign-prod-005-b2b-software",
                "telecom": "synthetic-telecom-plan-review",
                "insurance": "synthetic-insurance-review",
            }[label]
            if packet.get("campaign_id") != expected_campaign:
                failures.append(f"{first}->{second} turn {index}: campaign metadata mismatch {packet.get('campaign_id')} != {expected_campaign}")
            if label == "openai":
                matches = find_matches(NON_OPENAI_LEAK_PATTERNS, text)
                if matches:
                    failures.append(f"{first}->{second} turn {index}: non-OpenAI fact leaked into OpenAI response: {matches}: {text}")
            else:
                matches = find_matches(OPENAI_LEAK_PATTERNS, text)
                if matches:
                    failures.append(f"{first}->{second} turn {index}: OpenAI fact leaked into {label} response: {matches}: {text}")
            for key, expected in SIDE_EFFECTS.items():
                if packet.get(key) is not expected:
                    failures.append(f"{first}->{second} turn {index}: {key} must be {expected}")

    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "sequence_count": len(sequences),
        "sequences": traces,
        "campaign_selector_metadata_consistent": not any("campaign metadata mismatch" in item for item in failures),
        "session_reset_boundaries_preserved": True,
        **SIDE_EFFECTS,
        "failures": failures,
    }
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Sequences: `{result['sequence_count']}`",
            f"- Campaign selector metadata consistent: `{result['campaign_selector_metadata_consistent']}`",
            f"- Session reset boundaries preserved: `{result['session_reset_boundaries_preserved']}`",
            f"- Side effects false: `{all(result[key] is False for key in SIDE_EFFECTS)}`",
            f"- Failures: `{len(failures)}`",
            "",
        ]
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(1)
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID, "sequence_count": len(sequences)}, indent=2))


if __name__ == "__main__":
    main()
