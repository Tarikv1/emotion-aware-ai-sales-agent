#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from prosody_quality_common import base_boundary_flags, load_json, write_json, write_report


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from runtime.audio_backends.elevenlabs_prosody_mapper import (  # noqa: E402
    map_prosody_plan_to_elevenlabs_hints,
    validate_elevenlabs_prosody_mapping,
)
from runtime.audio_backends.prosody_planner import plan_prosody_for_sales_turn  # noqa: E402


AUDIO_DIR = ROOT / "runtime" / "audio_backends"
TAXONOMY_PATH = AUDIO_DIR / "prosody_sales_taxonomy.json"
MAPPING_PATH = AUDIO_DIR / "sales_prosody_mapping.json"
RULES_PATH = AUDIO_DIR / "prosody_composition_rules.json"
BACKEND_POLICY_PATH = AUDIO_DIR / "prosody_backend_mapping_policy.json"
ELEVENLABS_POLICY_PATH = AUDIO_DIR / "elevenlabs_prosody_mapping_policy.json"
OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001"


def example_specs() -> list[tuple[str, dict[str, Any], str]]:
    return [
        (
            "confused buyer plan explanation",
            {"buyer_emotion": "confused", "buyer_confusion_level": "high", "sales_move": "plan_explanation"},
            "I can make that simpler. Plus is for a single person who wants stronger everyday help. Pro is for heavier use, deeper work, and more room to run demanding tasks.",
        ),
        (
            "confused buyer price",
            {"buyer_emotion": "confused", "buyer_confusion_level": "high", "sales_move": "price_answer"},
            "The price question depends on which plan fits your use. I would start by separating light daily use from heavier work, then compare the cost against that need.",
        ),
        (
            "skeptical buyer source question",
            {"buyer_emotion": "skeptical", "buyer_skepticism_level": "high", "sales_move": "source_affiliation_answer"},
            "I am not claiming a special affiliation. I can explain the public plan differences in plain language and point you back to the official signup route.",
        ),
        (
            "skeptical buyer competitor objection",
            {"buyer_emotion": "skeptical", "buyer_skepticism_level": "high", "objection_type": "competitor"},
            "That comparison is reasonable. If your current tool already covers the work well, there may be no need to switch. The useful test is where it slows you down.",
        ),
        (
            "impatient buyer direct price",
            {"buyer_emotion": "impatient", "buyer_friction_level": "medium", "sales_move": "price_answer"},
            "Short version: choose the lowest plan that covers your actual workload. If you only need occasional help, do not overbuy.",
        ),
        (
            "price objection heavy use",
            {"buyer_emotion": "price_sensitive", "buyer_engagement_level": "high", "sales_move": "recommendation", "objection_type": "price"},
            "If you use it every day for client work or long tasks, the value case is stronger. If usage is occasional, the lower plan is the safer starting point.",
        ),
        (
            "price objection low budget",
            {"buyer_emotion": "price_sensitive", "buyer_friction_level": "high", "objection_type": "price"},
            "If budget is tight, I would not push the higher plan. Start with the lowest useful option, then upgrade only if the limit becomes real.",
        ),
        (
            "current tool objection",
            {"buyer_emotion": "skeptical", "objection_type": "already_have_tool"},
            "If your current tool already solves the work, staying with it is sensible. The only reason to change is a clear gap in quality, speed, or reliability.",
        ),
        (
            "privacy concern",
            {"buyer_emotion": "skeptical", "objection_type": "privacy", "safety_boundary_detected": True},
            "Privacy is a fair concern. Do not put sensitive material into a tool unless the plan, settings, and your own data rules allow it.",
        ),
        (
            "buyer says I already told you",
            {"buyer_emotion": "frustrated", "buyer_friction_level": "high", "sales_move": "repair", "buyer_said_already_told_you": True},
            "You did say that. You are comparing tools you already use and want the plan choice without repeating the background.",
        ),
        (
            "buyer correction",
            {"buyer_emotion": "neutral", "sales_move": "correction_repair"},
            "Thanks for correcting that. I will use the updated detail and keep the recommendation tied to what you just clarified.",
        ),
        (
            "ASR uncertainty",
            {"buyer_emotion": "neutral", "sales_move": "repair", "asr_uncertainty_detected": True},
            "I may have missed that last part. Could you say the plan or tool name once more?",
        ),
        (
            "buyer asks same question again",
            {"buyer_emotion": "confused", "sales_move": "repeat_answer"},
            "Same answer in simpler terms: Plus fits lighter individual use. Pro fits heavier, more frequent work where limits matter.",
        ),
        (
            "use-case discovery",
            {"buyer_emotion": "neutral", "sales_move": "use_case_discovery"},
            "What will you mainly use it for: writing, coding, research, customer work, or a mix of those?",
        ),
        (
            "intensity discovery",
            {"buyer_emotion": "neutral", "sales_move": "intensity_discovery"},
            "How often do you expect to use it: a few times a week, daily, or for long work sessions?",
        ),
        (
            "team vs individual clarification",
            {"buyer_emotion": "neutral", "sales_move": "team_clarification"},
            "Is this just for you, or do you need something that works for a team?",
        ),
        (
            "recommendation after enough context",
            {"buyer_emotion": "interested", "sales_move": "recommendation", "decision_stage": "recommendation"},
            "Based on what you described, start with Plus if this is mostly personal productivity. Choose Pro only if heavier limits or deeper work are part of the need.",
        ),
        (
            "Plus vs Pro comparison",
            {"buyer_emotion": "curious", "sales_move": "compare_plus_pro"},
            "Plus is the practical individual upgrade. Pro is for heavier use, more demanding tasks, and people who hit limits often.",
        ),
        (
            "Pro tier selection",
            {"buyer_emotion": "interested", "sales_move": "pro_tier_selection"},
            "Pro makes sense if the tool is part of your daily work and limits would slow you down. Otherwise, Plus is the cleaner first step.",
        ),
        (
            "no-fit close",
            {"buyer_emotion": "neutral", "sales_move": "close", "close_readiness": "no_fit"},
            "Then I would not recommend upgrading right now. Staying with your current setup is the better fit.",
        ),
        (
            "terminal acceptance",
            {"buyer_emotion": "interested", "sales_move": "close", "close_readiness": "accepted"},
            "That sounds settled. Plus is the right starting point for your use case.",
        ),
        (
            "boundary no email",
            {"buyer_emotion": "neutral", "safety_boundary_detected": True, "objection_type": "no_email"},
            "Understood. I will not ask for email. We can keep this at the plan comparison level.",
        ),
        (
            "boundary no CRM",
            {"buyer_emotion": "neutral", "safety_boundary_detected": True, "objection_type": "no_crm"},
            "Understood. No CRM step. I will keep the answer focused on the plan choice.",
        ),
        (
            "boundary no calendar",
            {"buyer_emotion": "neutral", "safety_boundary_detected": True, "objection_type": "no_calendar"},
            "Understood. No calendar step. I can summarize the recommendation and stop there.",
        ),
        (
            "source affiliation answer",
            {"buyer_emotion": "skeptical", "sales_move": "source_affiliation_answer", "objection_type": "source_affiliation"},
            "I am not presenting myself as an official representative. Treat this as a plain-language explanation, then verify the final details through the official route.",
        ),
        (
            "opening permission check",
            {"buyer_emotion": "neutral", "sales_move": "opening_permission_check"},
            "Before I compare plans, is it okay if I ask two quick questions about how you plan to use it?",
        ),
        (
            "barge-in recovery",
            {"buyer_emotion": "impatient", "sales_move": "barge_in_recovery"},
            "Got it. I will keep this short. The main choice is light individual use versus heavier daily work.",
        ),
        (
            "buyer frustration",
            {"buyer_emotion": "frustrated", "buyer_friction_level": "high"},
            "I hear the frustration. I will avoid repeating the setup and focus on the decision point.",
        ),
        (
            "buyer disengaged",
            {"buyer_emotion": "disengaged", "buyer_engagement_level": "low"},
            "No problem. The short answer is to stay with the lower plan unless you already know limits are blocking your work.",
        ),
        (
            "buyer interested",
            {"buyer_emotion": "interested", "buyer_engagement_level": "high"},
            "If you are interested in using it regularly, the next useful step is matching the plan to your workload, not just the feature list.",
        ),
        (
            "buyer says not using AI",
            {"buyer_emotion": "neutral", "objection_type": "not_using_ai"},
            "If you are not using AI tools today, start small. Try the basic workflow first before paying for a heavier plan.",
        ),
        (
            "buyer says using ChatGPT and other tools",
            {"buyer_emotion": "skeptical", "objection_type": "using_chatgpt_and_other_tools"},
            "Since you already use several tools, the upgrade should solve a specific gap. If it only duplicates what works, it is not worth it.",
        ),
        (
            "buyer says ChatGPT or maybe Claude",
            {"buyer_emotion": "confused", "objection_type": "chatgpt_or_claude_uncertain"},
            "If you are choosing between tools, decide by the work you do most often. The best option is the one that handles that work reliably.",
        ),
        (
            "buyer asks if plans are models or subscriptions",
            {"buyer_emotion": "confused", "sales_move": "subscription_vs_model"},
            "Think of them as subscriptions, not just model names. The plan changes access, limits, and included capabilities.",
        ),
        (
            "buyer asks signup path",
            {"buyer_emotion": "interested", "sales_move": "signup_path"},
            "Use the official signup flow from the provider. I would avoid third-party links when money or account access is involved.",
        ),
        (
            "buyer asks upgrade path",
            {"buyer_emotion": "interested", "sales_move": "upgrade_path"},
            "The safer path is to start where the fit is clear, then upgrade only when your actual use shows the need.",
        ),
        (
            "buyer asks data privacy training",
            {"buyer_emotion": "skeptical", "sales_move": "privacy_training_answer"},
            "Check the current privacy and data controls before entering sensitive work. If your use is regulated, confirm the rules with your company first.",
        ),
        (
            "wrong product question",
            {"buyer_emotion": "confused", "sales_move": "wrong_product_repair"},
            "That sounds like a different product question. For this comparison, I can only help with the plan choice we have been discussing.",
        ),
        (
            "unsupported claim request",
            {"buyer_emotion": "skeptical", "sales_move": "unsupported_claim"},
            "I cannot make that claim without verified evidence. The safer answer is to compare the published plan differences and avoid promises.",
        ),
        (
            "final goodbye",
            {"buyer_emotion": "neutral", "sales_move": "final_goodbye"},
            "Thanks for the time. I would start with the lower plan and upgrade only if the limits become real.",
        ),
        (
            "API versus ChatGPT boundary",
            {"buyer_emotion": "confused", "sales_move": "api_boundary", "objection_type": "api_vs_chatgpt"},
            "The API and ChatGPT subscriptions are different buying paths. For your case, focus on the consumer plan unless you are building software.",
        ),
        (
            "business enterprise",
            {"buyer_emotion": "interested", "sales_move": "enterprise_recommendation"},
            "If this is for a business team, the individual plans may be the wrong comparison. You should review the business option instead.",
        ),
        (
            "free enough",
            {"buyer_emotion": "neutral", "objection_type": "free_is_enough"},
            "If the free option already handles the work, there is no reason to pay yet. Upgrade when the limitation is specific and recurring.",
        ),
        (
            "too busy",
            {"buyer_emotion": "impatient", "objection_type": "too_busy"},
            "Then keep it simple. Use the current setup now, and revisit the plan only when a real limit blocks work.",
        ),
        (
            "anxious buyer",
            {"buyer_emotion": "anxious", "buyer_friction_level": "medium"},
            "You do not need to decide under pressure. Pick the lowest plan that fits the next month of use.",
        ),
        (
            "curious buyer",
            {"buyer_emotion": "curious", "buyer_engagement_level": "high"},
            "The interesting difference is not just features. It is whether the plan gives enough room for the work you repeat often.",
        ),
        (
            "annoyed buyer",
            {"buyer_emotion": "annoyed", "buyer_friction_level": "high"},
            "I will keep it direct. If this feels like extra complexity, do not upgrade until the need is obvious.",
        ),
        (
            "direct price neutral",
            {"buyer_emotion": "neutral", "sales_move": "price_answer"},
            "Compare price against expected use. Occasional use points lower. Daily demanding work points higher.",
        ),
        (
            "competitor neutral",
            {"buyer_emotion": "neutral", "objection_type": "competitor"},
            "A competitor may be better if it fits your workflow. The plan choice should follow the job you need done.",
        ),
        (
            "source neutral",
            {"buyer_emotion": "neutral", "sales_move": "source_affiliation_answer"},
            "Use this as general guidance, not an official statement. Confirm final prices and terms through the provider.",
        ),
        (
            "plan change",
            {"buyer_emotion": "interested", "sales_move": "upgrade_path", "decision_stage": "plan_change"},
            "Changing plans should follow usage. If the current plan is enough, wait. If limits slow work repeatedly, upgrade.",
        ),
        (
            "team no team",
            {"buyer_emotion": "neutral", "sales_move": "team_clarification", "objection_type": "not_team"},
            "If it is only for you, keep the comparison to individual plans. Team features should not drive the decision.",
        ),
        (
            "plan explain API",
            {"buyer_emotion": "confused", "sales_move": "subscription_vs_model", "objection_type": "api_boundary"},
            "A subscription is for using the product directly. The API is for building software that uses the models.",
        ),
        (
            "low budget no fit",
            {"buyer_emotion": "price_sensitive", "buyer_friction_level": "high", "sales_move": "close", "close_readiness": "no_fit"},
            "With that budget constraint, I would not recommend the higher plan. Stay lower for now.",
        ),
        (
            "close soft",
            {"buyer_emotion": "interested", "sales_move": "close", "close_readiness": "ready"},
            "Given your usage, Plus is the safer first step. Move to Pro only if you hit limits often.",
        ),
        (
            "boundary stop",
            {"buyer_emotion": "annoyed", "safety_boundary_detected": True, "objection_type": "stop"},
            "Understood. I will stop the recommendation here.",
        ),
        (
            "privacy boundary",
            {"buyer_emotion": "anxious", "safety_boundary_detected": True, "objection_type": "privacy"},
            "Understood. Keep sensitive information out unless your privacy settings and internal rules allow it.",
        ),
        (
            "repeat price",
            {"buyer_emotion": "confused", "sales_move": "repeat_answer", "objection_type": "price"},
            "The short version is this: pay only when the free or lower plan blocks recurring work.",
        ),
        (
            "current tool gap",
            {"buyer_emotion": "skeptical", "objection_type": "already_have_tool"},
            "Look for the gap first. If your current tool misses long tasks, reliability, or workflow fit, then compare upgrades.",
        ),
        (
            "source price",
            {"buyer_emotion": "skeptical", "sales_move": "price_answer", "objection_type": "source_affiliation"},
            "For price, verify the current number through the official route. My role here is to help you decide what level fits.",
        ),
        (
            "enterprise security",
            {"buyer_emotion": "skeptical", "sales_move": "enterprise_recommendation", "objection_type": "privacy"},
            "If security controls are central, individual plans may not be enough. Review the business option and your company rules.",
        ),
        (
            "goodbye after no",
            {"buyer_emotion": "neutral", "sales_move": "final_goodbye", "close_readiness": "no_fit"},
            "That is fine. I would leave the upgrade alone for now.",
        ),
    ]


def validation_result(mapped: dict[str, Any]) -> dict[str, Any]:
    warnings = validate_elevenlabs_prosody_mapping(mapped)
    return {
        "status": "pass" if not warnings else "warning",
        "warnings": warnings,
    }


def main() -> int:
    for path in (TAXONOMY_PATH, MAPPING_PATH, RULES_PATH, BACKEND_POLICY_PATH, ELEVENLABS_POLICY_PATH):
        load_json(path)

    examples: list[dict[str, Any]] = []
    for index, (name, context, base_text) in enumerate(example_specs(), start=1):
        context_with_backend = {
            "case_id": f"elevenlabs_mapping.{index:03d}",
            "backend_id": "elevenlabs_existing_provider",
            **context,
        }
        plan = plan_prosody_for_sales_turn(context_with_backend)
        mapped = map_prosody_plan_to_elevenlabs_hints(plan, base_text)
        result = validation_result(mapped)
        example = {
            "example_id": f"elevenlabs_mapping.{index:03d}",
            "input_context": {"name": name, **context_with_backend},
            "base_text": base_text,
            "prosody_plan": plan,
            "shaped_text": mapped["shaped_text"],
            "style_prompt_hint": mapped["style_prompt_hint"],
            "voice_settings_hint": mapped["voice_settings_hint"],
            "pause_punctuation_plan": mapped["pause_punctuation_plan"],
            "emphasis_terms": mapped["emphasis_terms"],
            "safety_warnings": mapped["safety_warnings"],
            "raw_fish_tags_present": mapped["raw_fish_tags_present"],
            "internal_labels_exposed": mapped["internal_labels_exposed"],
            "provider_call_required": mapped["provider_call_required"],
            "live_wiring_allowed": mapped["live_wiring_allowed"],
            "validation_result": result,
        }
        examples.append(example)

    raw_tag_count = sum(1 for item in examples if item["raw_fish_tags_present"])
    internal_label_count = sum(1 for item in examples if item["internal_labels_exposed"])
    provider_required_count = sum(1 for item in examples if item["provider_call_required"])
    live_wiring_count = sum(1 for item in examples if item["live_wiring_allowed"])
    warning_count = sum(1 for item in examples if item["validation_result"]["status"] != "pass")
    result = {
        "experiment_id": "ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001",
        "phase": "4I5",
        "status": "pass" if warning_count == 0 else "warning",
        "example_count": len(examples),
        "examples_count": len(examples),
        "input_files": [
            "runtime/audio_backends/prosody_sales_taxonomy.json",
            "runtime/audio_backends/sales_prosody_mapping.json",
            "runtime/audio_backends/prosody_composition_rules.json",
            "runtime/audio_backends/prosody_backend_mapping_policy.json",
            "runtime/audio_backends/elevenlabs_prosody_mapping_policy.json",
            "runtime/audio_backends/prosody_planner.py",
            "runtime/audio_backends/elevenlabs_prosody_mapper.py",
        ],
        "raw_fish_tag_leakage_count": raw_tag_count,
        "internal_label_leakage_count": internal_label_count,
        "unsafe_instruction_count": 0,
        "provider_call_required_count": provider_required_count,
        "live_wiring_allowed_count": live_wiring_count,
        "provider_call_required": False,
        "live_wiring_allowed": False,
        "provider_calls_made": False,
        "openai_api_calls_made": False,
        "elevenlabs_calls_made": False,
        "live_tts_calls_made": False,
        "fish_inference_performed": False,
        "liquid_inference_performed": False,
        "kokoro_inference_performed": False,
        "local_model_generation_made": False,
        "ollama_generation_made": False,
        "training_performed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False,
        "fish_tags_internal_only": True,
        "raw_fish_tags_allowed_in_elevenlabs_text": False,
        "boundary_flags": base_boundary_flags(),
        "examples": examples,
    }
    write_json(OUTPUT_DIR / "result.json", result)
    write_report(
        OUTPUT_DIR / "report.md",
        "ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001",
        [
            f"Status: {result['status']}",
            f"- Examples: {len(examples)}",
            f"- Raw Fish tag leakage: {raw_tag_count}",
            f"- Internal label leakage: {internal_label_count}",
            f"- Provider calls made: {result['provider_calls_made']}",
            f"- ElevenLabs calls made: {result['elevenlabs_calls_made']}",
            f"- Live TTS calls made: {result['live_tts_calls_made']}",
            f"- Runtime behavior changed: {result['runtime_behavior_changed']}",
            f"- Response text changed: {result['response_text_changed']}",
            "",
            "This prototype creates shaped text and future-review metadata only. It does not call ElevenLabs, generate audio, or wire anything into live runtime.",
        ],
    )
    print(json.dumps({"status": result["status"], "example_count": len(examples), "warnings": warning_count}, indent=2))
    return 0 if raw_tag_count == 0 and internal_label_count == 0 and provider_required_count == 0 and live_wiring_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
