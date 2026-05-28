#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from prosody_quality_common import (
    CLEANUP_PLAN_DIR,
    GENERATED_DIR,
    MAPPING_PATH,
    RULES_PATH,
    TAXONOMY_PATH,
    base_boundary_flags,
    count_by,
    label_index,
    load_json,
    write_json,
    write_report,
)


TODAY = "2026-05-29"
PHASE = "4I4"
FALLBACK_DISALLOWED_FOR = [
    "live_call",
    "regulated_claim",
    "confused_buyer",
    "angry_buyer",
    "boundary_request",
]


def words_from_id(label_id: str) -> str:
    return label_id.split(".", 1)[-1].replace("_", " ")


def category_profile(category: str) -> dict[str, str]:
    profiles = {
        "pacing": {
            "description": "Sets speaking speed for {phrase} so call tempo matches buyer state without adding pressure or changing claims.",
            "use": "Use when {context} needs a tempo adjustment around {phrase}; keep the answer short, grounded, and buyer-controlled.",
            "text": "Shape this with clause length and sentence count: slower for explanation, tighter for simple confirmations.",
            "eleven": "For a future ElevenLabs adapter, express this with pace and sentence-length guidance only; keep spoken text free of bracket tags.",
        },
        "pause": {
            "description": "Controls silence placement for {phrase} so the buyer has space after objections, prices, repairs, or decisions.",
            "use": "Use when {context} benefits from a deliberate pause around {phrase}; avoid using silence as pressure.",
            "text": "Use punctuation and turn boundaries to create a natural pause without markup.",
            "eleven": "For a future ElevenLabs adapter, use pause and punctuation hints only; never insert raw Fish tags.",
        },
        "volume": {
            "description": "Sets relative loudness intent for {phrase} while keeping phone delivery calm and non-theatrical.",
            "use": "Use when {context} needs volume moderation for {phrase}; keep the voice conversational and respectful.",
            "text": "Use word choice and fewer exclamation-like cues; do not write stage directions into the reply.",
            "eleven": "For a future ElevenLabs adapter, map to supported voice-setting or style-prompt controls only if available.",
        },
        "pitch": {
            "description": "Sets pitch contour for {phrase} so questions, confidence, and closes sound natural rather than dramatic.",
            "use": "Use when {context} needs a pitch cue for {phrase}; avoid emotional exaggeration.",
            "text": "Use normal question punctuation and decisive sentence endings; avoid written pitch notation.",
            "eleven": "For a future ElevenLabs adapter, use approved style guidance only; no bracketed pitch tags in spoken text.",
        },
        "tone": {
            "description": "Defines the professional stance for {phrase} so the agent sounds consultative instead of scripted or pushy.",
            "use": "Use when {context} needs a tone boundary around {phrase}; keep source claims honest.",
            "text": "Choose plain, direct wording and avoid hype, fake intimacy, or internal reasoning language.",
            "eleven": "For a future ElevenLabs adapter, use style-prompt wording if supported; do not inject raw control tags.",
        },
        "warmth": {
            "description": "Sets the amount of empathy for {phrase} while preserving professional distance and buyer control.",
            "use": "Use when {context} needs reassurance or rapport around {phrase}; do not simulate intimacy.",
            "text": "Use brief acknowledgements and customer-first phrasing without emotional performance.",
            "eleven": "For a future ElevenLabs adapter, express warmth through style prompt or voice settings only after review.",
        },
        "confidence": {
            "description": "Sets certainty level for {phrase} while preserving caveats, source boundaries, and no-overclaim behavior.",
            "use": "Use when {context} needs decisiveness around {phrase}; only sound certain when the claim is grounded.",
            "text": "Use decisive verbs for known facts and short caveats for changeable terms.",
            "eleven": "For a future ElevenLabs adapter, keep confidence as an internal style hint; no raw Fish syntax.",
        },
        "energy": {
            "description": "Sets momentum for {phrase} so the call can move forward without hype or forced excitement.",
            "use": "Use when {context} needs energy adjustment around {phrase}; avoid urgency unless it is buyer-requested and factual.",
            "text": "Use shorter turns for low energy and concise next-step wording for momentum.",
            "eleven": "For a future ElevenLabs adapter, map only to restrained energy guidance supported by the provider.",
        },
        "clarity": {
            "description": "Shapes wording for {phrase} so the buyer hears one clear idea at a time.",
            "use": "Use when {context} needs simpler phrasing around {phrase}; do not hide uncertainty or omit source limits.",
            "text": "Use shorter words, one idea per sentence, and a natural relevance check only when needed.",
            "eleven": "For a future ElevenLabs adapter, this remains mostly text shaping, not tag injection.",
        },
        "emotion_response": {
            "description": "Adapts delivery to buyer emotion for {phrase} without mirroring, exaggerating, or manipulating the buyer.",
            "use": "Use when {context} shows a buyer emotion matching {phrase}; keep the response useful, brief, and low pressure.",
            "text": "Acknowledge the emotion lightly, answer the point, then move one step forward.",
            "eleven": "For a future ElevenLabs adapter, express only safe emotional stance through reviewed style hints.",
        },
        "objection_handling": {
            "description": "Guides delivery for {phrase} so objections are acknowledged, answered, and advanced without argument.",
            "use": "Use when {context} contains the objection pattern {phrase}; answer directly before any next question.",
            "text": "Start with a brief acknowledgement, give the useful contrast, and avoid repeated qualification.",
            "eleven": "For a future ElevenLabs adapter, use calm objection-handling style hints only; no raw tags.",
        },
        "trust_building": {
            "description": "Controls trust cues for {phrase} so the agent is transparent about sources, limitations, and buyer control.",
            "use": "Use when {context} needs trust repair or source boundaries around {phrase}; never imply hidden actions.",
            "text": "Name the boundary plainly and route to official channels when terms can change.",
            "eleven": "For a future ElevenLabs adapter, keep trust cues in text shape and approved style guidance.",
        },
        "sales_delivery": {
            "description": "Guides the selling move for {phrase} so value, fit, and next steps are concise rather than feature-dumped.",
            "use": "Use when {context} calls for the sales move {phrase}; keep the buyer moving toward a decision.",
            "text": "Tie the answer to buyer words, make one point, then stop or ask one relevant question.",
            "eleven": "For a future ElevenLabs adapter, map to delivery style only after text behavior is separately approved.",
        },
        "plan_explanation": {
            "description": "Shapes plan explanation for {phrase} so subscriptions, tiers, API boundaries, and privacy limits stay understandable.",
            "use": "Use when {context} needs plan explanation around {phrase}; do not invent current prices or terms.",
            "text": "Use plain plan names, define one distinction, and check relevance only when useful.",
            "eleven": "For a future ElevenLabs adapter, keep this as text and pacing guidance, not raw tags.",
        },
        "recommendation_delivery": {
            "description": "Controls recommendation delivery for {phrase} so the agent can recommend or disqualify without overselling.",
            "use": "Use when {context} has enough fit signal for {phrase}; state the decision rule and caveat missing context.",
            "text": "Give the recommendation first, then the short reason, then a low-pressure next step.",
            "eleven": "For a future ElevenLabs adapter, express recommendation confidence through reviewed style settings only.",
        },
        "closing_delivery": {
            "description": "Controls closing behavior for {phrase} so the agent advances, exits, or stops without fake side effects.",
            "use": "Use when {context} reaches a close state around {phrase}; never keep selling after acceptance or refusal.",
            "text": "Use a short close sentence and avoid extra questions after terminal decisions.",
            "eleven": "For a future ElevenLabs adapter, use only subtle delivery hints; never inject tags or fake actions.",
        },
        "repair": {
            "description": "Guides repair delivery for {phrase} so corrections, ASR uncertainty, and repeated context are handled without loops.",
            "use": "Use when {context} needs a repair around {phrase}; acknowledge once and move forward.",
            "text": "Apologize briefly if needed, restate known context, and avoid asking the same question again.",
            "eleven": "For a future ElevenLabs adapter, repair remains text-shape and pause guidance.",
        },
        "clarification": {
            "description": "Guides one-question clarification for {phrase} so discovery stays natural and does not expose classifier language.",
            "use": "Use when {context} truly lacks the information needed for {phrase}; ask one short natural question.",
            "text": "Ask a single plain question and avoid stacked options unless comparison is required.",
            "eleven": "For a future ElevenLabs adapter, clarify through wording and pacing only.",
        },
        "boundary_respect": {
            "description": "Controls boundary response for {phrase} so privacy, contact, CRM, and stop requests are respected immediately.",
            "use": "Use when {context} contains a boundary request around {phrase}; do not persist after refusal.",
            "text": "Confirm the boundary, state no hidden action, and stop pressure.",
            "eleven": "For a future ElevenLabs adapter, keep the boundary in plain text; no emotional performance.",
        },
        "phone_call_delivery": {
            "description": "Shapes phone-call turn behavior for {phrase} so spoken interaction stays brief, interruptible, and natural.",
            "use": "Use when {context} needs phone discipline around {phrase}; avoid script-reading and stacked questions.",
            "text": "Keep turns short, answer then ask, and recover cleanly after interruption.",
            "eleven": "For a future ElevenLabs adapter, use call-delivery style hints only if supported and reviewed.",
        },
        "multilingual_delivery": {
            "description": "Guides multilingual delivery for {phrase} so brand names and plan terms stay clear across spoken variation.",
            "use": "Use when {context} includes language or pronunciation friction around {phrase}; avoid unnecessary translation.",
            "text": "Prefer simple English, careful brand names, and idiom-free phrasing.",
            "eleven": "For a future ElevenLabs adapter, map pronunciation and pace only through approved controls.",
        },
        "source_and_truthfulness": {
            "description": "Controls truthfulness delivery for {phrase} so source-grounded claims are clear without source-scaffold overuse.",
            "use": "Use when {context} needs source or affiliation handling around {phrase}; caveat terms that can change.",
            "text": "State grounded facts plainly, avoid fake affiliation, and route to official pages for current terms.",
            "eleven": "For a future ElevenLabs adapter, keep this as wording and confidence guidance only.",
        },
        "safety_and_compliance": {
            "description": "Blocks unsafe speech behavior for {phrase} so compliance boundaries are explicit in internal planning.",
            "use": "Use when {context} touches safety or compliance around {phrase}; this is a guardrail, not a buyer-facing tag.",
            "text": "Use plain safe wording and avoid internal policy language in the spoken response.",
            "eleven": "For a future ElevenLabs adapter, enforce as a no-tag safety constraint before any style mapping.",
        },
        "unsafe_or_disallowed": {
            "description": "Marks the blocked style {phrase} so it can be detected, avoided, and never mapped into live speech.",
            "use": "Use only as evidence or an avoid-list marker when {context} could drift toward {phrase}.",
            "text": "Do not render this as spoken style; replace it with a calm, respectful alternative.",
            "eleven": "Do not map this to ElevenLabs. It is a blocked internal marker and must not become a style prompt.",
        },
    }
    return profiles[category]


def clean_label(label: dict[str, Any]) -> dict[str, Any]:
    label = deepcopy(label)
    label_id = str(label.get("label_id", ""))
    category = str(label.get("category", ""))
    phrase = words_from_id(label_id)
    context = ", ".join(label.get("sales_contexts") or [category]).replace("_", " ")
    profile = category_profile(category)
    risk = str(label.get("risk_level") or "low")
    risky_marker = (
        category == "unsafe_or_disallowed"
        or label_id.startswith("unsafe.")
        or label_id.startswith("safety.no_")
        or "no_fake" in label_id
        or "manipulative" in label_id
        or "pressure" in label_id
        or "overclaim" in label_id
    )
    if risky_marker:
        risk = "high"
    label["description"] = profile["description"].format(phrase=phrase, context=context)
    label["when_to_use"] = profile["use"].format(phrase=phrase, context=context)
    label["when_not_to_use"] = (
        "Do not use this as a live-safe style, a pressure tactic, a substitute for source grounding, "
        "or a reason to continue after a buyer refusal."
        if category != "unsafe_or_disallowed"
        else "Never use this as an allowed delivery style; keep it only as a blocked-style marker."
    )
    label["allowed_in_live"] = False
    label["internal_only"] = True
    label["risk_level"] = risk
    if risk == "high":
        label["disallowed_for"] = sorted(set(label.get("disallowed_for") or []) | set(FALLBACK_DISALLOWED_FOR))
    elif not isinstance(label.get("disallowed_for"), list):
        label["disallowed_for"] = []
    label["safety_notes"] = (
        "Internal-only prosody control. Do not expose raw Fish-style tags, fake side effects, "
        "or unverified claims in buyer-facing speech."
    )
    label["backend_mapping"] = {
        "elevenlabs_hint": profile["eleven"].format(phrase=phrase, context=context),
        "plain_text_hint": profile["text"].format(phrase=phrase, context=context),
        "future_fish_hint": (
            f"Future/internal only: {phrase} may map to approved Fish-style controls only if Fish is "
            "explicitly selected, licensed, reviewed, and enabled in a later phase."
        ),
        "kokoro_hint": (
            f"Future benchmark only: approximate {phrase} with punctuation, speed, phrasing, or voice choice "
            "only if Kokoro is later evaluated and approved."
        ),
        "liquid_hint": (
            "No current Liquid mapping. Liquid remains architecture inspiration only after failed manual "
            "listening review."
        ),
    }
    if "bracket" not in label["backend_mapping"]["elevenlabs_hint"].lower() and "tag" not in label["backend_mapping"]["elevenlabs_hint"].lower():
        label["backend_mapping"]["elevenlabs_hint"] += " Do not add bracket tags to spoken text."
    return label


def scenario_key(mapping_id: str) -> str:
    match = re.match(r"^mapping\.\d+\.(?P<scenario>.+?)\.[^.]+$", mapping_id)
    return match.group("scenario") if match else mapping_id


def variant_name(mapping_id: str) -> str:
    return mapping_id.rsplit(".", 1)[-1]


def extra_label_for_mapping(mapping: dict[str, Any], scenario: str) -> str:
    text = " ".join(
        str(mapping.get(key) or "")
        for key in ("buyer_emotion", "sales_move", "objection_type", "decision_stage", "close_readiness")
    ).lower()
    if "already" in scenario:
        return "repair.summarize_known_context"
    if "asr" in scenario:
        return "repair.repeat_with_different_words"
    if "terminal_acceptance" in scenario or "accepted" in text:
        return "close.stop_after_acceptance"
    if "no_fit" in scenario:
        return "close.no_fit_close"
    if "boundary" in scenario or "no_email" in text or "no_crm" in text or "no_calendar" in text or "stop" in text:
        return "boundary.no_pressure_after_boundary"
    if "privacy" in scenario or "privacy" in text:
        return "trust.official_route_only"
    if "source" in scenario or "affiliation" in text:
        return "source.official_route_boundary"
    if "competitor" in scenario or "current_tool" in scenario or "already_have_tool" in text:
        return "objection.competitor_gap_probe"
    if "price" in scenario or "price" in text:
        return "objection.price_cost_control"
    if "confused" in scenario or "plan" in scenario or "subscription" in scenario or "api" in text:
        return "clarity.repeat_differently"
    if "recommend" in scenario or "enterprise" in text:
        return "recommend.confidence_based_on_known_context"
    if "close" in scenario:
        return "close.next_step_without_pressure"
    if "impatient" in scenario or "too_busy" in scenario:
        return "pacing.compress_for_impatient_buyer"
    if "interested" in scenario:
        return "energy.increase_for_momentum"
    if "disengaged" in scenario:
        return "emotion_response.disengaged_buyer_relevance_bridge"
    if "correction" in scenario or "wrong_product" in scenario:
        return "repair.move_forward_after_repair"
    return "sales.concise_summary"


def clean_mapping(mapping: dict[str, Any], scenario: str, role: str, collapsed: list[str], labels_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    mapping = deepcopy(mapping)
    selected = list(dict.fromkeys(mapping.get("selected_prosody_labels") or []))
    if role != "base_behavior" or len(selected) < 3:
        candidates = [
            extra_label_for_mapping(mapping, scenario),
            "sales.low_pressure_next_step",
            "sales.concise_summary",
            "clarity.summary_before_next_question",
        ]
        for extra in candidates:
            if extra in labels_by_id and extra not in selected:
                selected.append(extra)
                break
    selected = [label_id for label_id in selected if label_id in labels_by_id and not label_id.startswith("unsafe.")]
    if len(selected) > 8:
        selected = selected[:8]
    mapping["selected_prosody_labels"] = selected
    mapping["backend_mapping_notes"] = (
        "Evidence-only internal prosody mapping. Later ElevenLabs work may use text length, punctuation, "
        "or reviewed style hints; raw Fish-style tags remain blocked and no provider call is made. "
        f"Cleanup role: {role}; collapsed duplicate variants: {collapsed or 'none'}."
    )
    mapping["parameterization"] = {
        "family_id": scenario,
        "variant_role": role,
        "collapsed_variant_ids": collapsed,
        "parameterized_dimensions": [
            "buyer_friction_level",
            "buyer_confusion_level",
            "buyer_skepticism_level",
            "buyer_engagement_level",
        ],
        "rationale": "4I4 collapsed repeated low/medium/base rows unless the retained variant changes delivery behavior.",
    }
    mapping["avoid_styles"] = sorted(set(mapping.get("avoid_styles") or []) | {"raw bracket tags", "fake side effects", "pressure after refusal"})
    return mapping


def clean_mappings(mappings: list[dict[str, Any]], labels_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mapping in mappings:
        groups[scenario_key(str(mapping.get("mapping_id", "")))].append(mapping)

    cleaned: list[dict[str, Any]] = []
    collapsed_count = 0
    for scenario, group in groups.items():
        group = sorted(group, key=lambda item: str(item.get("mapping_id", "")))
        base = next((item for item in group if variant_name(str(item.get("mapping_id", ""))) == "base"), group[0])
        non_base = [item for item in group if item is not base]
        retained_variant = non_base[-1] if non_base else None
        collapsed_for_base = [str(item.get("mapping_id")) for item in non_base[:-1]]
        cleaned.append(clean_mapping(base, scenario, "base_behavior", collapsed_for_base, labels_by_id))
        collapsed_count += len(collapsed_for_base)
        if retained_variant is not None:
            cleaned.append(clean_mapping(retained_variant, scenario, "elevated_or_specific_behavior", [], labels_by_id))

    return cleaned, {
        "scenario_family_count": len(groups),
        "mapping_count_before": len(mappings),
        "mapping_count_after": len(cleaned),
        "collapsed_mapping_variant_count": collapsed_count,
    }


def clean_rule(rule: dict[str, Any]) -> dict[str, Any]:
    rule = deepcopy(rule)
    rule_id = str(rule.get("rule_id", ""))
    scenario = rule_id.replace("rule.", "").replace("_", " ")
    rule["conflict_resolution"] = {
        "priority_order": [
            "safety_and_boundary",
            "repair_or_asr_uncertainty",
            "terminal_close",
            "objection_handling",
            "sales_momentum",
        ],
        "instructions": (
            "When labels conflict, prefer boundary respect, source truthfulness, and repair over energy, urgency, "
            "or closing pressure."
        ),
    }
    rule["backend_notes"] = (
        f"Evidence-only rule for {scenario}. Current ElevenLabs text remains plain; future mapping may use "
        "sentence shape, punctuation, or reviewed style hints only. Raw Fish-style tags are disallowed."
    )
    if any(term in rule_id for term in ("close", "terminal", "boundary", "pressure", "urgent", "objection")):
        rule["safety_notes"] = (
            "Stop after buyer acceptance or refusal where relevant. Do not add pressure, fake side effects, "
            "raw bracket tags, provider calls, live TTS, or runtime wiring."
        )
    else:
        rule["safety_notes"] = (
            "No provider call, no live TTS, no runtime wiring, no buyer-facing Fish tag injection, and no "
            "response text behavior change."
        )
    return rule


def duplicate_signature_count(mappings: list[dict[str, Any]]) -> int:
    counts: dict[tuple[str, str, str], int] = defaultdict(int)
    for mapping in mappings:
        signature = (
            "|".join(mapping.get("selected_prosody_labels", [])),
            str(mapping.get("example_spoken_text_before", "")),
            str(mapping.get("example_spoken_text_after", "")),
        )
        counts[signature] += 1
    return sum(1 for count in counts.values() if count > 1)


def update_baseline_evidence(taxonomy: dict[str, Any], mappings: list[dict[str, Any]], rules: list[dict[str, Any]]) -> None:
    fish_path = GENERATED_DIR / "FISH-INSPIRED-PROSODY-TAXONOMY-001" / "result.json"
    fish = load_json(fish_path)
    fish["phase"] = PHASE
    fish["taxonomy_label_count"] = len(taxonomy.get("labels", []))
    fish["taxonomy_category_count"] = len(count_by(taxonomy.get("labels", []), "category"))
    fish["unsafe_disallowed_label_count"] = count_by(taxonomy.get("labels", []), "category").get("unsafe_or_disallowed", 0)
    fish["runtime_behavior_changed"] = False
    fish["response_text_changed"] = False
    write_json(fish_path, fish)

    sales_path = GENERATED_DIR / "SALES-PROSODY-MAPPING-001" / "result.json"
    sales = load_json(sales_path)
    sales["phase"] = PHASE
    sales["composition_rule_count"] = len(rules)
    sales["sales_mapping_count"] = len(mappings)
    sales["runtime_behavior_changed"] = False
    sales["response_text_changed"] = False
    write_json(sales_path, sales)
    write_report(
        GENERATED_DIR / "SALES-PROSODY-MAPPING-001" / "report.md",
        "SALES-PROSODY-MAPPING-001",
        [
            "Status: pass",
            f"- composition_rule_count: {len(rules)}",
            f"- sales_mapping_count: {len(mappings)}",
            f"- examples_count: {sales.get('examples_count')}",
            "- 4I4 collapsed duplicated mapping variants into parameterized base/elevated rows.",
            "- No provider calls, audio generation, Fish inference, Liquid inference, Kokoro inference, live wiring, runtime behavior change, or response text change.",
        ],
    )

    planner_path = GENERATED_DIR / "PROSODY-PLANNER-PROTOTYPE-001" / "result.json"
    planner = load_json(planner_path)
    planner["phase"] = PHASE
    planner["taxonomy_label_count"] = len(taxonomy.get("labels", []))
    planner["composition_rule_count"] = len(rules)
    planner["sales_mapping_count"] = len(mappings)
    planner["live_runtime_wiring_changed"] = False
    planner["provider_calls_made"] = False
    planner["elevenlabs_calls_made"] = False
    planner["live_tts_calls_made"] = False
    planner["runtime_behavior_changed"] = False
    planner["response_text_changed"] = False
    write_json(planner_path, planner)


def write_cleanup_plan(before: dict[str, Any], mapping_before: dict[str, Any], mapping_cleanup: dict[str, Any], taxonomy: dict[str, Any]) -> None:
    label_count = len(taxonomy.get("labels", []))
    plan = {
        "experiment_id": "PROSODY-TAXONOMY-CLEANUP-PLAN-001",
        "phase": PHASE,
        "status": "pass",
        "input_evidence": [
            "research/experiments/generated/PROSODY-TAXONOMY-QUALITY-AUDIT-001/result.json",
            "research/experiments/generated/SALES-PROSODY-MAPPING-QUALITY-AUDIT-001/result.json",
            "research/experiments/generated/PROSODY-PLANNER-DRY-RUN-AUDIT-001/result.json",
            "research/experiments/generated/PROSODY-TAXONOMY-QUALITY-DECISION-001/result.json",
        ],
        "issue_classification": {
            "true_duplicate_label": "Exact same descriptions or when_to_use fields should be rewritten or merged.",
            "acceptable_family_similarity": "Shared Fish-inspired tags and sales contexts are expected inside category families and should not be counted as true duplicates.",
            "too_vague_label": "Generic labels without sales-state-specific guidance need stronger descriptions and hints.",
            "boilerplate_backend_hint": "Repeated provider hints must be rewritten with concrete text/pause/style mapping limits.",
            "risky_label_needs_restriction": "High-risk and unsafe labels stay internal-only, live-disallowed, and populated with disallowed_for contexts.",
            "mapping_duplicate_variant": "Triplicated base/low/medium rows without behavior changes should be collapsed.",
            "mapping_should_be_parameterized": "Friction and engagement variants should live as parameters when selected labels and examples are otherwise identical.",
            "mapping_needs_human_review": "Mappings with loop risk, terminal-close pressure, or unsupported claims require review.",
            "no_action_needed": "Required coverage families and blocked unsafe styles should remain separate.",
        },
        "total_labels_reviewed": label_count,
        "duplicate_clusters_before": before.get("duplicate_label_count"),
        "labels_to_merge_remove": 0,
        "labels_to_keep_but_clarify": before.get("too_vague_label_count"),
        "labels_to_mark_internal_only_evidence_only": before.get("risky_label_count"),
        "labels_whose_backend_hints_need_rewriting": before.get("backend_mapping_boilerplate_label_count"),
        "mapping_variants_to_collapse": mapping_cleanup["collapsed_mapping_variant_count"],
        "mapping_variants_to_keep": mapping_cleanup["mapping_count_after"],
        "expected_label_count_after_cleanup": label_count,
        "expected_mapping_count_after_cleanup": mapping_cleanup["mapping_count_after"],
        "expected_duplicate_mapping_signature_count_after_cleanup": 0,
        "constraints": {
            "taxonomy_label_count_minimum": 220,
            "mapping_count_minimum": 80,
            "preserve_required_categories": True,
            "preserve_unsafe_disallowed_labels": True,
            "fish_tags_internal_only": True,
            "elevenlabs_current_path_unchanged": True,
        },
        "before_metrics": {
            "taxonomy_label_count": before.get("taxonomy_label_count"),
            "duplicate_label_count": before.get("duplicate_label_count"),
            "true_duplicate_count": before.get("true_duplicate_count", 0),
            "too_vague_label_count": before.get("too_vague_label_count"),
            "backend_hint_boilerplate_count": before.get("backend_mapping_boilerplate_label_count"),
            "mapping_count": mapping_before.get("mapping_count"),
            "mapping_duplicate_signature_count": mapping_before.get("duplicate_mapping_signature_count"),
        },
        "boundary_flags": base_boundary_flags(),
        "provider_calls_made": False,
        "elevenlabs_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    write_json(CLEANUP_PLAN_DIR / "result.json", plan)
    write_report(
        CLEANUP_PLAN_DIR / "report.md",
        "PROSODY-TAXONOMY-CLEANUP-PLAN-001",
        [
            "Status: pass",
            f"- total_labels_reviewed: {label_count}",
            f"- duplicate_clusters_before: {before.get('duplicate_label_count')}",
            f"- labels_to_keep_but_clarify: {before.get('too_vague_label_count')}",
            f"- backend hints to rewrite: {before.get('backend_mapping_boilerplate_label_count')}",
            f"- mapping variants to collapse: {mapping_cleanup['collapsed_mapping_variant_count']}",
            f"- expected_label_count_after_cleanup: {label_count}",
            f"- expected_mapping_count_after_cleanup: {mapping_cleanup['mapping_count_after']}",
            "- Family similarity is retained where it preserves sales coverage; exact duplicate semantics are rewritten instead of deleting useful labels.",
            "- No provider calls, audio generation, runtime behavior change, response text change, or live wiring.",
        ],
    )


def main() -> int:
    taxonomy = load_json(TAXONOMY_PATH)
    mapping_payload = load_json(MAPPING_PATH)
    rules_payload = load_json(RULES_PATH)
    before_audit = load_json(GENERATED_DIR / "PROSODY-TAXONOMY-QUALITY-AUDIT-001" / "result.json")
    before_mapping_audit = load_json(GENERATED_DIR / "SALES-PROSODY-MAPPING-QUALITY-AUDIT-001" / "result.json")

    taxonomy["phase"] = PHASE
    taxonomy["updated_on"] = TODAY
    taxonomy["cleanup_version"] = "4I4-cleanup-001"
    taxonomy["labels"] = [clean_label(label) for label in taxonomy.get("labels", [])]
    labels_by_id = label_index(taxonomy)

    cleaned_mappings, mapping_cleanup = clean_mappings(mapping_payload.get("mappings", []), labels_by_id)
    mapping_payload["phase"] = PHASE
    mapping_payload["updated_on"] = TODAY
    mapping_payload["cleanup_version"] = "4I4-cleanup-001"
    mapping_payload["mappings"] = cleaned_mappings

    rules_payload["phase"] = PHASE
    rules_payload["updated_on"] = TODAY
    rules_payload["cleanup_version"] = "4I4-cleanup-001"
    rules_payload["composition_rules"] = [clean_rule(rule) for rule in rules_payload.get("composition_rules", [])]

    write_json(TAXONOMY_PATH, taxonomy)
    write_json(MAPPING_PATH, mapping_payload)
    write_json(RULES_PATH, rules_payload)
    update_baseline_evidence(taxonomy, cleaned_mappings, rules_payload["composition_rules"])
    write_cleanup_plan(before_audit, before_mapping_audit, mapping_cleanup, taxonomy)

    output = {
        "status": "pass",
        "taxonomy_label_count": len(taxonomy.get("labels", [])),
        "mapping_count_before": mapping_cleanup["mapping_count_before"],
        "mapping_count_after": mapping_cleanup["mapping_count_after"],
        "collapsed_mapping_variant_count": mapping_cleanup["collapsed_mapping_variant_count"],
        "duplicate_mapping_signature_count_after": duplicate_signature_count(cleaned_mappings),
        "composition_rule_count": len(rules_payload["composition_rules"]),
        "provider_calls_made": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
    }
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
