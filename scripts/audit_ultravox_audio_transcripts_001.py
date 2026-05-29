#!/usr/bin/env python3
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001" / "result.json"
QUALITY_RESULT_PATH = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-QUALITY-001" / "result.json"
RESULT_DIR = ROOT / "research" / "experiments" / "generated" / "ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001"
RESULT_PATH = RESULT_DIR / "result.json"
REPORT_PATH = RESULT_DIR / "report.md"
EXPECTED_USER_PHRASES = ["What is this?", "Don't put me in CRM."]


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def clip(text: Any, limit: int = 220) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def normalize(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def fuzzy_match(expected: str, observed: str) -> bool:
    expected_norm = normalize(expected)
    observed_norm = normalize(observed)
    if not expected_norm or not observed_norm:
        return False
    return expected_norm in observed_norm or observed_norm in expected_norm or difflib.SequenceMatcher(None, expected_norm, observed_norm).ratio() >= 0.86


def transcripts_by_role(sandbox: dict[str, Any], role: str) -> list[str]:
    texts: list[str] = []
    for item in sandbox.get("final_transcripts_sanitized", []):
        if isinstance(item, dict) and item.get("role") == role and item.get("text"):
            texts.append(str(item["text"]))
    return texts


def expected_phrase_matches(user_texts: list[str]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for expected in EXPECTED_USER_PHRASES:
        exact = [text for text in user_texts if text == expected]
        fuzzy = [text for text in user_texts if fuzzy_match(expected, text)]
        matches.append(
            {
                "expected_phrase": expected,
                "exact_match": bool(exact),
                "fuzzy_match": bool(fuzzy),
                "matched_transcript_snippet": clip(exact[0] if exact else (fuzzy[0] if fuzzy else "")),
            }
        )
    return matches


def response_matches_expected_tool(agent_texts: list[str], expected_responses: list[Any]) -> bool:
    joined_agent = "\n".join(agent_texts).lower()
    if not joined_agent.strip():
        return False
    for response in expected_responses:
        if not isinstance(response, dict):
            continue
        expected = str(response.get("buyer_facing_response") or "").strip().lower()
        if not expected:
            continue
        for agent in agent_texts:
            agent_norm = agent.strip().lower()
            if agent_norm and (agent_norm in expected or expected in agent_norm):
                return True
    return False


def build_result(sandbox: dict[str, Any], quality: dict[str, Any]) -> dict[str, Any]:
    user_texts = transcripts_by_role(sandbox, "user")
    agent_texts = transcripts_by_role(sandbox, "agent")
    matches = expected_phrase_matches(user_texts)
    agent_joined = "\n".join(agent_texts).lower()
    transcript_text_available = bool(user_texts or agent_texts)
    user_audio_correctly_transcribed = all(match["exact_match"] or match["fuzzy_match"] for match in matches)
    crm_preserved = any("CRM" in text for text in user_texts)
    boundary_request_understood = "crm" in agent_joined and ("will not claim" in agent_joined or "not claim" in agent_joined)
    response_respected_tool = response_matches_expected_tool(agent_texts, sandbox.get("expected_tool_responses_sanitized", []))
    invented_product_facts = int(sandbox.get("product_truth_drift_count", 0)) > 0 or int(sandbox.get("unsupported_claim_count", 0)) > 0
    claimed_fake_side_effects = int(sandbox.get("fake_side_effect_count", 0)) > 0
    exposed_internal_labels = int(sandbox.get("internal_label_leak_count", 0)) > 0
    claimed_openai = "openai" in agent_joined
    transcript_quality_passed = (
        transcript_text_available
        and user_audio_correctly_transcribed
        and crm_preserved
        and boundary_request_understood
        and response_respected_tool
        and not invented_product_facts
        and not claimed_fake_side_effects
        and not exposed_internal_labels
        and not claimed_openai
    )
    return {
        "evaluation_id": "ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001",
        "phase": "4J6",
        "source_sandbox_evaluation_id": sandbox.get("evaluation_id"),
        "source_quality_evaluation_id": quality.get("evaluation_id"),
        "user_transcript_count": int(sandbox.get("user_transcript_count", 0)),
        "agent_transcript_count": int(sandbox.get("agent_transcript_count", 0)),
        "transcript_text_available": transcript_text_available,
        "missing_transcript_text": not transcript_text_available,
        "expected_user_phrases": EXPECTED_USER_PHRASES,
        "expected_phrase_matches": matches,
        "user_audio_correctly_transcribed": user_audio_correctly_transcribed,
        "crm_preserved": crm_preserved,
        "boundary_request_understood": boundary_request_understood,
        "agent_response_respected_project_tool_output": response_respected_tool,
        "agent_invented_product_facts": invented_product_facts,
        "agent_claimed_fake_side_effects": claimed_fake_side_effects,
        "agent_exposed_internal_labels": exposed_internal_labels,
        "agent_claimed_openai_affiliation": claimed_openai,
        "raw_private_data_in_transcript": False,
        "public_evidence_sanitized": sandbox.get("raw_private_audio_or_transcripts_used") is False and sandbox.get("join_url_full_recorded") is False,
        "sanitized_transcript_snippets": [
            {"role": "user", "text": clip(text)} for text in user_texts
        ]
        + [{"role": "agent", "text": clip(text)} for text in agent_texts],
        "product_truth_drift_count": int(sandbox.get("product_truth_drift_count", 0)),
        "unsupported_claim_count": int(sandbox.get("unsupported_claim_count", 0)),
        "fake_side_effect_count": int(sandbox.get("fake_side_effect_count", 0)),
        "internal_label_leak_count": int(sandbox.get("internal_label_leak_count", 0)),
        "crm_email_calendar_claim_count": int(sandbox.get("crm_email_calendar_claim_count", 0)),
        "transcript_quality_passed": transcript_quality_passed,
        "new_provider_call_made": False,
        "new_audio_generated": False,
        "audio_files_copied": False,
        "audio_files_committed": False,
        "outbound_phone_call_made": False,
        "real_customer_data_used": False,
        "raw_private_audio_or_transcripts_used": False,
        "live_wiring_allowed": False,
        "production_call_allowed": False,
        "real_customer_data_allowed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }


def render_report(result: dict[str, Any]) -> str:
    lines = [
        "# ULTRAVOX-AUDIO-TRANSCRIPT-QUALITY-001",
        "",
        f"User transcript count: `{result['user_transcript_count']}`",
        f"Agent transcript count: `{result['agent_transcript_count']}`",
        f"Transcript text available: `{str(result['transcript_text_available']).lower()}`",
        f"Missing transcript text: `{str(result['missing_transcript_text']).lower()}`",
        f"User audio correctly transcribed: `{str(result['user_audio_correctly_transcribed']).lower()}`",
        f"CRM preserved: `{str(result['crm_preserved']).lower()}`",
        f"Boundary request understood: `{str(result['boundary_request_understood']).lower()}`",
        f"Agent response respected project tool output: `{str(result['agent_response_respected_project_tool_output']).lower()}`",
        f"Agent invented product facts: `{str(result['agent_invented_product_facts']).lower()}`",
        f"Agent claimed fake side effects: `{str(result['agent_claimed_fake_side_effects']).lower()}`",
        f"Agent exposed internal labels: `{str(result['agent_exposed_internal_labels']).lower()}`",
        f"Agent claimed OpenAI affiliation: `{str(result['agent_claimed_openai_affiliation']).lower()}`",
        f"Public evidence sanitized: `{str(result['public_evidence_sanitized']).lower()}`",
        f"Transcript quality passed: `{str(result['transcript_quality_passed']).lower()}`",
        "",
        "## Expected Phrase Matches",
    ]
    for match in result["expected_phrase_matches"]:
        lines.append(
            f"- `{match['expected_phrase']}` exact=`{str(match['exact_match']).lower()}` fuzzy=`{str(match['fuzzy_match']).lower()}` observed=`{match['matched_transcript_snippet']}`"
        )
    lines.extend(
        [
            "",
            "## Sanitized Snippets",
            *[f"- {item['role']}: {item['text']}" for item in result["sanitized_transcript_snippets"]],
            "",
            "## Boundaries",
            "New provider call made: `false`",
            "New audio generated: `false`",
            "Audio files copied: `false`",
            "Audio files committed: `false`",
            "Outbound phone call made: `false`",
            "Real customer data used: `false`",
            "Raw private audio or transcripts used: `false`",
            "Live wiring allowed: `false`",
            "Production call allowed: `false`",
            "Runtime behavior changed: `false`",
            "Response text changed: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    sandbox = load_json(SANDBOX_RESULT_PATH)
    quality = load_json(QUALITY_RESULT_PATH)
    result = build_result(sandbox, quality)
    write_json(RESULT_PATH, result)
    write_text(REPORT_PATH, render_report(result))
    print(json.dumps({"transcript_quality_passed": result["transcript_quality_passed"], "user_transcript_count": result["user_transcript_count"]}, indent=2))


if __name__ == "__main__":
    main()
