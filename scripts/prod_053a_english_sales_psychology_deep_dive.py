#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-053A-english-sales-psychology-deep-dive"
CHECKPOINT_NAME = "English Sales Psychology Deep Dive"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
CHECKED_DATE = "2026-05-15"

BOUNDARY_FLAGS = {
    "runtime_behavior_changed": False,
    "response_text_behavior_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_judging_used": False,
    "private_data_read": False,
    "source_excerpt_text_stored": False,
    "copied_scripts_stored": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
}

SOURCE_REGISTER = [
    {
        "source_id": "prod053a-source-001",
        "title": "Franke and Park adaptive selling/customer orientation meta-analysis",
        "url": "https://journals.sagepub.com/doi/10.1509/jmkr.43.4.693",
        "source_type": "academic sales meta-analysis",
        "evidence_weight": "high",
        "usefulness": "Adaptive selling improves performance only when the seller can recognize the situation and alter the approach.",
    },
    {
        "source_id": "prod053a-source-002",
        "title": "Adaptive selling integrative framework",
        "url": "https://link.springer.com/article/10.1007/s11747-025-01096-3",
        "source_type": "open academic sales review",
        "evidence_weight": "high",
        "usefulness": "A useful agent needs situation categories plus a small strategy library, not one universal script.",
    },
    {
        "source_id": "prod053a-source-003",
        "title": "Salesperson listening meta-analysis",
        "url": "https://www.sciencedirect.com/science/article/abs/pii/S0148296319303017",
        "source_type": "academic sales listening meta-analysis",
        "evidence_weight": "high",
        "usefulness": "Listening supports trust, satisfaction, loyalty, adaptive selling, and relationship outcomes.",
    },
    {
        "source_id": "prod053a-source-004",
        "title": "Perceived listening work-outcomes meta-analysis",
        "url": "https://link.springer.com/article/10.1007/s10869-023-09897-5",
        "source_type": "open academic listening meta-analysis",
        "evidence_weight": "high",
        "usefulness": "Listening is most strongly tied to relationship outcomes such as trust and satisfaction.",
    },
    {
        "source_id": "prod053a-source-005",
        "title": "Gartner Challenger Sales Model overview",
        "url": "https://www.gartner.com/smarterwithgartner/power-challenger-sales-model",
        "source_type": "industry sales methodology research",
        "evidence_weight": "medium",
        "usefulness": "Useful selling can teach one relevant reframe before pitching, but only if claims are campaign-supported.",
    },
    {
        "source_id": "prod053a-source-006",
        "title": "Gartner modern B2B buyers and information overload",
        "url": "https://www.gartner.com/smarterwithgartner/what-sales-should-know-about-modern-b2b-buyers",
        "source_type": "industry buyer research",
        "evidence_weight": "medium",
        "usefulness": "Buyers often struggle to buy because of complexity, information overload, and internal change risk.",
    },
    {
        "source_id": "prod053a-source-007",
        "title": "HBR customer indecision and no-decision sales losses",
        "url": "https://hbr.org/2022/06/stop-losing-sales-to-customer-indecision",
        "source_type": "industry sales research article",
        "evidence_weight": "medium",
        "usefulness": "No decision is often a risk/confidence problem, so the agent should lower perceived risk without pressuring.",
    },
    {
        "source_id": "prod053a-source-008",
        "title": "Bain B2B Elements of Value",
        "url": "https://www.bain.com/insights/the-b2b-elements-of-value-hbr",
        "source_type": "buyer value framework",
        "evidence_weight": "medium",
        "usefulness": "B2B buyers still have personal concerns such as reputation, risk reduction, and anxiety reduction.",
    },
    {
        "source_id": "prod053a-source-009",
        "title": "Mayer, Davis, and Schoorman organizational trust model",
        "url": "https://www.jstor.org/stable/258792",
        "source_type": "academic trust model",
        "evidence_weight": "high",
        "usefulness": "Trust objections should be separated into ability, benevolence, and integrity gaps.",
    },
    {
        "source_id": "prod053a-source-010",
        "title": "NCBI Bookshelf motivational interviewing chapter",
        "url": "https://www.ncbi.nlm.nih.gov/books/NBK571068/",
        "source_type": "public clinical communication guidance",
        "evidence_weight": "high",
        "usefulness": "Open questions, affirmations, reflections, and summaries help show understanding without forcing agreement.",
    },
    {
        "source_id": "prod053a-source-011",
        "title": "Empathy in motivational interviewing and language synchrony",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC5018199/",
        "source_type": "open academic communication research",
        "evidence_weight": "high",
        "usefulness": "Simple reflection can repeat or rephrase, but empathy is broader than parroting customer words.",
    },
    {
        "source_id": "prod053a-source-012",
        "title": "Frontiers reactance and persuasive communication review",
        "url": "https://www.frontiersin.org/journals/communication/articles/10.3389/fcomm.2019.00056/full",
        "source_type": "open academic communication review",
        "evidence_weight": "high",
        "usefulness": "Controlling language can trigger resistance; preserve real choice when recommending next steps.",
    },
    {
        "source_id": "prod053a-source-013",
        "title": "Ryan and Deci self-determination theory",
        "url": "https://digitalwellbeing.org/wp-content/uploads/2020/03/Ryan-and-Deci-2000-Self-Determination-Theory-and-the-Facilitation-of-Intrinsic-Motivation-Social-Development-and-Well-Being.pdf",
        "source_type": "academic motivation theory",
        "evidence_weight": "high",
        "usefulness": "Autonomy, competence, and relatedness are useful filters for sales wording; pressure undermines autonomy.",
    },
    {
        "source_id": "prod053a-source-014",
        "title": "Leader autonomy support meta-analysis",
        "url": "https://link.springer.com/article/10.1007/s11031-018-9698-y",
        "source_type": "open academic motivation meta-analysis",
        "evidence_weight": "high",
        "usefulness": "Autonomy support uses perspective-taking, choice, and informational rather than controlling language.",
    },
    {
        "source_id": "prod053a-source-015",
        "title": "Stanford Fogg Behavior Model",
        "url": "https://behaviordesign.stanford.edu/resources/fogg-behavior-model",
        "source_type": "behavior design framework",
        "evidence_weight": "medium",
        "usefulness": "When action does not happen, motivation, ability, or prompt may be missing; do not treat all hesitation as resistance.",
    },
    {
        "source_id": "prod053a-source-016",
        "title": "COM-B behaviour change wheel",
        "url": "https://implementationscience.biomedcentral.com/articles/10.1186/1748-5908-6-42",
        "source_type": "open academic behavior-change framework",
        "evidence_weight": "high",
        "usefulness": "Classify friction as capability, opportunity, or motivation before choosing a response.",
    },
    {
        "source_id": "prod053a-source-017",
        "title": "Oxford conversation analysis overview",
        "url": "https://academic.oup.com/edited-volume/61882/chapter/547683169",
        "source_type": "academic conversation analysis",
        "evidence_weight": "high",
        "usefulness": "Partial repeats and targeted question words can locate a specific trouble source in a prior turn.",
    },
    {
        "source_id": "prod053a-source-018",
        "title": "Repair as interface between interaction and cognition",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6849777/",
        "source_type": "open academic conversation repair review",
        "evidence_weight": "high",
        "usefulness": "Repair practices help resolve trouble in speaking, hearing, and understanding before continuing.",
    },
    {
        "source_id": "prod053a-source-019",
        "title": "Amazon Alexa design principle: Be brief",
        "url": "https://developer.amazon.com/en-US/alexa/alexa-haus/design-principles/be-brief",
        "source_type": "voice UX design guidance",
        "evidence_weight": "medium",
        "usefulness": "Spoken agents should be brief, active, simple, and low-friction to avoid cognitive load.",
    },
    {
        "source_id": "prod053a-source-020",
        "title": "Google conversation design quick reference",
        "url": "https://developers.google.com/assistant/downloads/design-principles-quick-reference.pdf",
        "source_type": "voice UX design guidance",
        "evidence_weight": "medium",
        "usefulness": "After asking a question, stop speaking and let the user answer.",
    },
    {
        "source_id": "prod053a-source-021",
        "title": "Digital.gov clear and short plain-language guide",
        "url": "https://digital.gov/guides/plain-language/writing/clear-short",
        "source_type": "public communication guidance",
        "evidence_weight": "medium",
        "usefulness": "Use short sentences and one idea per sentence.",
    },
    {
        "source_id": "prod053a-source-022",
        "title": "CDC plain language checklist",
        "url": "https://www.cdc.gov/health-literacy/php/develop-materials/plain-language.html",
        "source_type": "public communication guidance",
        "evidence_weight": "medium",
        "usefulness": "Plain language should be understandable the first time people hear it.",
    },
    {
        "source_id": "prod053a-source-023",
        "title": "NIH plain language guide",
        "url": "https://www.nih.gov/sites/default/files/2025-02/nih-plain-language-getting-started-brushing-up.pdf",
        "source_type": "public communication guidance",
        "evidence_weight": "medium",
        "usefulness": "Remove padding, stay direct, and keep one idea per sentence.",
    },
    {
        "source_id": "prod053a-source-024",
        "title": "Samuelson and Zeckhauser status quo bias",
        "url": "https://rzeckhauser.scholars.harvard.edu/publications/status-quo-bias-decision-making",
        "source_type": "academic decision psychology",
        "evidence_weight": "high",
        "usefulness": "Doing nothing is a powerful default; make review steps feel reversible and low-risk.",
    },
    {
        "source_id": "prod053a-source-025",
        "title": "Iyengar and Lepper choice overload",
        "url": "https://pubmed.ncbi.nlm.nih.gov/11138768/",
        "source_type": "academic decision psychology",
        "evidence_weight": "high",
        "usefulness": "Too many options can reduce action; offer one or two next-step paths, not a menu.",
    },
    {
        "source_id": "prod053a-source-026",
        "title": "Harvard Program on Negotiation BATNA explainer",
        "url": "https://www.pon.harvard.edu/daily/batna/translate-your-batna-to-the-current-deal/",
        "source_type": "negotiation education source",
        "evidence_weight": "medium",
        "usefulness": "A good sales next step should leave the buyer's no-deal alternative visible instead of hiding it.",
    },
]

TOPIC_FINDINGS = [
    {
        "finding_id": "prod053a-finding-001",
        "topic": "adaptive_selling",
        "source_ids": ["prod053a-source-001", "prod053a-source-002"],
        "finding": "Useful adaptation needs situation recognition, confidence to alter the approach, a strategy library, and feedback from the interaction.",
        "agent_use": "Classify the customer move first, then pick one small response pattern. Do not use one universal objection script.",
        "avoid": "Do not infer personality or hidden emotion to choose a strategy.",
        "runtime_value": "high",
    },
    {
        "finding_id": "prod053a-finding-002",
        "topic": "listening_and_trust",
        "source_ids": ["prod053a-source-003", "prod053a-source-004", "prod053a-source-010", "prod053a-source-011"],
        "finding": "Listening and reflective responses are trust-building behaviors, but reflection is not the same as repeating everything the customer said.",
        "agent_use": "Use a short acknowledgement or one targeted reflection before answering. Mirror only a short phrase when it helps repair or invites elaboration.",
        "avoid": "Do not echo full customer categories such as boss, manager, spouse, and partner in every response.",
        "runtime_value": "high",
    },
    {
        "finding_id": "prod053a-finding-003",
        "topic": "buyer_confidence",
        "source_ids": ["prod053a-source-006", "prod053a-source-007", "prod053a-source-024", "prod053a-source-025"],
        "finding": "Many stalled sales are not lost to a competitor; they stall because the buyer is overloaded, uncertain, or safer doing nothing.",
        "agent_use": "Reduce decision load and risk. Preserve relief language, but say it like a person: no commitment today; take a look and let me know.",
        "avoid": "Do not answer an uncertain buyer by adding more facts, more options, or a bigger commitment ask.",
        "runtime_value": "high",
    },
    {
        "finding_id": "prod053a-finding-004",
        "topic": "autonomy_and_reactance",
        "source_ids": ["prod053a-source-012", "prod053a-source-013", "prod053a-source-014", "prod053a-source-026"],
        "finding": "People resist persuasive messages when they feel their freedom is being threatened or the next step is a hidden commitment.",
        "agent_use": "Use real choices and explicit permission. Keep the buyer's ability to pause, compare, decline, or ask for a human visible.",
        "avoid": "Do not use must, have to, obviously, last chance, or false-choice closes.",
        "runtime_value": "high",
    },
    {
        "finding_id": "prod053a-finding-005",
        "topic": "behavior_friction",
        "source_ids": ["prod053a-source-015", "prod053a-source-016"],
        "finding": "A hesitation can come from missing motivation, ability/capability, opportunity/context, or timing.",
        "agent_use": "When the customer hesitates, lower friction or ask a tiny clarifier before proposing the next step.",
        "avoid": "Do not treat every hesitation as a closeable objection or pressure problem.",
        "runtime_value": "high",
    },
    {
        "finding_id": "prod053a-finding-006",
        "topic": "trust_repair",
        "source_ids": ["prod053a-source-008", "prod053a-source-009"],
        "finding": "Trust concerns are not all the same: the buyer may question competence, whether the offer is in their interest, or whether the claim is honest.",
        "agent_use": "Answer the trust gap that is actually present: proof for ability, low-pressure fit for benevolence, limits and verification for integrity.",
        "avoid": "Do not use testimonials, confidence, or reassurance as a universal trust answer.",
        "runtime_value": "high",
    },
    {
        "finding_id": "prod053a-finding-007",
        "topic": "conversation_repair",
        "source_ids": ["prod053a-source-017", "prod053a-source-018"],
        "finding": "Conversation repair should identify a specific trouble source instead of restarting the whole pitch.",
        "agent_use": "Use short repair moves such as 'the setup part?' or 'what changed?' only when the customer meaning is unclear.",
        "avoid": "Do not ask broad discovery questions after the customer already gave enough detail.",
        "runtime_value": "medium",
    },
    {
        "finding_id": "prod053a-finding-008",
        "topic": "spoken_brevity",
        "source_ids": ["prod053a-source-019", "prod053a-source-020", "prod053a-source-021", "prod053a-source-022", "prod053a-source-023"],
        "finding": "Live spoken agents should use short, active, simple turns with one idea per sentence and should stop after asking a question.",
        "agent_use": "Keep most English sales turns to one or two breaths: acknowledgement, answer, relief or next step, stop.",
        "avoid": "Do not stack policy explanations, product facts, social proof, and a question in one turn.",
        "runtime_value": "high",
    },
    {
        "finding_id": "prod053a-finding-009",
        "topic": "ethical_insight",
        "source_ids": ["prod053a-source-005", "prod053a-source-008", "prod053a-source-026"],
        "finding": "Insight-led selling is useful when it helps the buyer understand the situation, not when it manufactures urgency or pain.",
        "agent_use": "Offer one campaign-supported reframe only after a direct factual answer or when the buyer asks why this matters.",
        "avoid": "Do not use fear, scarcity, invented benchmark claims, or emotional manipulation.",
        "runtime_value": "medium",
    },
]

COMPACT_CANDIDATE_RULES = [
    {
        "rule_id": "english_psych_001_listen_answer_then_continue",
        "name": "Listen, answer, then continue.",
        "rule": "Start with a tiny acknowledgement, answer the customer move, then offer one low-friction next step.",
        "example_good": "Of course. I can send it over. No commitment today. Take a look and let me know.",
        "example_bad": "I can send a summary for your manager or spouse and there is no decision or commitment required from you today.",
        "source_finding_ids": ["prod053a-finding-002", "prod053a-finding-008"],
        "runtime_cost": "low",
        "promotion_readiness": "candidate_for_prod_053b_review",
    },
    {
        "rule_id": "english_psych_002_relief_without_policy_dump",
        "name": "Keep relief, remove policy tone.",
        "rule": "If a safety or pressure boundary matters, say the relief plainly and briefly instead of explaining the whole policy.",
        "example_good": "No commitment today. Just take a look and let me know.",
        "example_bad": "There is no decision, no payment, no commitment, and no binding agreement required from you on this call.",
        "source_finding_ids": ["prod053a-finding-003", "prod053a-finding-008"],
        "runtime_cost": "low",
        "promotion_readiness": "candidate_for_prod_053b_review",
    },
    {
        "rule_id": "english_psych_003_mirror_only_for_repair_or_discovery",
        "name": "Mirror only when it does work.",
        "rule": "Use a short partial repeat only to show listening, repair ambiguity, or invite elaboration; otherwise do not repeat the customer's category.",
        "example_good": "Your boss? Got it. What would they care about most, price or setup?",
        "example_bad": "Of course, I can send a short summary for your boss so your boss can review it.",
        "source_finding_ids": ["prod053a-finding-002", "prod053a-finding-007"],
        "runtime_cost": "low",
        "promotion_readiness": "candidate_for_prod_053b_review",
    },
    {
        "rule_id": "english_psych_004_one_small_decision",
        "name": "One small decision per turn.",
        "rule": "When the buyer is uncertain, ask for or offer only one small next step instead of asking them to process the whole sale.",
        "example_good": "I can keep it simple and send the two main points first.",
        "example_bad": "I can send the summary, explain pricing, compare options, book a call, and include the contract terms.",
        "source_finding_ids": ["prod053a-finding-003", "prod053a-finding-008"],
        "runtime_cost": "low",
        "promotion_readiness": "candidate_for_prod_053b_review",
    },
    {
        "rule_id": "english_psych_005_diagnose_friction_not_personality",
        "name": "Diagnose friction, not personality.",
        "rule": "Treat hesitation as possible relevance, ability, authority, risk, or timing friction; never label the buyer's personality or hidden emotion.",
        "example_good": "Is the main thing price, timing, or who needs to review it?",
        "example_bad": "It sounds like you are anxious about deciding.",
        "source_finding_ids": ["prod053a-finding-001", "prod053a-finding-005"],
        "runtime_cost": "low",
        "promotion_readiness": "candidate_for_prod_053b_review",
    },
    {
        "rule_id": "english_psych_006_autonomy_visible",
        "name": "Make autonomy visible.",
        "rule": "Use real options and make pause, review, decline, or human handoff acceptable outcomes.",
        "example_good": "We can leave it there for today, or I can send the short version.",
        "example_bad": "You should at least book the next call so you do not miss the opportunity.",
        "source_finding_ids": ["prod053a-finding-004"],
        "runtime_cost": "low",
        "promotion_readiness": "candidate_for_prod_053b_review",
    },
    {
        "rule_id": "english_psych_007_trust_gap_specific",
        "name": "Answer the specific trust gap.",
        "rule": "For trust concerns, identify whether the gap is ability, interest, or honesty, and answer only that gap.",
        "example_good": "I do not want to overclaim that. I can send what is verified, and a specialist can cover the technical part.",
        "example_bad": "You can trust us; many people are happy with it.",
        "source_finding_ids": ["prod053a-finding-006"],
        "runtime_cost": "low",
        "promotion_readiness": "candidate_for_prod_053b_review",
    },
    {
        "rule_id": "english_psych_008_stop_after_question",
        "name": "Ask, then stop.",
        "rule": "If the agent asks a question, it should not add another explanation after the question.",
        "example_good": "What would be most useful in the summary?",
        "example_bad": "What would be most useful in the summary? I can include pricing, terms, setup, and next steps if that helps.",
        "source_finding_ids": ["prod053a-finding-008"],
        "runtime_cost": "low",
        "promotion_readiness": "candidate_for_prod_053b_review",
    },
]

REJECTED_OR_DEFERRED_TACTICS = [
    {
        "tactic_id": "prod053a-reject-001",
        "name": "False scarcity or fake urgency",
        "decision": "reject",
        "reason": "It can increase pressure and reactance, and it violates the project's low-pressure sales boundary.",
    },
    {
        "tactic_id": "prod053a-reject-002",
        "name": "Hidden emotion diagnosis",
        "decision": "reject",
        "reason": "Emotion signals are weak context; hidden-state certainty is already blocked by existing project policy.",
    },
    {
        "tactic_id": "prod053a-reject-003",
        "name": "Commitment traps",
        "decision": "reject",
        "reason": "Turning a soft yes into obligation conflicts with autonomy, trust, and no-commitment relief.",
    },
    {
        "tactic_id": "prod053a-reject-004",
        "name": "Full customer-category echoing",
        "decision": "reject",
        "reason": "Repeating boss, spouse, manager, or partner every time sounds scripted and does not add useful listening evidence.",
    },
    {
        "tactic_id": "prod053a-reject-005",
        "name": "Large live psychology planner",
        "decision": "defer",
        "reason": "A heavy reasoning layer can add latency. Research should be compressed into deterministic, reviewed rules first.",
    },
    {
        "tactic_id": "prod053a-reject-006",
        "name": "General persuasion principles without source mapping",
        "decision": "reject",
        "reason": "Generic tricks such as reciprocity, liking, and social proof are too easy to misuse unless tied to a safe, source-backed response rule.",
    },
]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def source_registry() -> list[dict[str, Any]]:
    return [
        {
            **source,
            "checked_date": CHECKED_DATE,
            "reuse_label": "summarized_or_adapted_pattern",
            "source_excerpt_text_copied": False,
            "copied_script_text_stored": False,
        }
        for source in SOURCE_REGISTER
    ]


def build_summary(sources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "source_count": len(sources),
        "topic_finding_count": len(TOPIC_FINDINGS),
        "compact_candidate_rule_count": len(COMPACT_CANDIDATE_RULES),
        "rejected_or_deferred_tactic_count": len(REJECTED_OR_DEFERRED_TACTICS),
        "sources_by_weight": dict(Counter(source["evidence_weight"] for source in sources)),
        "high_value_topic_count": sum(1 for finding in TOPIC_FINDINGS if finding["runtime_value"] == "high"),
        "candidate_rules_ready_for_review": sum(
            1 for rule in COMPACT_CANDIDATE_RULES if rule["promotion_readiness"] == "candidate_for_prod_053b_review"
        ),
        "runtime_layer_recommendation": "Compress these findings into a small English rule layer in PROD-053B after review.",
        "research_scope": "English sales-call psychology, with general human psychology only where it directly improves sales-call naturalness or safety.",
        **BOUNDARY_FLAGS,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        f"# {CHECKPOINT_NAME}",
        "",
        "PROD-053A is a source-backed research checkpoint for the English conversation psychology layer. It does not change runtime behavior or response text.",
        "",
        "## Summary",
        "",
        f"- Sources reviewed: `{summary['source_count']}`",
        f"- Topic findings: `{summary['topic_finding_count']}`",
        f"- Compact candidate rules: `{summary['compact_candidate_rule_count']}`",
        f"- Rejected or deferred tactics: `{summary['rejected_or_deferred_tactic_count']}`",
        f"- Runtime behavior changed: `{summary['runtime_behavior_changed']}`",
        f"- Response text behavior changed: `{summary['response_text_behavior_changed']}`",
        f"- Provider calls made: `{summary['provider_calls_made']}`",
        "",
        "## Most Useful Findings",
        "",
    ]
    for finding in payload["topic_findings"]:
        lines.extend(
            [
                f"### {finding['topic']}",
                "",
                f"- Finding: {finding['finding']}",
                f"- Agent use: {finding['agent_use']}",
                f"- Avoid: {finding['avoid']}",
                "",
            ]
        )
    lines.extend(["## Compact Rule Candidates", ""])
    for rule in payload["compact_candidate_rules"]:
        lines.extend(
            [
                f"- `{rule['rule_id']}` {rule['name']}: {rule['rule']}",
                f"  - Good: {rule['example_good']}",
                f"  - Bad: {rule['example_bad']}",
            ]
        )
    lines.extend(["", "## Rejected Or Deferred Tactics", ""])
    for tactic in payload["rejected_or_deferred_tactics"]:
        lines.append(f"- `{tactic['decision']}` {tactic['name']}: {tactic['reason']}")
    lines.extend(["", "## Sources", ""])
    for source in payload["source_registry"]:
        lines.append(f"- `{source['source_id']}` {source['title']} - {source['url']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No source excerpts or copied scripts are stored.",
            "- No runtime behavior, response text, retrieval, provider, LLM judging, private-data, voice, demo, payment, contract, or production promotion is enabled.",
            "- PROD-053B should convert only reviewed candidates into a compact English runtime rule layer.",
            "",
        ]
    )
    return "\n".join(lines)


def build_payload() -> dict[str, Any]:
    sources = source_registry()
    summary = build_summary(sources)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "checked_date": CHECKED_DATE,
        "summary": summary,
        "source_registry": sources,
        "topic_findings": TOPIC_FINDINGS,
        "compact_candidate_rules": COMPACT_CANDIDATE_RULES,
        "rejected_or_deferred_tactics": REJECTED_OR_DEFERRED_TACTICS,
        "validation": {
            "passed": True,
            "notes": [
                "Research packet stores paraphrased project-owned findings only.",
                "Compact rule candidates are not runtime-promoted in this checkpoint.",
            ],
        },
    }


def main() -> None:
    payload = build_payload()
    write_json(OUT_DIR / "result.json", payload)
    write_json(OUT_DIR / "source_register.json", {"items": payload["source_registry"]})
    write_json(OUT_DIR / "topic_findings.json", {"items": payload["topic_findings"]})
    write_json(OUT_DIR / "compact_candidate_rules.json", {"items": payload["compact_candidate_rules"]})
    write_json(OUT_DIR / "rejected_or_deferred_tactics.json", {"items": payload["rejected_or_deferred_tactics"]})
    write_text(OUT_DIR / "report.md", render_report(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
