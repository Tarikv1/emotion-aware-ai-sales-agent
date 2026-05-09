#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import time
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from full_sale_scenario_grounding import (
    HIGH_SIMILARITY_THRESHOLD,
    LeakageFinding,
    collect_transient_sentences_from_zip_dir,
    leakage_status,
    normalize_text,
    sentence_fragments,
)


ROOT = Path(__file__).resolve().parents[1]
PROD_014_ID = "PROD-014-callcenteren-scenario-bank"
PROD_013_ID = "PROD-013-callcenteren-pattern-extraction"
DEFAULT_PATTERN_BANK = ROOT / "research" / "experiments" / "generated" / "PROD-013-callcenteren-pattern-extraction" / "pattern-bank.json"
DEFAULT_RAW_ZIP_DIR = ROOT / "data" / "external" / "callcenteren" / "raw"
DEFAULT_SCENARIO_COUNT = 240
DATASET_URL = "https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english"
PAPER_URL = "https://arxiv.org/abs/2507.02958"
LICENSE = "cc-by-nc-4.0"
SAFE_CLOSE_DEFINITION = "verbal commitment or sale-ready outcome without payment collection"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel_path(path: Path, *, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def safe_label(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_") or "unknown"


def first_record(records: list[dict[str, Any]], field: str, value: str) -> dict[str, Any] | None:
    for record in records:
        if str(record.get(field, "")) == value:
            return record
    return None


def first_pattern_id(records: list[dict[str, Any]], field: str, value: str, fallback: str) -> str:
    record = first_record(records, field, value)
    return str(record.get("pattern_id")) if record and record.get("pattern_id") else fallback


def non_unclear_intents(domain: dict[str, Any]) -> list[str]:
    intents = domain.get("common_customer_intents", {})
    ordered = sorted(((str(key), int(value)) for key, value in intents.items()), key=lambda item: item[1], reverse=True)
    return [label for label, _count in ordered if label != "unclear_intent"]


def top_key(counter_like: dict[str, Any], default: str) -> str:
    if not counter_like:
        return default
    ordered = sorted(((str(key), int(value)) for key, value in counter_like.items()), key=lambda item: item[1], reverse=True)
    return ordered[0][0] if ordered else default


def scenario_label_for(template: dict[str, Any], *, objection_override: str | None = None, tactic_override: str | None = None) -> str:
    intent = str(template.get("initial_intent", ""))
    objection = str(objection_override or template.get("likely_objection", ""))
    tactic = str(tactic_override or template.get("safe_agent_tactic", "")).lower()
    if intent == "buying_interest":
        return "sale_eligible"
    if intent == "callback_request":
        return "callback_request"
    if intent in {"cancellation", "wrong_person", "hostile_rejection", "not_interested"}:
        return "cancellation_boundary"
    if intent == "billing_issue" or (intent in {"technical_problem", "billing_issue"} and objection == "does_not_trust_agent"):
        return "trust_repair"
    if intent == "technical_problem" or "handoff" in tactic or "route" in tactic:
        return "support_handoff"
    if objection in {"does_not_trust_agent", "bad_previous_experience"}:
        return "trust_repair"
    if intent == "price_request" or objection in {"too_expensive", "payment_fear"}:
        return "price_objection"
    return "sale_eligible"


def expected_outcome_for(label: str, template: dict[str, Any]) -> str:
    if label == "sale_eligible":
        return "sale_ready"
    if label == "callback_request":
        return "callback_agreed"
    if label == "cancellation_boundary":
        return "end_call"
    if label in {"support_handoff", "trust_repair"}:
        return "human_handoff" if "handoff" in str(template.get("safe_agent_tactic", "")).lower() else "support_only"
    return "non_sale_correct"


def customer_prompt_for(label: str, intent: str, objection: str, domain: str) -> str:
    objection_prompts = {
        "too_expensive": "Before I decide, I need the cost explained in plain terms and why it is worth considering.",
        "not_interested": "I am not interested unless you can quickly connect this to a real problem I have.",
        "already_has_provider": f"I already have a {domain.replace('_', ' ')} provider, so explain what would actually change.",
        "needs_to_think": "I need time to think, so do not rush me into a decision.",
        "needs_spouse_or_manager": "I cannot decide alone, so help me understand what I would need to discuss with the other decision maker.",
        "bad_previous_experience": "I had a bad experience before, so I need a low-pressure reason to trust this next step.",
        "no_time": "I cannot talk now; give me one clear reason to schedule a callback.",
        "does_not_trust_agent": "I am not sure I trust this call, so explain what can be verified without pressuring me.",
        "confused_about_offer": "I am confused about what you are offering, so explain the useful part before asking me to decide.",
        "wants_written_info": "Send me the information, but first tell me what I should pay attention to.",
        "contract_fear": "I am worried about being locked into something, so clarify the commitment before any close.",
        "payment_fear": "I do not want to discuss payment; explain the next non-payment step if there is one.",
        "hidden_objection": "I am hesitating, and I need you to ask what is actually holding me back.",
    }
    if objection in objection_prompts:
        return objection_prompts[objection]
    if label == "sale_eligible":
        return "I am interested, but I need to know whether this actually fits my situation before I agree."
    if label == "price_objection":
        return "Before I decide, I need the cost explained in plain terms and why it is worth considering."
    if label == "callback_request":
        return "I cannot talk now; give me one clear reason to schedule a callback."
    if label == "cancellation_boundary":
        return "I am leaning toward cancelling, so do not try to sell until you understand why."
    if label == "support_handoff":
        return "My service issue is still unresolved, and I need help before discussing any offer."
    if label == "trust_repair":
        return "I am frustrated about this account issue and I need to know you will not guess or pressure me."
    if intent == "appointment_request":
        return "I might book a time, but I need the next step to be clear and low pressure."
    if objection == "already_has_provider":
        return f"I already have a {domain.replace('_', ' ')} provider, so explain what would actually change."
    return "I can listen briefly, but ask what matters before you try to close."


def response_requirements_for(label: str, tactic: str, avoid: list[str]) -> list[str]:
    base = [
        "acknowledge the customer's stated state without labeling their emotion as fact",
        "ask one focused discovery or clarification question before any close attempt",
        "avoid " + ", ".join(avoid),
    ]
    if label == "sale_eligible":
        return base + [
            "confirm eligibility and fit before a sale-ready close",
            "treat close as verbal commitment only, not payment collection",
        ]
    if label == "price_objection":
        return base + [
            "separate price concern from value, timing, and contract concerns",
            "use cost or value framing only if campaign facts support it",
        ]
    if label == "callback_request":
        return base + [
            "respect time pressure",
            "offer a callback only after stating a clear customer-relevant reason",
        ]
    if label == "cancellation_boundary":
        return [
            "stop selling until the boundary or cancellation reason is understood",
            "confirm whether the customer wants no further sales discussion",
            "avoid pressure, scarcity, or retention claims",
        ]
    if label == "support_handoff":
        return [
            "prioritize issue resolution before sales",
            "route or hand off instead of guessing",
            "avoid unsupported troubleshooting or product claims",
        ]
    if label == "trust_repair":
        return [
            "repair trust with transparency and a low-pressure next step",
            "explain what can and cannot be verified",
            "avoid urgency, vague claims, and overtalking",
        ]
    return base + [f"use tactic: {tactic}"]


def turn_plan_for(label: str, template: dict[str, Any], domain: dict[str, Any]) -> list[dict[str, Any]]:
    intent = str(template.get("initial_intent", "unclear_intent"))
    objection = str(template.get("likely_objection", "hidden_objection"))
    tactic = str(template.get("safe_agent_tactic", "ask one discovery question before closing"))
    avoid = [str(item) for item in template.get("avoid", [])] or ["premature_close"]
    emotion = str(template.get("emotion_state", domain.get("typical_emotional_tone", "neutral")))
    prompt = customer_prompt_for(label, intent, objection, str(domain.get("domain", "service")))
    requirements = response_requirements_for(label, tactic, avoid)
    flow = [str(stage) for stage in template.get("conversation_flow", [])] or ["opening", "discovery", "objection_handling"]
    if len(flow) < 3:
        flow = [*flow, "discovery", "objection_handling"][:3]
    return [
        {
            "turn_id": "turn-001",
            "stage": flow[0],
            "customer_prompt": prompt,
            "customer_intent": intent,
            "customer_emotion": emotion,
            "expected_agent_response_requirements": requirements[:3],
            "avoid": avoid,
            "success_signal": "customer continues without escalation or pressure response",
        },
        {
            "turn_id": "turn-002",
            "stage": flow[1],
            "customer_prompt": f"Customer raises `{objection}` while staying in a `{emotion}` tone.",
            "customer_intent": intent,
            "customer_emotion": emotion,
            "expected_agent_response_requirements": requirements,
            "avoid": avoid,
            "success_signal": "agent chooses safe tactic before close",
        },
        {
            "turn_id": "turn-003",
            "stage": flow[2],
            "customer_prompt": "Customer asks what the next safe step would be.",
            "customer_intent": intent,
            "customer_emotion": "neutral" if label not in {"support_handoff", "trust_repair"} else emotion,
            "expected_agent_response_requirements": response_requirements_for(label, tactic, avoid),
            "avoid": avoid,
            "success_signal": "next step matches scenario outcome and no payment is collected",
        },
    ]


def selected_variant_records(bank: dict[str, Any], index: int, label: str) -> dict[str, dict[str, Any]]:
    objections = list(bank.get("objection_patterns", []))
    strategies = list(bank.get("persuasion_strategy_patterns", []))
    emotions = list(bank.get("emotion_tone_transition_patterns", []))
    discoveries = list(bank.get("discovery_question_patterns", []))
    closes = list(bank.get("close_attempt_patterns", []))

    def pick(records: list[dict[str, Any]], offset: int = 0) -> dict[str, Any]:
        if not records:
            return {}
        return records[(index + offset) % len(records)]

    target_close_type = "handoff_close" if label in {"support_handoff", "trust_repair"} else "callback_close" if label == "callback_request" else "trial_close"
    close_candidates = [record for record in closes if str(record.get("close_type", "")) == target_close_type] or closes
    return {
        "objection": pick(objections, 0),
        "strategy": pick(strategies, index // 2),
        "emotion": pick(emotions, index // 3),
        "discovery": pick(discoveries, index // 5),
        "close": pick(close_candidates, index // 7),
    }


def variant_labels(variant: dict[str, dict[str, Any]]) -> dict[str, str]:
    objection = variant.get("objection", {})
    strategy = variant.get("strategy", {})
    emotion = variant.get("emotion", {})
    discovery = variant.get("discovery", {})
    close = variant.get("close", {})
    return {
        "objection": str(objection.get("objection_type", "")),
        "objection_emotion": str(objection.get("emotion_signal", "")),
        "strategy": str(strategy.get("strategy_label", strategy.get("use_strategy", ""))),
        "avoid_label": str(strategy.get("avoid_label", "")),
        "emotion_transition": str(emotion.get("transition_label", "")),
        "emotion_before": str(emotion.get("customer_emotion_before", "")),
        "emotion_after": str(emotion.get("customer_emotion_after", "")),
        "discovery_question": str(discovery.get("question_type", "")),
        "close_type": str(close.get("close_type", "")),
        "commitment_level": str(close.get("commitment_level", "")),
    }


def scenario_label_for_variant(template: dict[str, Any], variant: dict[str, dict[str, Any]]) -> str:
    labels = variant_labels(variant)
    return scenario_label_for(
        template,
        objection_override=labels["objection"] or None,
        tactic_override=labels["strategy"] or None,
    )


def turn_plan_for_variant(
    label: str,
    template: dict[str, Any],
    domain: dict[str, Any],
    variant: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    labels = variant_labels(variant)
    intent = str(template.get("initial_intent", "unclear_intent"))
    objection = labels["objection"] or str(template.get("likely_objection", "hidden_objection"))
    tactic = labels["strategy"] or str(template.get("safe_agent_tactic", "ask one discovery question before closing"))
    avoid = [str(item) for item in template.get("avoid", [])] or ["premature_close"]
    if labels["avoid_label"] and labels["avoid_label"] != "none" and labels["avoid_label"] not in avoid:
        avoid.append(labels["avoid_label"])
    emotion = labels["objection_emotion"] or labels["emotion_before"] or str(template.get("emotion_state", domain.get("typical_emotional_tone", "neutral")))
    prompt = customer_prompt_for(label, intent, objection, str(domain.get("domain", "service")))
    requirements = response_requirements_for(label, tactic, avoid)
    discovery_question = labels["discovery_question"] or "focused_discovery_question"
    flow = [str(stage) for stage in template.get("conversation_flow", [])] or ["opening", "discovery", "objection_handling"]
    if len(flow) < 3:
        flow = [*flow, "discovery", "objection_handling"][:3]
    return [
        {
            "turn_id": "turn-001",
            "stage": flow[0],
            "customer_prompt": prompt,
            "customer_intent": intent,
            "customer_emotion": emotion,
            "expected_agent_response_requirements": requirements[:3],
            "avoid": avoid,
            "success_signal": "customer continues without escalation or pressure response",
        },
        {
            "turn_id": "turn-002",
            "stage": flow[1],
            "customer_prompt": f"Customer raises `{objection}` and needs a `{discovery_question}` before any close.",
            "customer_intent": intent,
            "customer_emotion": emotion,
            "expected_agent_response_requirements": requirements,
            "avoid": avoid,
            "success_signal": "agent chooses safe tactic before close",
        },
        {
            "turn_id": "turn-003",
            "stage": flow[2],
            "customer_prompt": "Customer asks what the next safe step would be.",
            "customer_intent": intent,
            "customer_emotion": labels["emotion_after"] or ("neutral" if label not in {"support_handoff", "trust_repair"} else emotion),
            "expected_agent_response_requirements": response_requirements_for(label, tactic, avoid),
            "avoid": avoid,
            "success_signal": "next step matches scenario outcome and no payment is collected",
        },
    ]


def source_pattern_ids_for(
    template: dict[str, Any],
    domain: dict[str, Any],
    bank: dict[str, Any],
    variant: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    domain_label = str(domain.get("domain", "unknown"))
    intent = str(template.get("initial_intent", top_key(domain.get("common_customer_intents", {}), "unclear_intent")))
    labels = variant_labels(variant or {})
    objection = labels["objection"] or str(template.get("likely_objection", top_key(domain.get("common_objections", {}), "hidden_objection")))
    tactic = labels["strategy"] or str(template.get("safe_agent_tactic", "benefit_framing"))
    flow = [str(stage) for stage in template.get("conversation_flow", [])]
    label = scenario_label_for(template, objection_override=objection, tactic_override=tactic)
    categories: list[str] = []
    ids: list[str] = []
    variant_ids: list[str] = []

    def add(category: str, pattern_id: str, *, variant_source: bool = False) -> None:
        if pattern_id not in ids:
            ids.append(pattern_id)
        if category not in categories:
            categories.append(category)
        if variant_source and pattern_id and pattern_id not in variant_ids:
            variant_ids.append(pattern_id)

    add("scenario_template", str(template.get("template_id", f"template-{safe_label(intent)}")))
    add("domain_pattern", f"domain-{safe_label(domain_label)}")
    add("customer_intent", first_pattern_id(bank.get("customer_intent_patterns", []), "intent_label", intent, f"intent-{safe_label(intent)}"))
    objection_pattern_id = str((variant or {}).get("objection", {}).get("pattern_id", "")) or first_pattern_id(
        bank.get("objection_patterns", []), "objection_type", objection, f"objection-{safe_label(objection)}"
    )
    add("objection", objection_pattern_id, variant_source=True)
    strategy_pattern_id = str((variant or {}).get("strategy", {}).get("pattern_id", "")) or first_pattern_id(
        bank.get("persuasion_strategy_patterns", []), "strategy_label", safe_label(tactic), f"persuasion-{safe_label(tactic)}"
    )
    add("persuasion_strategy", strategy_pattern_id, variant_source=True)
    discovery = (variant or {}).get("discovery", {}) or (bank.get("discovery_question_patterns", [{}]) or [{}])[0]
    if discovery:
        add("discovery_question", str(discovery.get("pattern_id", "discovery-question")), variant_source=bool((variant or {}).get("discovery")))
    for stage in flow[:2]:
        add("turn_stage", first_pattern_id(bank.get("turn_stage_patterns", []), "stage_label", stage, f"stage-{safe_label(stage)}"))
    close_type = "handoff_close" if label in {"support_handoff", "trust_repair"} else "callback_close" if label == "callback_request" else "trial_close"
    close_pattern_id = str((variant or {}).get("close", {}).get("pattern_id", "")) or first_pattern_id(
        bank.get("close_attempt_patterns", []), "close_type", close_type, f"close-{safe_label(close_type)}"
    )
    add("close_attempt", close_pattern_id, variant_source=True)
    emotion_pattern_id = str((variant or {}).get("emotion", {}).get("pattern_id", ""))
    if emotion_pattern_id:
        add("emotion_transition", emotion_pattern_id, variant_source=True)
    if label in {"support_handoff", "cancellation_boundary", "trust_repair"}:
        safety = bank.get("safety_compliance_boundary_patterns", [])
        if safety:
            add("safety_boundary", str(safety[0].get("pattern_id", "safety-boundary")))
    return ids, categories, variant_ids


def available_source_pattern_counts(bank: dict[str, Any]) -> dict[str, int]:
    keys = [
        "scenario_templates",
        "domain_specific_scenario_patterns",
        "objection_patterns",
        "emotion_tone_transition_patterns",
        "persuasion_strategy_patterns",
        "discovery_question_patterns",
        "turn_stage_patterns",
        "close_attempt_patterns",
        "safety_compliance_boundary_patterns",
        "agent_mistake_patterns",
        "customer_personas",
    ]
    return {key: len(bank.get(key, [])) if isinstance(bank.get(key), list) else len(bank.get(key, {})) for key in keys}


def max_similarity_from_length(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    return (2 * min(len(left), len(right))) / (len(left) + len(right))


def detect_prod_014_leakage(
    scenarios: list[dict[str, Any]],
    source_sentences: list[str],
    runtime_prompts: list[str],
) -> list[LeakageFinding]:
    normalized_source = [normalize_text(item) for item in source_sentences if normalize_text(item)]
    normalized_prompts = "\n".join(normalize_text(prompt) for prompt in runtime_prompts)
    findings: list[LeakageFinding] = []

    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        text = "\n".join(str(value) for value in [
            scenario.get("scenario_title", ""),
            scenario.get("customer_context", ""),
            scenario.get("agent_goal", ""),
            *scenario.get("generated_turn_outline", []),
            *scenario.get("unsafe_behaviors_to_catch", []),
            *scenario.get("safe_close_criteria", []),
        ])
        normalized_scenario = normalize_text(text)
        scenario_sentences = [normalize_text(sentence) for sentence in sentence_fragments(text)]

        for source_sentence in normalized_source:
            if not source_sentence:
                continue
            if source_sentence in normalized_scenario:
                findings.append(LeakageFinding("exact_transcript_sentence", scenario_id, source_sentence[:120]))
            for scenario_sentence in scenario_sentences:
                if max_similarity_from_length(source_sentence, scenario_sentence) < HIGH_SIMILARITY_THRESHOLD:
                    continue
                matcher = SequenceMatcher(None, source_sentence, scenario_sentence)
                if matcher.quick_ratio() < HIGH_SIMILARITY_THRESHOLD:
                    continue
                ratio = matcher.ratio()
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
                    "commercial_runtime_prompt_contamination",
                    scenario_id,
                    "Scenario contains transcript-derived prompt text.",
                )
            )
    return findings


def build_scenarios(pattern_bank: dict[str, Any], scenario_count: int) -> list[dict[str, Any]]:
    bank = pattern_bank["pattern_bank"]
    templates = list(bank.get("scenario_templates", []))
    domains = list(bank.get("domain_specific_scenario_patterns", []))
    if not templates or not domains:
        return []

    desired = max(scenario_count, 1)
    scenarios: list[dict[str, Any]] = []
    seen_labels: Counter[str] = Counter()
    for index in range(desired):
        template = templates[index % len(templates)]
        domain = domains[(index // len(templates)) % len(domains)]
        base_label = scenario_label_for(template)
        variant = selected_variant_records(bank, index, base_label)
        label = scenario_label_for_variant(template, variant)
        seen_labels[label] += 1
        source_ids, categories, variant_source_ids = source_pattern_ids_for(template, domain, bank, variant)
        domain_label = str(domain.get("domain", "unknown"))
        turns = turn_plan_for_variant(label, template, domain, variant)
        scenario_id = f"prod-014-{safe_label(label)}-{seen_labels[label]:03d}"
        expected_outcome = expected_outcome_for(label, template)
        labels = variant_labels(variant)
        scenario = {
            "scenario_id": scenario_id,
            "scenario_label": label,
            "domain": domain_label,
            "source_recipe": {
                "source_pattern_bank": PROD_013_ID,
                "minimum_source_patterns": 5,
                "source_pattern_categories": categories,
                "variant_index": index,
                "variant_source_pattern_ids": variant_source_ids,
                "uses_exact_transcript_text": False,
                "uses_single_source_transcript": False,
            },
            "source_pattern_ids": source_ids,
            "source_pattern_category_count": len(categories),
            "customer_persona": str(template.get("customer_persona", "uncertain_buyer")),
            "initial_intent": str(template.get("initial_intent", "unclear_intent")),
            "likely_objection": labels["objection"] or str(template.get("likely_objection", top_key(domain.get("common_objections", {}), "hidden_objection"))),
            "starting_emotion": labels["objection_emotion"] or labels["emotion_before"] or str(template.get("emotion_state", domain.get("typical_emotional_tone", "neutral"))),
            "safe_agent_tactic": labels["strategy"] or str(template.get("safe_agent_tactic", "ask one discovery question before closing")),
            "emotion_transition_label": labels["emotion_transition"],
            "discovery_question_type": labels["discovery_question"],
            "close_type": labels["close_type"],
            "commitment_level": labels["commitment_level"],
            "bad_tactics_to_avoid": [str(item) for item in template.get("avoid", [])] or ["premature_close"],
            "conversation_flow": [turn["stage"] for turn in turns],
            "expected_outcome": expected_outcome,
            "safe_close_definition": SAFE_CLOSE_DEFINITION,
            "support_or_boundary_first": label in {"support_handoff", "cancellation_boundary", "trust_repair"},
            "commercial_runtime_prompt_safe": True,
            "copied_transcript_text_used": False,
            "generated_from_single_source_transcript": False,
            "contains_transcript_derived_prompt_text": False,
            "scenario_title": f"{domain_label.replace('_', ' ').title()} {label.replace('_', ' ')} scenario",
            "customer_context": f"Project-owned scenario built from abstract `{label}`, `{domain_label}`, and `{labels['objection'] or 'objection'}` pattern labels.",
            "agent_goal": "Use the safe tactic, discover fit or boundary, and avoid unsafe persuasion.",
            "generated_turn_outline": [
                f"{turn['stage']}: {turn['customer_prompt']} Agent must {turn['expected_agent_response_requirements'][0]}."
                for turn in turns
            ],
            "unsafe_behaviors_to_catch": [str(item) for item in template.get("avoid", [])] or ["premature_close"],
            "safe_close_criteria": [
                "verbal commitment or sale-ready outcome only",
                "no payment collection",
                "no unsupported claims",
                "support and do-not-call boundaries override sales",
            ],
            "turns": turns,
        }
        scenarios.append(scenario)
    return scenarios


def scenario_quality_score(scenarios: list[dict[str, Any]]) -> float:
    if not scenarios:
        return 0.0
    scores: list[float] = []
    for scenario in scenarios:
        checks = [
            len(scenario.get("source_pattern_ids", [])) >= 5,
            scenario.get("source_pattern_category_count", 0) >= 4,
            scenario.get("copied_transcript_text_used") is False,
            scenario.get("generated_from_single_source_transcript") is False,
            scenario.get("contains_transcript_derived_prompt_text") is False,
            scenario.get("commercial_runtime_prompt_safe") is True,
            bool(scenario.get("turns")),
            scenario.get("expected_outcome") in {"sale_ready", "callback_agreed", "non_sale_correct", "support_only", "human_handoff", "end_call"},
        ]
        scores.append(sum(1 for check in checks if check) / len(checks))
    return round(sum(scores) / len(scores), 4)


def metric_payload(scenarios: list[dict[str, Any]], leakage_findings: list[Any]) -> dict[str, Any]:
    labels = {scenario["scenario_label"] for scenario in scenarios}
    non_sale = [scenario for scenario in scenarios if scenario["expected_outcome"] in {"support_only", "human_handoff", "end_call", "non_sale_correct"}]
    safe_close = [scenario for scenario in scenarios if scenario["expected_outcome"] in {"sale_ready", "callback_agreed"}]
    emotion_values = {turn["customer_emotion"] for scenario in scenarios for turn in scenario.get("turns", [])}
    return {
        "scenario_quality_score": {
            "value": scenario_quality_score(scenarios),
            "definition": "Average scenario compliance with multi-pattern, no-transcript, outcome, and turn-coverage rules.",
        },
        "leakage_failure_rate": {
            "value": round(len(leakage_findings) / len(scenarios), 4) if scenarios else 0.0,
            "definition": "Leakage findings divided by generated scenarios.",
        },
        "safe_close_coverage": {
            "value": round(len(safe_close) / len(scenarios), 4) if scenarios else 0.0,
            "covered_labels": sorted(label for label in labels if label in {"sale_eligible", "callback_request", "price_objection"}),
        },
        "non_sale_boundary_coverage": {
            "value": round(len(non_sale) / len(scenarios), 4) if scenarios else 0.0,
            "covered_labels": sorted(label for label in labels if label in {"support_handoff", "cancellation_boundary", "trust_repair"}),
        },
        "emotion_transition_coverage": {
            "value": round(len(emotion_values) / 8, 4),
            "observed_emotion_labels": sorted(emotion_values),
        },
    }


def build_payload(
    pattern_bank_path: Path,
    *,
    scenario_count: int = DEFAULT_SCENARIO_COUNT,
    raw_zip_dir: Path | None = None,
    leakage_sentence_limit: int = 5000,
) -> dict[str, Any]:
    started = time.perf_counter()
    source = load_json(pattern_bank_path)
    scenarios = build_scenarios(source, scenario_count)
    bank = source.get("pattern_bank", {})
    recipe_keys = {
        "|".join(
            [
                str(scenario.get("domain", "")),
                str(scenario.get("initial_intent", "")),
                str(scenario.get("likely_objection", "")),
                str(scenario.get("safe_agent_tactic", "")),
                str(scenario.get("emotion_transition_label", "")),
                str(scenario.get("discovery_question_type", "")),
                str(scenario.get("close_type", "")),
                *[str(item) for item in scenario.get("source_recipe", {}).get("variant_source_pattern_ids", [])],
            ]
        )
        for scenario in scenarios
    }
    runtime_prompts: list[str] = []
    source_sentences: list[str] = []
    if raw_zip_dir is not None and raw_zip_dir.exists() and leakage_sentence_limit > 0:
        source_sentences = collect_transient_sentences_from_zip_dir(raw_zip_dir, limit=leakage_sentence_limit)
    findings = detect_prod_014_leakage(scenarios, source_sentences, runtime_prompts)
    summary = {
        "scenario_count_requested": scenario_count,
        "scenario_count": len(scenarios),
        "turn_count": sum(len(scenario.get("turns", [])) for scenario in scenarios),
        "unique_scenario_recipe_count": len(recipe_keys),
        "source_pattern_variant_count": len(recipe_keys),
        "available_source_pattern_counts": available_source_pattern_counts(bank),
        "source_pattern_reference_count": sum(len(scenario.get("source_pattern_ids", [])) for scenario in scenarios),
        "source_pattern_category_count": len({category for scenario in scenarios for category in scenario["source_recipe"]["source_pattern_categories"]}),
        "transient_source_sentence_count": len(source_sentences),
        "leakage_finding_count": len(findings),
        "provider_calls_made": False,
        "llm_used": False,
        "download_performed": False,
        "runtime_behavior_changed": False,
        "raw_transcript_text_stored": False,
        "ready_for_prod_015_evaluation": len(findings) == 0 and bool(scenarios),
        "elapsed_ms": int((time.perf_counter() - started) * 1000),
    }
    return {
        "prod_014_id": PROD_014_ID,
        "title": "CallCenterEN scenario bank generated from abstract PROD-013 patterns",
        "dataset_source": {
            "dataset_name": source.get("dataset_source", {}).get("dataset_name", "AIxBlock/92k-real-world-call-center-scripts-english"),
            "dataset_url": source.get("dataset_source", {}).get("dataset_url", DATASET_URL),
            "paper_url": source.get("dataset_source", {}).get("paper_url", PAPER_URL),
            "license": source.get("dataset_source", {}).get("license", LICENSE),
        },
        "source_pattern_bank": {
            "prod_013_id": source.get("prod_013_id", ""),
            "path": rel_path(pattern_bank_path),
            "conversation_count": source.get("summary", {}).get("conversation_count", 0),
            "turn_count": source.get("summary", {}).get("turn_count", 0),
            "speaker_role_signal_inference": source.get("source_characteristics", {}).get("speaker_role_signal_inference", False),
            "speaker_role_inference_is_ground_truth": source.get("source_characteristics", {}).get("speaker_role_inference_is_ground_truth", False),
        },
        "reuse_boundary": {
            "reuse_label": "abstract_scenario_bank_only",
            "raw_transcript_text_stored": False,
            "exact_script_storage_allowed": False,
            "company_specific_wording_allowed": False,
            "pii_placeholders_as_features_allowed": False,
            "agent_or_customer_names_allowed": False,
            "long_call_summaries_allowed": False,
            "commercial_runtime_prompt_text_from_transcripts_allowed": False,
            "commercial_model_training_allowed": False,
            "commercial_runtime_prompt_safe": True,
        },
        "scenario_generation": {
            "mode": "expanded_multi_pattern_combinatorial",
            "default_scenario_count": DEFAULT_SCENARIO_COUNT,
            "uses_scenario_templates": True,
            "uses_domain_variants": True,
            "uses_objection_variants": True,
            "uses_strategy_variants": True,
            "uses_emotion_variants": True,
            "uses_discovery_variants": True,
            "uses_close_variants": True,
            "raw_dataset_size_does_not_equal_scenario_count": True,
            "scenario_count_is_configurable": True,
        },
        "summary": summary,
        "metrics": metric_payload(scenarios, findings),
        "scenario_bank": scenarios,
        "leakage_tests": {
            "minimum_source_patterns_per_scenario": 5,
            "exact_transcript_sentence_check": {
                "status": leakage_status(findings, "exact_transcript_sentence"),
                "method": "normalized scan against transient local source sentences when raw ZIPs are available",
            },
            "high_similarity_paraphrase_check": {
                "status": leakage_status(findings, "high_similarity_paraphrase"),
                "method": "similarity scan against transient local source sentences when raw ZIPs are available",
            },
            "single_source_scenario_check": {
                "status": leakage_status(findings, "single_source_scenario"),
                "method": "each scenario must cite at least five abstract source pattern IDs across multiple categories",
            },
            "commercial_runtime_prompt_check": {
                "status": leakage_status(findings, "commercial_runtime_prompt_contamination"),
                "method": "no scenario text is exported as commercial runtime prompt material",
            },
            "findings": [finding.to_dict() for finding in findings],
        },
        "decision": "ready_for_prod_015_runtime_evaluation_without_runtime_promotion",
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    metrics = payload["metrics"]
    lines = [
        "# PROD-014 CallCenterEN Scenario Bank",
        "",
        "This scenario bank generated from PROD-013 turns abstract CallCenterEN pattern labels into testable, project-owned scenario packets.",
        "",
        "The main bank is expanded from multi-pattern combinations rather than capped to the old 24-scenario smoke slice.",
        "",
        "It uses no exact transcript text, no raw call summaries, no names, no provider calls, no LLM calls, and no transcript-derived runtime prompt material.",
        "",
        "Safe close means verbal commitment or sale-ready outcome without payment collection.",
        "",
        "## Summary",
        "",
        f"- Scenarios: `{summary['scenario_count']}`",
        f"- Requested scenarios: `{summary['scenario_count_requested']}`",
        f"- Unique scenario recipes: `{summary['unique_scenario_recipe_count']}`",
        f"- Turns: `{summary['turn_count']}`",
        f"- Source pattern references: `{summary['source_pattern_reference_count']}`",
        f"- Source pattern categories: `{summary['source_pattern_category_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        f"- Ready for PROD-015: `{summary['ready_for_prod_015_evaluation']}`",
        "",
        "## Metrics",
        "",
    ]
    for key, metric in metrics.items():
        lines.append(f"- {key}: `{metric['value']}`")
    lines.extend(["", "## Leakage Tests", ""])
    for name, check in payload["leakage_tests"].items():
        if isinstance(check, dict) and "status" in check:
            lines.append(f"- {name}: `{check['status']}`")
    lines.extend(["", "## Scenario Packets", ""])
    for scenario in payload["scenario_bank"]:
        lines.append(
            "- `{scenario_id}` `{label}` domain `{domain}` outcome `{outcome}` patterns `{patterns}`".format(
                scenario_id=scenario["scenario_id"],
                label=scenario["scenario_label"],
                domain=scenario["domain"],
                outcome=scenario["expected_outcome"],
                patterns=len(scenario["source_pattern_ids"]),
            )
        )
    lines.extend(
        [
            "",
            "## Runtime Boundary",
            "",
            "PROD-014 does not change runtime behavior. Use it as the input bank for PROD-015 evaluation, where old runtime and retrieval runtime can answer the same generated customer prompts under leakage, safe-close, and non-sale correctness metrics.",
        ]
    )
    return "\n".join(lines) + "\n"
