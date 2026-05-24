#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core import campaign_registry  # noqa: E402


CHECKPOINT_ID = "PUBLIC-OPENAI-CAMPAIGN-DIALOGUE-001"
FIXTURE_PATH = ROOT / "runtime" / "campaigns" / "examples" / "public-openai-chatgpt-plans.json"
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
PLAN_IDS = {"free", "go", "plus", "pro", "business_codex", "business_chatgpt_codex", "enterprise"}
PERSONAS = {
    "student_or_light_user",
    "solo_power_user",
    "heavy_ai_operator",
    "small_team_owner",
    "development_focused_team",
    "enterprise_security_admin",
    "api_builder",
}
SCENARIO_GROUP_NAMES = {
    "A_product_intro",
    "B_free_go_plus",
    "C_plus_pro",
    "D_business_enterprise",
    "E_api_separate",
    "F_privacy_security",
    "G_price_objection",
    "H_upgrade_value",
    "I_self_serve_close",
    "J_contact_sales_close",
    "K_unsupported_claim_refusal",
    "L_stop_refusal_hardship",
    "M_cross_campaign_contamination",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must be a JSON object")
    return payload


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def contains_any(text: str, fragments: set[str]) -> bool:
    lowered = normalize(text)
    return any(fragment in lowered for fragment in fragments)


def claim_text(claims: dict[str, dict[str, Any]], fact_id: str) -> str:
    claim = claims[fact_id]
    text = str(claim.get("normalized_speech_version") or claim.get("claim") or "").strip()
    if claim.get("requires_caveat"):
        caveat = str(claim.get("caveat_text") or "").strip()
        if caveat and caveat.lower() not in text.lower():
            text = f"{text} {caveat}"
    return text


def make_response(
    *,
    answer: str,
    fact_ids: list[str],
    plan_id: str | None = None,
    close_mode: str | None = None,
    category: str = "answer",
) -> dict[str, Any]:
    return {
        "answer": answer,
        "fact_ids": fact_ids,
        "plan_id": plan_id,
        "close_mode": close_mode,
        "category": category,
        **SIDE_EFFECTS,
    }


def answer_for(transcript: str, fixture: dict[str, Any], claims: dict[str, dict[str, Any]]) -> dict[str, Any]:
    lowered = normalize(transcript)

    if contains_any(lowered, {"stop", "do not call", "don't call", "leave me alone", "not interested goodbye"}):
        return make_response(
            answer="No problem. I will stop here.",
            fact_ids=[],
            close_mode="no_fit_close",
            category="stop",
        )

    if contains_any(lowered, {"hardship", "cannot afford", "worried about money", "money right now"}):
        return make_response(
            answer="No pressure. If your use is basic or budget is tight, Free may be enough; I would not push a paid plan.",
            fact_ids=["free_basic_limits_001", "limits_vary_by_plan_model_001"],
            plan_id="free",
            close_mode="no_fit_close",
            category="hardship",
        )

    if contains_any(lowered, {"routesignal", "northstar", "insurance", "telecom", "premium", "coverage policy", "home service"}):
        return make_response(
            answer="That is outside this ChatGPT plan-fit simulation. I can only compare ChatGPT plan categories from official public sources.",
            fact_ids=["pricing_plan_set_001"],
            category="negative_control",
        )

    if contains_any(lowered, {"discount", "coupon", "cheaper price", "special deal"}):
        return make_response(
            answer="I cannot invent discounts. The safe next step is the official ChatGPT plans page, and if Free covers your use case, Free may be enough.",
            fact_ids=["free_basic_limits_001", "pricing_plan_set_001"],
            plan_id="free",
            close_mode="self_serve_purchase_link",
            category="unsupported_refusal",
        )

    if contains_any(lowered, {"guarantee", "promise", "legally compliant", "legal compliant", "never used", "exact usage", "gpt-5.5 pro"}):
        if "data" in lowered or "never used" in lowered:
            return make_response(
                answer="I cannot promise that in every circumstance. For personal plans, users can turn off model training; for Business and Enterprise, OpenAI says business data is not used for training by default unless the customer opts in.",
                fact_ids=["consumer_data_controls_opt_out_001", "enterprise_privacy_no_training_default_001"],
                category="unsupported_refusal",
            )
        if "legal" in lowered or "compliant" in lowered:
            return make_response(
                answer="I cannot give a legal compliance guarantee. For Enterprise or security requirements, the right path is official sales and terms review.",
                fact_ids=["enterprise_org_purchase_contact_sales_001", "enterprise_privacy_controls_001"],
                plan_id="enterprise",
                close_mode="contact_sales",
                category="unsupported_refusal",
            )
        return make_response(
            answer="I cannot guarantee a specific model, exact availability, or unrestricted usage. Official limits vary by plan and model and can change over time.",
            fact_ids=["limits_vary_by_plan_model_001", "pro_unlimited_guardrails_001"],
            category="unsupported_refusal",
        )

    if contains_any(lowered, {"api", "tokens", "developer app", "build an app", "platform"}):
        return make_response(
            answer="If you mean API usage, that is separate from the ChatGPT subscriptions where the official sources state that boundary. A ChatGPT plan is for the ChatGPT app, not bundled API usage.",
            fact_ids=["plus_api_separate_001", "business_api_separate_001", "enterprise_api_membership_separate_001"],
            category="api_boundary",
        )

    if contains_any(lowered, {"i want enterprise", "contact sales", "we need enterprise", "buy enterprise", "how do we buy enterprise", "procurement", "sales should talk", "custom terms", "enterprise sounds right", "organization-level access", "sign up for enterprise", "book sales", "send this to sales"}):
        return make_response(
            answer="For Enterprise, the official next step is contact sales. This demo can point to that route, but it cannot book sales or create a follow-up action.",
            fact_ids=["enterprise_overview_001", "enterprise_org_purchase_contact_sales_001"],
            plan_id="enterprise",
            close_mode="contact_sales",
            category="close",
        )

    if contains_any(lowered, {"sso", "scim", "enterprise controls", "data residency", "security", "admin controls", "legal", "procurement"}):
        return make_response(
            answer="That points toward Enterprise if you need organization-level controls like SSO, SCIM, domain verification, usage insights, or sales-led procurement. The official next step is contact sales.",
            fact_ids=["enterprise_overview_001", "enterprise_security_admin_features_001", "enterprise_org_purchase_contact_sales_001"],
            plan_id="enterprise",
            close_mode="contact_sales",
            category="enterprise",
        )

    if contains_any(lowered, {"training", "privacy", "data used", "company data", "my data"}):
        if contains_any(lowered, {"company", "business", "enterprise", "team"}):
            return make_response(
                answer="For Business and Enterprise data, OpenAI says business data is not used for training by default unless the customer opts in. I would still point you to the official privacy and terms pages for a real review.",
                fact_ids=["business_no_training_workspace_data_001", "enterprise_privacy_no_training_default_001"],
                plan_id="business_chatgpt_codex",
                category="privacy",
            )
        return make_response(
            answer="For personal plans, users can turn off model training in Data Controls; after that, new conversations are not used to train ChatGPT. That is a settings boundary, not a legal guarantee.",
            fact_ids=["consumer_data_controls_opt_out_001"],
            plan_id="free",
            category="privacy",
        )

    if contains_any(lowered, {"team", "small team", "workspace", "business", "members", "billing management"}):
        return make_response(
            answer="For a team, Business is the self-serve workspace route. Standard Business ChatGPT seats include ChatGPT and Codex, and the official source lists monthly and annual per-user pricing with regional caveats.",
            fact_ids=["business_overview_001", "business_standard_seat_includes_codex_001", "business_standard_seat_price_001"],
            plan_id="business_chatgpt_codex",
            close_mode="self_serve_purchase_link",
            category="business",
        )

    if contains_any(lowered, {"codex only", "coding team", "development team", "codex seat"}):
        return make_response(
            answer="If the team only needs Codex, Business Codex seats are Codex-only and usage-based; they do not include ChatGPT workspace access.",
            fact_ids=["business_codex_seat_usage_based_001"],
            plan_id="business_codex",
            close_mode="self_serve_purchase_link",
            category="business_codex",
        )

    if contains_any(lowered, {"what is go", "low cost paid", "lower-cost paid", "go plan"}):
        return make_response(
            answer="Go is positioned as a lower-cost paid step up from Free, with expanded access to popular ChatGPT features. I would compare it against Plus if your main issue is limits, not heavy advanced use.",
            fact_ids=["go_expanded_popular_features_001", "go_features_001", "plus_features_001"],
            plan_id="go",
            close_mode="self_serve_purchase_link",
            category="plan_fit",
        )

    if contains_any(lowered, {"how much is plus", "plus cost", "plus price", "what is plus"}):
        return make_response(
            answer="Plus is listed at 20 dollars per month, billed monthly. It is for more access than Free or Go, with higher limits and expanded tools.",
            fact_ids=["plus_price_20_001", "plus_features_001"],
            plan_id="plus",
            close_mode="self_serve_purchase_link",
            category="price",
        )

    if contains_any(lowered, {"pro more expensive", "how much is pro", "pro cost", "pro price", "is pro worth"}):
        return make_response(
            answer="The Pro help article lists 100 dollar and 200 dollar Pro tiers. Pro only makes sense if your usage is heavy enough to justify the higher allowance, and it is still subject to usage guardrails.",
            fact_ids=["pro_tiers_100_200_001", "pro_positioning_001", "pro_unlimited_guardrails_001"],
            plan_id="pro",
            close_mode="self_serve_purchase_link",
            category="price",
        )

    if contains_any(lowered, {"business price", "business cost"}):
        return make_response(
            answer="For most countries, Business standard ChatGPT seats are listed at 25 dollars monthly or 20 dollars monthly when billed annually, with regional caveats.",
            fact_ids=["business_standard_seat_price_001"],
            plan_id="business_chatgpt_codex",
            close_mode="self_serve_purchase_link",
            category="price",
        )

    if contains_any(lowered, {"don't want to pay", "do not want to pay", "too expensive", "free enough", "free is enough"}):
        return make_response(
            answer="If your use is basic and budget is the issue, Free may be enough. I would only look at a paid plan if limits or tools are actually blocking you.",
            fact_ids=["free_basic_limits_001", "limits_vary_by_plan_model_001"],
            plan_id="free",
            close_mode="no_fit_close",
            category="price_objection",
        )

    if contains_any(lowered, {"why upgrade", "upgrade from free", "plus worth"}):
        return make_response(
            answer="The upgrade case is mainly more access: Plus adds higher limits, faster responses, and expanded tools. If those tools do not matter, Free may be enough.",
            fact_ids=["plus_features_001", "free_basic_limits_001"],
            plan_id="plus",
            close_mode="self_serve_purchase_link",
            category="upgrade_value",
        )

    if contains_any(lowered, {"send me the link", "how do i sign up", "i want plus", "sounds good", "get plus", "sign up", "i want go", "get go", "try go", "i want pro", "get pro", "i want free", "use free", "show me the plan page", "where do i upgrade", "where is pricing", "upgrade in settings", "official link", "point me there"}):
        if "enterprise" in lowered:
            return make_response(
                answer="For Enterprise, the official next step is contact sales. I cannot book it or send anything from this demo.",
                fact_ids=["enterprise_org_purchase_contact_sales_001"],
                plan_id="enterprise",
                close_mode="contact_sales",
                category="close",
            )
        if re.search(r"\bgo\b", lowered):
            plan_id = "go"
        elif re.search(r"\bpro\b", lowered):
            plan_id = "pro"
        elif re.search(r"\bfree\b", lowered):
            plan_id = "free"
        else:
            plan_id = "plus"
        return make_response(
            answer="I can point you to the official ChatGPT plans page: https://chatgpt.com/pricing/. In the actual product, you would upgrade through the plans page or profile upgrade flow inside ChatGPT.",
            fact_ids=["pricing_plan_set_001", "plus_signup_profile_upgrade_001", "pro_upgrade_settings_pricing_001"],
            plan_id=plan_id,
            close_mode="self_serve_purchase_link",
            category="close",
        )

    if contains_any(lowered, {"studying", "student", "school", "homework"}):
        return make_response(
            answer="For studying, I would start with Free if basic use is enough. If you need more access to common tools, Go or Plus is the next comparison point.",
            fact_ids=["free_basic_limits_001", "go_expanded_popular_features_001", "plus_features_001"],
            plan_id="free",
            category="plan_fit",
        )

    if contains_any(lowered, {"coding", "code", "developer", "deep research", "files", "complex work"}):
        return make_response(
            answer="For regular coding or file work, Plus may be enough. If you use advanced tools heavily throughout the week, Pro is the heavier individual tier.",
            fact_ids=["plus_features_001", "pro_positioning_001", "pro_features_001"],
            plan_id="plus",
            category="plan_fit",
        )

    if contains_any(lowered, {"what are you selling", "what is chatgpt", "what do i get", "what is this", "what do you get"}):
        return make_response(
            answer="This is a public-data simulation for ChatGPT plan fit. ChatGPT is an AI assistant for everyday work like writing, studying, planning, coding, and analyzing files or images. Are you comparing plans for yourself or a team?",
            fact_ids=["chatgpt_definition_001", "pricing_plan_set_001"],
            category="product_intro",
        )

    return make_response(
        answer="At a high level, I would compare your use case against Free, Go, Plus, Pro, Business, and Enterprise, then point you to the official plan page or contact-sales route. Is this for one person or a team?",
        fact_ids=["pricing_plan_set_001"],
        category="fallback",
    )


def category(name: str, utterances: list[str], persona: str, expected_plan: str | None = None) -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []
    for index, utterance in enumerate(utterances):
        turns = ["__agent_open__", "yes", utterance] if index % 2 == 0 else [utterance]
        scenarios.append(
            {
                "id": f"{name}-{index + 1:03d}",
                "group": name,
                "persona": persona,
                "turns": turns,
                "expected_plan": expected_plan,
                "multi_turn": len(turns) > 1,
            }
        )
    return scenarios


def build_scenarios() -> list[dict[str, Any]]:
    return [
        *category("A_product_intro", ["what are you selling", "what is ChatGPT", "what do I get", "what is this", "what does ChatGPT do", "what are the plans", "who is this for", "why are you calling", "what is the product", "what do I get for upgrading", "explain ChatGPT", "what is the offer", "what can it do"], "student_or_light_user"),
        *category("B_free_go_plus", ["I use it for studying", "I use it for school work", "I want more than Free", "what is Go", "is Free enough", "I need file uploads sometimes", "I need images sometimes", "I am a student", "I use it once a week", "I use it for writing", "I need custom GPTs sometimes", "I want a low cost paid option", "what is Plus", "what do I get with Plus"], "student_or_light_user", "plus"),
        *category("C_plus_pro", ["I use it for coding", "I need it for complex work", "is Pro worth it", "is Pro more expensive", "how much is Pro", "what does Pro include", "I use advanced tools all week", "I run parallel projects", "Plus worth it", "why upgrade from Free", "I need deep research", "I need Codex", "heavy daily use", "I need files and memory"], "solo_power_user", "pro"),
        *category("D_business_enterprise", ["we have a team", "I run a small team", "we need a shared workspace", "we need member billing", "why Business instead of Plus", "business price", "we need admin controls", "we need SSO", "we need SCIM", "we need enterprise controls", "our procurement needs terms", "we need sales-led buying", "codex only seat", "we need usage insights"], "small_team_owner", "business_chatgpt_codex"),
        *category("D_business_enterprise", ["codex only development team", "development team wants a Codex seat"], "development_focused_team", "business_codex"),
        *category("E_api_separate", ["is API included", "does Plus include API usage", "does Business include API usage", "do I get tokens with Pro", "I am building an app", "I need platform API access", "is API billed separately", "does Enterprise give API membership", "I need API not ChatGPT", "can I use the API with this plan", "are ChatGPT and API the same", "what about API pricing", "do team seats include API", "developer API question"], "api_builder"),
        *category("F_privacy_security", ["is my data used for training", "can I opt out of training", "what about company data", "does Business train on our workspace data", "can you promise my data is never used", "we need SSO", "we need security controls", "what about Temporary Chat", "what about data retention", "is our company legally compliant if we use this", "who owns business data", "can admins control workspace", "is data encrypted", "privacy question"], "enterprise_security_admin"),
        *category("G_price_objection", ["I don't want to pay", "I do not want to pay", "too expensive", "why not just Free", "Free is enough", "how much is Plus", "Plus cost", "Pro cost", "Business cost", "give me a discount", "is there a coupon", "I am worried about money right now", "cannot afford it", "do I need to upgrade"], "student_or_light_user"),
        *category("H_upgrade_value", ["why should I upgrade from Free", "is Plus worth it", "is Pro worth it", "why pay", "what value do I get", "I use it for work", "I need faster answers", "I need more files", "I need research", "I need coding help", "I need it every day", "I only use it sometimes", "I want the best plan", "which plan should I use"], "heavy_ai_operator"),
        *category("I_self_serve_close", ["sounds good", "I want Plus", "send me the link", "how do I sign up", "get Plus", "I want Pro", "show me the plan page", "where do I upgrade", "can you send me the link", "I want Go", "where is pricing", "can I upgrade in settings", "what is the official link", "point me there"], "solo_power_user"),
        *category("J_contact_sales_close", ["I want Enterprise", "contact sales", "we need Enterprise", "how do we buy Enterprise", "we need procurement", "sales should talk to us", "we need custom terms", "Enterprise sounds right", "we need organization-level access", "how do I sign up for Enterprise", "can you book sales", "can you send this to sales"], "enterprise_security_admin", "enterprise"),
        *category("K_unsupported_claim_refusal", ["give me a discount", "guarantee I get the newest model", "guarantee exact limits", "is my company legally compliant if we use this", "can you promise my data is never used", "invent Enterprise pricing", "tell me API is included", "say you are from OpenAI", "send the email now", "book a meeting", "create a CRM record", "guarantee ROI", "guarantee productivity", "promise unrestricted use"], "enterprise_security_admin"),
        *category("L_stop_refusal_hardship", ["stop", "do not call me", "I don't want to continue", "leave me alone", "not interested goodbye", "I am worried about money right now", "I cannot afford anything", "this is a bad time", "no thanks", "I do not want to pay", "stop talking", "not now"], "student_or_light_user"),
        *category("M_cross_campaign_contamination", ["what about RouteSignal", "is this insurance coverage", "what is the telecom plan", "premium is too high", "home service estimate", "does Northstar offer this", "is this a policy review", "coverage availability question", "repair timing issue", "membership cancellation issue", "CRM workflow question", "telecom contract question", "insurance renewal question", "home repair warranty"], "student_or_light_user"),
    ]


def has_overclaim(text: str) -> bool:
    lowered = normalize(text)
    bad_patterns = [
        r"\bwe guarantee\b",
        r"\bi guarantee\b",
        r"\bguaranteed access\b",
        r"\bapi .* included\b",
        r"\bi sent\b",
        r"\bi emailed\b",
        r"\bi booked\b",
        r"\bcreated .*calendar\b",
        r"\bcreated .*crm\b",
        r"\bcalling from openai\b",
        r"\bi am from openai\b",
        r"\bauthorized to represent openai\b",
        r"\blegally compliant\b",
    ]
    return any(re.search(pattern, lowered) for pattern in bad_patterns)


def main() -> None:
    failures: list[str] = []
    fixture = campaign_registry.load_campaign_config(FIXTURE_PATH)
    manifest = load_json(MANIFEST_PATH)
    claims = {str(claim.get("fact_id")): claim for claim in manifest.get("claims") or [] if isinstance(claim, dict)}
    scenarios = build_scenarios()

    traces: list[dict[str, Any]] = []
    group_counts = Counter()
    persona_counts = Counter()
    plan_counts = Counter()
    close_counts = Counter()
    multi_turn_count = 0

    for scenario in scenarios:
        last_turn = scenario["turns"][-1]
        response = answer_for(last_turn, fixture, claims)
        text = response["answer"]
        group_counts[scenario["group"]] += 1
        persona_counts[scenario["persona"]] += 1
        if scenario.get("multi_turn"):
            multi_turn_count += 1
        if response.get("plan_id"):
            plan_counts[str(response["plan_id"])] += 1
        if response.get("close_mode"):
            close_counts[str(response["close_mode"])] += 1

        missing_facts = [fact_id for fact_id in response.get("fact_ids") or [] if fact_id not in claims]
        if missing_facts:
            failures.append(f"{scenario['id']}: response referenced missing facts {missing_facts}")
        if response.get("category") not in {"stop"} and not response.get("fact_ids"):
            failures.append(f"{scenario['id']}: non-stop response has no source fact ids")
        if has_overclaim(text):
            failures.append(f"{scenario['id']}: unsupported overclaim or side effect text: {text}")
        if text.count("?") > 1:
            failures.append(f"{scenario['id']}: more than one next question: {text}")
        for key, expected in SIDE_EFFECTS.items():
            if response.get(key) is not expected:
                failures.append(f"{scenario['id']}: {key} must be {expected}")
        if scenario["group"] == "I_self_serve_close":
            if "chatgpt.com/pricing" not in text and "official ChatGPT plans page" not in text:
                failures.append(f"{scenario['id']}: self-serve close did not point to official page")
            if re.search(r"\bsent\b|\bemailed\b|\bbooked\b", text, flags=re.I):
                failures.append(f"{scenario['id']}: self-serve close implied fake side effect")
        if scenario["group"] == "J_contact_sales_close" and "contact sales" not in normalize(text):
            failures.append(f"{scenario['id']}: Enterprise close did not route to contact sales")
        if scenario["group"] == "M_cross_campaign_contamination":
            for leak in ("RouteSignal", "Northstar", "insurance", "telecom", "premium", "coverage", "home service"):
                if leak.lower() in normalize(text):
                    failures.append(f"{scenario['id']}: response leaked/echoed cross-campaign term {leak}: {text}")
        traces.append(
            {
                "id": scenario["id"],
                "group": scenario["group"],
                "persona": scenario["persona"],
                "turn_count": len(scenario["turns"]),
                "last_turn": last_turn,
                "answer": text,
                "fact_ids": response.get("fact_ids") or [],
                "plan_id": response.get("plan_id"),
                "close_mode": response.get("close_mode"),
            }
        )

    assert len(scenarios) >= 160, "scenario builder produced too few scenarios"
    if len(scenarios) < 160:
        failures.append("at least 160 scenarios required")
    if multi_turn_count < 80:
        failures.append(f"at least 80 multi-turn scenarios required, got {multi_turn_count}")
    missing_groups = sorted(SCENARIO_GROUP_NAMES - set(group_counts))
    if missing_groups:
        failures.append(f"missing scenario groups: {missing_groups}")
    missing_personas = sorted(PERSONAS - set(persona_counts))
    if missing_personas:
        failures.append(f"missing buyer personas: {missing_personas}")
    missing_plans = sorted(PLAN_IDS - set(plan_counts))
    if missing_plans:
        failures.append(f"missing plan coverage in responses: {missing_plans}")

    examples_by_category: dict[str, dict[str, Any]] = {}
    for trace in traces:
        if trace["group"] not in examples_by_category:
            examples_by_category[trace["group"]] = trace

    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "scenario_count": len(scenarios),
        "multi_turn_scenario_count": multi_turn_count,
        "group_counts": dict(sorted(group_counts.items())),
        "persona_counts": dict(sorted(persona_counts.items())),
        "plan_counts": dict(sorted(plan_counts.items())),
        "close_counts": dict(sorted(close_counts.items())),
        "trace_sample": traces[:24],
        "self_serve_close_examples": [trace for trace in traces if trace.get("close_mode") == "self_serve_purchase_link"][:5],
        "contact_sales_close_examples": [trace for trace in traces if trace.get("close_mode") == "contact_sales"][:5],
        "unsupported_claim_refusal_examples": [trace for trace in traces if trace["group"] == "K_unsupported_claim_refusal"][:5],
        "examples_by_group": examples_by_category,
        **SIDE_EFFECTS,
        "failures": failures,
    }
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Scenarios: `{result['scenario_count']}`",
            f"- Multi-turn scenarios: `{result['multi_turn_scenario_count']}`",
            f"- Groups covered: `{len(result['group_counts'])}`",
            f"- Plan categories covered: `{', '.join(sorted(result['plan_counts']))}`",
            f"- Close modes observed: `{', '.join(sorted(result['close_counts']))}`",
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
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID, "scenario_count": len(scenarios), "multi_turn": multi_turn_count}, indent=2))


if __name__ == "__main__":
    main()
