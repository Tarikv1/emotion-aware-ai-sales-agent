#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


EXPECTED_AGENT_ID = "agent_7801kt0g32zxf4f8x5zkykj7syty"
CHECKPOINT_ID = "ELEVENLABS-040-detailed-pricing-control"
PRICE_TRIGGER_RE = re.compile(
    r"\b(?:how much|costs?|prices?|quotes?|charge|fee|range|ballpark|budget|afford|monthly|extra|fit|fits|works?)\b|\$\s?1,200\b",
    re.IGNORECASE,
)
ADVANCED_PRICE_FOLLOWUP_RE = re.compile(
    r"(?=.*\b(?:how much|costs?|prices?|charge|fee|range|ballpark|budget|afford|monthly|more expensive)\b)(?=.*\b(?:extras?|extra things|booking|payments?|integrations?|live scheduling|logins?)\b)",
    re.IGNORECASE,
)
PAID_PRICE_RE = re.compile(
    r"(?:\$\s?\d[\d,]*(?:\s?(?:-|to)\s?\$?\d[\d,]*\+?)?|\b\d+\s?(?:dollars?|per month|monthly)\b)",
    re.IGNORECASE,
)
RANGE_SEPARATOR_RE = r"(?:-|to)"
ONGOING_COST_TRIGGER_RE = re.compile(
    r"\b(?:hosting|maintenance|updates|support|ongoing (?:fees?|costs?)|monthly|per month)\b",
    re.IGNORECASE,
)
MENU_RE = re.compile(
    r"\b(?:quick launch|essential local|custom business(?=\s+(?:package|plan|tier|option|site|website)\b|[,:;.!?]|$)|growth website|integration website|starter ecommerce|advanced ecommerce)\b",
    re.IGNORECASE,
)
FIXED_QUOTE_RE = re.compile(
    r"\b(?:exactly|exact price|exact quote|exact amount|fixed price|flat(?: fee)?|final price|locked(?: in)?|all[- ]in|comes to|call it)\b",
    re.IGNORECASE,
)
NEGATED_FIXED_QUOTE_RE = re.compile(
    r"\b(?:not(?:\s+(?:a|an))?(?:\s+real)?|can(?:not|'t)|could(?:\s+not|n't)|won't|will\s+not|unable\s+to)\b(?:\s+\w+){0,5}\s+\b(?:exactly|exact(?:\s+(?:price|quote|amount))?|fixed\s+price|flat(?:\s+fee)?|final\s+price|locked(?:\s+in)?|all[- ]in)\b",
    re.IGNORECASE,
)
CEILING_RE = re.compile(
    r"\b(?:maximum|max(?:imum)?|ceiling|cap(?:ped)?|no more than|at most)\b|\bunder\s+\$?\s?\d[\d,]*(?:\.\d+)?\b|\bunder\s+(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)[-\s]+(?:hundred|thousand|million|grand)(?:\s+dollars?)?\b",
    re.IGNORECASE,
)
NEGATED_CEILING_RE = re.compile(
    r"\b(?:not(?:\s+(?:a|an))?(?:\s+real)?|can(?:not|[’']t)|could(?:\s+not|n[’']t)|would(?:\s+not|n[’']t)|won[’']t|will\s+not|unable\s+to)\b(?:\s+\w+){0,6}\s+\b(?:maximum|max(?:imum)?|ceiling|cap(?:ped)?|no more than|at most|under)\b",
    re.IGNORECASE,
)
ARITHMETIC_RE = re.compile(
    r"(?:\+|\b(?:plus|add|stack|sum|total|combined|together)\b)",
    re.IGNORECASE,
)
PORTAL_SCOPE_RE = {
    "accounts": re.compile(r"\baccounts?\b", re.IGNORECASE),
    "data": re.compile(r"\b(?:data|database)\b", re.IGNORECASE),
    "permissions": re.compile(r"\bpermissions?\b", re.IGNORECASE),
    "security": re.compile(r"\bsecurity\b", re.IGNORECASE),
    "integrations": re.compile(r"\bintegrations?\b", re.IGNORECASE),
}
DRIVER_RE = re.compile(
    r"\b(?:page count|pages?|content|copy|layout|workflow|testing|routing|fields?|structure|scope|api|permissions|security|integrations?|mapping|sync)\b",
    re.IGNORECASE,
)
CARE_SCOPE_RE = re.compile(
    r"\b(?:hosting|maintenance|updates?|backups?|monitoring|edits?|reporting|support)\b",
    re.IGNORECASE,
)
CRM_SCOPE_RE = re.compile(
    r"\b(?:api|authentication|field mapping|fields?|sync|synchronization|data flow|error handling)\b",
    re.IGNORECASE,
)
CRM_REQUEST_FORM_SWITCH_RE = re.compile(
    r"(?=.*\b(?:simple\s+(?:form|handoff)|form\s+handoff|appointment\s+request)\b)(?=.*\b(?:how much|costs?|prices?|charge|fee)\b)(?=.*\b(?:do(?:\s+not|n[’']t)\s+have\s+(?:one|a\s+crm)|without\s+(?:a\s+)?crm|no\s+crm)\b)",
    re.IGNORECASE,
)
CRM_HANDOFF_SWITCH_RE = re.compile(
    r"(?=.*\b(?:simple|one[- ]way|supported)\b)(?=.*\b(?:crm\s+)?(?:handoff|connector|plugin)\b)(?=.*\b(?:how much|costs?|prices?|charge|fee)\b)",
    re.IGNORECASE,
)
CAPABILITY_REQUEST_RE = re.compile(
    r"\b(?:booking|calendar|crm|payments?|integrations?|connect(?:ion|ed|ing)?|api|portal|dashboard)\b",
    re.IGNORECASE,
)
ATLAS_CONTACT_DETAIL_RE = re.compile(
    r"\b(?:hello|info|sales|contact)\s*(?:at|@)\s*atlas\s*web\s*studio\s*(?:dot|\.)\s*com\b",
    re.IGNORECASE,
)
UNSUPPORTED_INCLUDED_RE = re.compile(
    r"\b(?:everything|every behavior|all behavior|all workflows?)\b.*\bincluded\b",
    re.IGNORECASE,
)
EXISTING_SITE_RE = re.compile(r"\b(?:existing site|existing website|compatible site|compatible website|on an existing site|current site)\b", re.IGNORECASE)
ADD_ON_RE = re.compile(r"\b(?:add(?:ing|ition)?|add-on|on an existing site|appointment[- ]request form)\b", re.IGNORECASE)
WHOLE_SITE_RE = re.compile(r"\b(?:new site|new website|whole site|whole project|full site|package)\b", re.IGNORECASE)
BUDGET_FIT_POSITIVE_RE = re.compile(
    r"(?:\byes\b[^.?!]*\b(?:fit|fits|can fit|does fit|should fit|work|works|can work)\b|\bthat\s+can\s+fit\b|\b(?:\$1,200|1,200|that budget|the budget|it)\s+(?:fit|fits|can fit|does fit|should fit|work|works|can work)\b|\b(?:that(?:\s+is|[’']s)|(?:\$1,200|1,200|that budget|the budget)\s+is)\s+(?:within\s+(?:the\s+)?(?:usual|normal)\s+range|realistic)\b|\bfit(?:s)?\s+within\s+(?:the\s+)?(?:budget|range|\$?\s?900\s?(?:-|to)\s?\$?\s?1,500)\b|\bstays\s+in\s+the\s+.*range\b)",
    re.IGNORECASE,
)
BUDGET_FIT_NEGATIVE_RE = re.compile(
    r"(?:\bdo(?:es)?\s+not\s+fit\b|\bdoesn't\s+fit\b|\bwon't\s+fit\b|\bwill\s+not\s+fit\b|\bcannot\s+fit\b|\bcan't\s+fit\b|\bdon't\s+think\b|\bdo\s+not\s+think\b|\bnot\s+sure\b|\bunsure\b|\bprobably\s+not\b|\bmaybe\s+not\b|\bnot\s+within\s+budget\b|\bover\s+budget\b|\bout(?:side)?\s+of?\s*budget\b|\boutside\s+budget\b|\bis\s+unrelated\b)",
    re.IGNORECASE,
)
BUDGET_FIT_HEDGE_RE = re.compile(
    r"(?:\bmaybe\b|\bmight\b|\bcould\b|\bpossibly\b|\bprobably\b|\bperhaps\b|\bi think\b|\bI think\b|\bmay\s+fit\b|\bmight\s+fit\b|\bcould\s+fit\b|\bpossibly\s+fit\b|\bprobably\s+fit\b)",
    re.IGNORECASE,
)
NEGATED_WHOLE_SITE_RE = re.compile(
    r"\b(?:not|is not|isn't|isnt|no)\s+(?:a\s+)?(?:new site(?:\s+package)?|new website(?:\s+package)?|whole[- ]site(?:\s+quote)?|whole[- ]project(?:\s+quote)?|full site(?:\s+quote)?|package(?:\s+quote)?)\b",
    re.IGNORECASE,
)
PRICE_QUOTE_RE = re.compile(
    r"(?:\$\s?\d[\d,]*(?:\s?(?:-|to)\s?\$?\d[\d,]*\+?)?|\bnine hundred\b.*\bfifteen hundred\b|\b900\b.*\b1,500\b)",
    re.IGNORECASE,
)
POST_QUOTE_PRICE_FOLLOWUP_RE = re.compile(
    r"\b(?:range|budget|driver|drives|cost(?:s)? more|cost(?:s)? less|more or less|higher|lower|scope|scoped|scoping|firm quote|real (?:number|price|quote)|ready|not all|figure that out|new\s+site|add[- ]on|addition|services page|reviews?)\b",
    re.IGNORECASE,
)
MOCKUP_REFERENCE_RE = re.compile(r"\b(?:mock[- ]?up|homepage concept)\b", re.IGNORECASE)
MOCKUP_VISUAL_CLARIFICATION_RE = re.compile(
    r"\b(?:just|basically)\s+(?:a\s+)?(?:picture|static visual|visual|concept)\b|\b(?:picture|static visual|visual|concept)\s*,?\s+basically\b",
    re.IGNORECASE,
)
SEND_EMAIL_CTA_RE = re.compile(
    r"(?:\bwhere\s+(?:can|do|should)\s+i\s+send\b|\b(?:what|which)\s+email\s+should\s+i\s+send\b|\bwhat(?:[’']s|\s+is)?\s+(?:(?:the|a)\s+)?(?:best|good)\s+email\b|\b(?:(?:i|we)\s+(?:can|could|would|will)|(?:i|we)['’]ll)\s+(?:send|email)\b)",
    re.IGNORECASE,
)
PORTAL_EMAIL_CAPTURE_CTA_RE = re.compile(
    r"\bwhat\s+email\s+should\s+i\s+have\s+you\s+send\s+it\s+to\b",
    re.IGNORECASE,
)
MOCKUP_OFFER_CTA_RE = re.compile(
    r"\b(?:i|we)\s+(?:can|could|would|will)\b[^.?!]{0,50}\b(?:put\s+together|create|make|prepare|build|show|share|walk\s+through|start\s+with|send|email)\b[^.?!]{0,50}\bmock[- ]?up\b",
    re.IGNORECASE,
)
MOCKUP_REVERSE_OFFER_CTA_RE = re.compile(
    r"\b(?:i|we)\s+(?:can|could|would|will)\b[^.?!]{0,60}\bmock[- ]?up\b[^.?!]{0,40}\b(?:put\s+together|prepared?|created?|made|built)\b",
    re.IGNORECASE,
)
MOCKUP_NEXT_STEP_CTA_RE = re.compile(
    r"(?:\b(?:open\s+to|would\s+you\s+be\s+open\s+to|take\s+a\s+look|next\s+step)\b[^.?!]{0,60}\bmock[- ]?up\b|\bmock[- ]?up\b[^.?!]{0,60}\b(?:take\s+a\s+look|next\s+step)\b)",
    re.IGNORECASE,
)
RENEWED_PITCH_CTA_RE = re.compile(
    r"\b(?:reason\s+i\s+called|judge\b[^.?!]{0,60}\bbefore\s+deciding|before\s+deciding\s+anything\s+paid|without\s+asking\s+you\s+to\s+commit)\b",
    re.IGNORECASE,
)
MOCKUP_SEND_SIGNAL_RE = re.compile(
    r"\b(?:send\s+(?:over\s+)?(?:it|that|(?:the\s+)?mock[- ]?up)|go\s+ahead\s+(?:and\s+send|with\s+(?:the\s+)?mock[- ]?up)|mock[- ]?up\s+sounds\s+good(?![^.?!]{0,25}\b(?:but\s+not|not\s+now|later)\b)|(?:yes|yeah)(?![^.?!]{0,20}\b(?:not|don[’']t|do\s+not)\b)[^.?!]{0,30}mock[- ]?up|let[’']?s\s+(?:do|see|start\s+with)\s+(?:the\s+)?mock[- ]?up|i(?:[’']d|\s+would)\s+like(?:\s+to\s+(?:see|do|try|start\s+with))?\s+(?:the\s+)?mock[- ]?up|i\s+want(?:\s+to\s+(?:see|do|try|start\s+with))?\s+(?:the\s+)?mock[- ]?up)\b",
    re.IGNORECASE,
)
PROJECT_PRICE_ASK_RE = re.compile(
    r"\b(?:what does|how much (?:does|is))\s+(?:a\s+)?(?:new\s+)?(?:site|website|build|project)\s+cost\b|\b(?:site|website|build|project)\s+(?:price|cost|quote|range)\b|\b(?:extra\s+cost|what\s+would\s+that\s+cost)\b",
    re.IGNORECASE,
)
SELF_UPDATE_EDITOR_RE = re.compile(
    r"\b(?:self[- ]update|editing\s+access|site\s+editor|content\s+editor|cms\s+setup)\b",
    re.IGNORECASE,
)
PRICE_CHAIN_ACCEPTANCE_RE = re.compile(
    r"\b(?:send it|send that|send the mockup|yes|yeah|sure|okay send|go ahead|take a look)\b",
    re.IGNORECASE,
)


def has_unsupported_fixed_quote(message: str) -> bool:
    without_refusals = NEGATED_FIXED_QUOTE_RE.sub("", message)
    return FIXED_QUOTE_RE.search(without_refusals) is not None


def has_unsupported_ceiling(message: str) -> bool:
    without_refusals = NEGATED_CEILING_RE.sub("", message)
    return CEILING_RE.search(without_refusals) is not None


def has_actionable_post_quote_cta(message: str) -> bool:
    return any(
        pattern.search(message) is not None
        for pattern in (SEND_EMAIL_CTA_RE, PORTAL_EMAIL_CAPTURE_CTA_RE, MOCKUP_OFFER_CTA_RE, MOCKUP_REVERSE_OFFER_CTA_RE, MOCKUP_NEXT_STEP_CTA_RE, RENEWED_PITCH_CTA_RE)
    )


def unsolicited_cta_messages(events: list[dict[str, Any]], *, start_index: int = 0) -> list[str]:
    mockup_send_authorized = False
    violations: list[str] = []
    for index, event in enumerate(events):
        if event["role"] == "user":
            if MOCKUP_SEND_SIGNAL_RE.search(event["message"]):
                mockup_send_authorized = True
            continue
        if (
            index >= start_index
            and event["role"] == "agent"
            and has_actionable_post_quote_cta(event["message"])
            and not mockup_send_authorized
        ):
            violations.append(event["message"])
    return violations


def unsolicited_mockup_mentions(events: list[dict[str, Any]], *, start_index: int = 0) -> list[str]:
    latest_user_message = ""
    violations: list[str] = []
    for index, event in enumerate(events):
        if event["role"] == "user":
            latest_user_message = event["message"]
            continue
        if (
            index >= start_index
            and event["role"] == "agent"
            and MOCKUP_REFERENCE_RE.search(event["message"])
            and MOCKUP_REFERENCE_RE.search(latest_user_message) is None
        ):
            violations.append(event["message"])
    return violations


def buyer_turn_references_mockup(events: list[dict[str, Any]], buyer_index: int) -> bool:
    if buyer_index < 0 or events[buyer_index]["role"] != "user":
        return False
    message = events[buyer_index]["message"]
    if MOCKUP_REFERENCE_RE.search(message):
        return True
    if MOCKUP_VISUAL_CLARIFICATION_RE.search(message) is None:
        return False
    return any(
        event["role"] == "agent" and MOCKUP_REFERENCE_RE.search(event["message"])
        for event in events[max(0, buyer_index - 3) : buyer_index]
    )

def money_range_pattern(start: str, end: str, *, plus_suffix: bool = False) -> re.Pattern[str]:
    suffix = r"\+(?=\D|$)" if plus_suffix else r"\b"
    return re.compile(rf"\$\s?{start}\s?{RANGE_SEPARATOR_RE}\s?\$?\s?{end}{suffix}", re.IGNORECASE)


APPROVED_VALUE_PATTERNS = {
    "basic_site": re.compile(r"(?:\$\s?900\s?%s\s?\$?\s?1,500\b|\bnine hundred\s+to\s+fifteen hundred(?: dollars)?\b)" % RANGE_SEPARATOR_RE, re.IGNORECASE),
    "light_feature": money_range_pattern("1,800", "3,000"),
    "workflow_content": money_range_pattern("2,800", "4,500"),
    "integration_heavy": money_range_pattern("4,000", "6,500"),
    "request_form": money_range_pattern("100", "250"),
    "crm_handoff": money_range_pattern("250", "600"),
    "crm_api": money_range_pattern("1,000", "2,500", plus_suffix=True),
    "care_79": re.compile(r"\$\s?79(?:\s+(?:per month|monthly)|/month)?\b", re.IGNORECASE),
    "care_149": re.compile(r"\$\s?149(?:\s+(?:per month|monthly)|/month)?\b", re.IGNORECASE),
    "care_249": re.compile(r"\$\s?249(?:\s+(?:per month|monthly)|/month)?\b", re.IGNORECASE),
}
CARE_PLAN_LABELS = {"care_79", "care_149", "care_249"}
KNOWN_MONEY_NORMALIZATIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\$\s?900\s*(?:-|to)\s*\$?\s?1500\b", re.IGNORECASE), "$900-$1,500"),
    (re.compile(r"\bbetween\s+nine hundred(?:\s+dollars?)?\s+and\s+fifteen hundred(?:\s+dollars?)?\b", re.IGNORECASE), "$900-$1,500"),
    (re.compile(r"\bnine hundred\s+(?:dollars?\s+)?to\s+fifteen hundred(?:\s+dollars?)?\b", re.IGNORECASE), "$900-$1,500"),
    (re.compile(r"\$\s?100\s*(?:-|to)\s*\$?\s?250\b", re.IGNORECASE), "$100-$250"),
    (re.compile(r"\bone hundred\s+(?:dollars?\s+)?to\s+two hundred fifty(?:\s+dollars?)?\b", re.IGNORECASE), "$100-$250"),
    (re.compile(r"\$\s?250\s*(?:-|to)\s*\$?\s?600\b", re.IGNORECASE), "$250-$600"),
    (re.compile(r"\btwo hundred fifty\s+(?:dollars?\s+)?to\s+six hundred(?:\s+dollars?)?\b", re.IGNORECASE), "$250-$600"),
    (re.compile(r"\$\s?4000\s*(?:-|to)\s*\$?\s?6500\b", re.IGNORECASE), "$4,000-$6,500"),
    (re.compile(r"\bfour thousand\s+(?:dollars?\s+)?to\s+(?:sixty five hundred|six thousand five hundred)(?:\s+dollars?)?\b", re.IGNORECASE), "$4,000-$6,500"),
    (re.compile(r"\$\s?1000\s*(?:-|to)\s*\$?\s?2500\+?\b", re.IGNORECASE), "$1,000-$2,500+"),
    (re.compile(r"\bone thousand\s+(?:dollars?\s+)?to\s+two thousand five hundred(?:\s+dollars?)?\s+plus\b", re.IGNORECASE), "$1,000-$2,500+"),
    (re.compile(r"\bone thousand\s+(?:dollars?\s+)?to\s+two thousand five hundred\s+dollar\s+plus\b", re.IGNORECASE), "$1,000-$2,500+"),
    (re.compile(r"\$\s?1200\b", re.IGNORECASE), "$1,200"),
    (re.compile(r"\btwelve hundred(?:\s+dollars?)?\b", re.IGNORECASE), "$1,200"),
    (re.compile(r"\bseventy nine(?:\s+dollars?)?\b", re.IGNORECASE), "$79"),
    (re.compile(r"\bone hundred forty nine(?:\s+dollars?)?\b", re.IGNORECASE), "$149"),
    (re.compile(r"\btwo hundred forty nine(?:\s+dollars?)?\b", re.IGNORECASE), "$249"),
)

EXPECTED_TEST_ORDER = [
    "sim_040_capability_question_no_unprompted_price",
    "sim_040_free_mockup_question_no_paid_price",
    "sim_040_basic_site_direct_price",
    "sim_040_existing_site_request_form_add_on",
    "sim_040_new_site_booking_whole_project",
    "sim_040_multi_feature_no_price_stacking",
    "sim_040_direct_crm_integration_existing_site",
    "sim_040_portal_requires_scope",
    "sim_040_budget_fit_direct_answer",
    "sim_040_care_plan_only_when_asked",
]
EXPECTED_TESTS: dict[str, dict[str, Any]] = {
    "sim_040_capability_question_no_unprompted_price": {
        "name": f"{CHECKPOINT_ID}::sim_040_capability_question_no_unprompted_price",
        "kind": "capability_no_price",
        "allowed_labels": set(),
        "requires_price_intent": False,
    },
    "sim_040_free_mockup_question_no_paid_price": {
        "name": f"{CHECKPOINT_ID}::sim_040_free_mockup_question_no_paid_price",
        "kind": "free_mockup_no_price",
        "allowed_labels": set(),
        "requires_price_intent": False,
    },
    "sim_040_basic_site_direct_price": {
        "name": f"{CHECKPOINT_ID}::sim_040_basic_site_direct_price",
        "kind": "basic_site",
        "allowed_labels": {"basic_site"},
        "requires_price_intent": True,
    },
    "sim_040_existing_site_request_form_add_on": {
        "name": f"{CHECKPOINT_ID}::sim_040_existing_site_request_form_add_on",
        "kind": "existing_request_form",
        "allowed_labels": {"request_form"},
        "requires_price_intent": True,
    },
    "sim_040_new_site_booking_whole_project": {
        "name": f"{CHECKPOINT_ID}::sim_040_new_site_booking_whole_project",
        "kind": "new_site_booking",
        "allowed_labels": {"basic_site", "integration_heavy"},
        "requires_price_intent": True,
    },
    "sim_040_multi_feature_no_price_stacking": {
        "name": f"{CHECKPOINT_ID}::sim_040_multi_feature_no_price_stacking",
        "kind": "multi_feature",
        "allowed_labels": {"integration_heavy"},
        "requires_price_intent": True,
    },
    "sim_040_direct_crm_integration_existing_site": {
        "name": f"{CHECKPOINT_ID}::sim_040_direct_crm_integration_existing_site",
        "kind": "crm_existing_site",
        "allowed_labels": {"crm_api"},
        "requires_price_intent": True,
    },
    "sim_040_portal_requires_scope": {
        "name": f"{CHECKPOINT_ID}::sim_040_portal_requires_scope",
        "kind": "portal_scope",
        "allowed_labels": set(),
        "requires_price_intent": True,
    },
    "sim_040_budget_fit_direct_answer": {
        "name": f"{CHECKPOINT_ID}::sim_040_budget_fit_direct_answer",
        "kind": "budget_fit",
        "allowed_labels": {"basic_site"},
        "requires_price_intent": True,
    },
    "sim_040_care_plan_only_when_asked": {
        "name": f"{CHECKPOINT_ID}::sim_040_care_plan_only_when_asked",
        "kind": "care_plan",
        "allowed_labels": CARE_PLAN_LABELS,
        "requires_price_intent": True,
    },
}


class Checks:
    def __init__(self) -> None:
        self.assertions: list[dict[str, Any]] = []
        self.failures: list[str] = []

    def check(self, name: str, condition: bool, detail: str) -> None:
        entry: dict[str, Any] = {"name": name, "passed": bool(condition)}
        if not condition:
            entry["detail"] = detail
            self.failures.append(f"{name}: {detail}")
        self.assertions.append(entry)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate sanitized ELEVENLABS-040 live test traces without trusting provider labels.")
    parser.add_argument("--input", type=Path, help="Sanitized capture JSON path")
    parser.add_argument("--mapping", type=Path, help="Optional live_test_mapping.json path. Defaults to input sibling when present.")
    parser.add_argument("--output", type=Path, help="Optional JSON path for the independent validation summary")
    parser.add_argument("--partial-canary", action="store_true", help="Validate exactly the basic-site canary instead of the full 10-test suite")
    parser.add_argument("--partial-test-id", help="Validate exactly one known expected 040 test id in partial mode")
    parser.add_argument("--self-test", action="store_true", help="Run built-in validator self-tests")
    args = parser.parse_args()
    if args.partial_canary and args.partial_test_id:
        parser.error("--partial-canary and --partial-test-id are mutually exclusive")
    if not args.self_test and args.input is None:
        parser.error("--input is required unless --self-test is used")
    return args


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read JSON input {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("input must contain a JSON object")
    return value


def capture_payload(document: dict[str, Any]) -> dict[str, Any]:
    payload = document.get("payload", document)
    if not isinstance(payload, dict):
        raise ValueError("input payload must be a JSON object")
    stored_hash = document.get("payload_sha256")
    if stored_hash:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        actual_hash = hashlib.sha256(canonical).hexdigest()
        if stored_hash != actual_hash:
            raise ValueError("payload_sha256 does not match the sanitized payload")
    return payload


def provider_test_id_mapping(document: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(document, dict):
        return {}
    tests = document.get("tests")
    mapping: dict[str, str] = {}
    if isinstance(tests, list):
        for raw in tests:
            if not isinstance(raw, dict):
                continue
            source_id = raw.get("source_test_id") or raw.get("repo_test_id") or raw.get("test_id")
            provider_id = raw.get("provider_test_id")
            if isinstance(source_id, str) and isinstance(provider_id, str) and source_id and provider_id:
                mapping[source_id] = provider_id
    raw_provider_ids = document.get("provider_test_ids")
    if isinstance(raw_provider_ids, dict):
        for source_id, provider_id in raw_provider_ids.items():
            if isinstance(source_id, str) and isinstance(provider_id, str) and source_id and provider_id:
                mapping[source_id] = provider_id
    return mapping


def canonical_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = " ".join(value.split())
    for pattern, replacement in KNOWN_MONEY_NORMALIZATIONS:
        normalized = pattern.sub(replacement, normalized)
    return normalized


def event_text(event: dict[str, Any]) -> str:
    return canonical_text(event.get("message") or event.get("original_message"))


def event_role(event: dict[str, Any]) -> str:
    value = str(event.get("role", "")).lower()
    return "agent" if value == "assistant" else value


def is_canonical_end_call_mirror(event: dict[str, Any]) -> bool:
    if event_role(event) != "agent" or event_text(event):
        return False
    tool_entries = [
        item
        for key in ("tool_calls", "tool_results")
        for item in event.get(key, [])
        if isinstance(item, dict)
    ]
    return bool(tool_entries) and all(
        item.get("type") == "system"
        and item.get("tool_name") == "end_call"
        and item.get("tool_has_been_called") is True
        for item in tool_entries
    )


def approved_labels(message: str) -> list[str]:
    return [label for label, pattern in APPROVED_VALUE_PATTERNS.items() if pattern.search(message)]


def money_matches(message: str) -> list[str]:
    return [match.group(0) for match in PAID_PRICE_RE.finditer(message)]


def monetary_labels_for_match(match_text: str) -> set[str]:
    labels = {label for label, pattern in APPROVED_VALUE_PATTERNS.items() if pattern.search(match_text)}
    if re.fullmatch(r"\$\s?1,200\b", match_text, re.IGNORECASE):
        labels.add("buyer_budget_reference")
    return labels


def money_match_labels(message: str) -> list[tuple[str, set[str]]]:
    return [(match.group(0), monetary_labels_for_match(match.group(0))) for match in PAID_PRICE_RE.finditer(message)]


def contains_affirmative_budget_fit(text: str) -> bool:
    for sentence in re.split(r"(?<=[.!?;])\s+", text):
        if (
            BUDGET_FIT_POSITIVE_RE.search(sentence) is not None
            and BUDGET_FIT_NEGATIVE_RE.search(sentence) is None
            and BUDGET_FIT_HEDGE_RE.search(sentence) is None
        ):
            return True
    return False


def contains_positive_whole_site_framing(text: str) -> bool:
    stripped = NEGATED_WHOLE_SITE_RE.sub("", text)
    stripped = re.sub(r"\b(?:or\s+)?(?:are you\s+)?considering a new site(?: too)?\b", "", stripped, flags=re.IGNORECASE)
    return WHOLE_SITE_RE.search(stripped) is not None


def unique_labels_seen(messages: list[str]) -> set[str]:
    labels: set[str] = set()
    for message in messages:
        labels.update(approved_labels(message))
    return labels


def first_index(events: list[dict[str, Any]], *, role: str, pattern: re.Pattern[str]) -> int | None:
    for index, event in enumerate(events):
        if event["role"] == role and pattern.search(event["message"]):
            return index
    return None


def first_agent_price_quote_index(events: list[dict[str, Any]]) -> int | None:
    for index, event in enumerate(events):
        if event["role"] == "agent" and PRICE_QUOTE_RE.search(event["message"]):
            return index
    return None


def extract_dialogue(run: dict[str, Any], checks: Checks) -> list[dict[str, Any]]:
    raw_events = run.get("agent_responses")
    checks.check(
        "ordered_agent_responses_present",
        isinstance(raw_events, list) and len(raw_events) > 0,
        "agent_responses must be a non-empty ordered list",
    )
    checks.check(
        "incomplete_simulation",
        not (isinstance(raw_events, list) and len(raw_events) == 0),
        "provider returned an explicit empty agent_responses list; classify as incomplete simulation",
    )
    if not isinstance(raw_events, list):
        return []
    events: list[dict[str, Any]] = []
    malformed = 0
    for raw in raw_events:
        if not isinstance(raw, dict):
            malformed += 1
            continue
        role = event_role(raw)
        message = event_text(raw)
        if role not in {"user", "agent"} or not message:
            if is_canonical_end_call_mirror(raw):
                continue
            if role in {"user", "agent"}:
                malformed += 1
            continue
        events.append({"role": role, "message": message})
    checks.check("ordered_dialogue_extractable", malformed == 0 and len(events) > 0, "trace contains missing or ambiguous ordered text responses")
    checks.check("buyer_turn_present", any(event["role"] == "user" for event in events), "trace must contain at least one buyer turn")
    checks.check("agent_turn_present", any(event["role"] == "agent" for event in events), "trace must contain at least one agent turn")
    return events


def record_common_message_rules(checks: Checks, events: list[dict[str, Any]]) -> None:
    for index, event in enumerate(events):
        if event["role"] != "agent":
            continue
        message = event["message"]
        labels = approved_labels(message)
        non_care_labels = [label for label in labels if label not in CARE_PLAN_LABELS]
        checks.check(
            "no_more_than_two_approved_ranges_in_response",
            len(non_care_labels) <= 2,
            f"agent response {index} contains more than two approved non-care ranges: {non_care_labels}",
        )
        checks.check(
            "no_menu_dump",
            MENU_RE.search(message) is None,
            f"agent response {index} reads the pricing menu",
        )
        if money_matches(message):
            checks.check(
                "no_unsupported_fixed_quote_or_ceiling",
                not has_unsupported_fixed_quote(message) and not has_unsupported_ceiling(message),
                f"agent response {index} contains an unsupported fixed quote or ceiling",
            )


def validate_post_quote_followup_cta_lock(checks: Checks, events: list[dict[str, Any]]) -> None:
    first_quote = first_agent_price_quote_index(events)
    if first_quote is None:
        checks.check("post_quote_price_followup_no_cta", True, "no quoted price chain found")
        return

    violations: list[str] = []
    first_quote_message = events[first_quote]["message"]
    buyer_mentioned_mockup = buyer_turn_references_mockup(events, first_quote - 1)
    if has_actionable_post_quote_cta(first_quote_message) or (
        MOCKUP_REFERENCE_RE.search(first_quote_message) and not buyer_mentioned_mockup
    ):
        violations.append(f"agent response {first_quote} appended mockup/email/send CTA to the price answer")

    active_price_chain = False
    buyer_mentioned_mockup = False
    for index, event in enumerate(events[first_quote + 1 :], start=first_quote + 1):
        message = event["message"]
        if event["role"] == "user":
            if PRICE_CHAIN_ACCEPTANCE_RE.search(message) and not POST_QUOTE_PRICE_FOLLOWUP_RE.search(message):
                active_price_chain = False
                buyer_mentioned_mockup = False
                continue
            if POST_QUOTE_PRICE_FOLLOWUP_RE.search(message):
                active_price_chain = True
                buyer_mentioned_mockup = MOCKUP_REFERENCE_RE.search(message) is not None
            else:
                active_price_chain = False
                buyer_mentioned_mockup = False
            continue
        if event["role"] == "agent" and active_price_chain:
            actionable_cta = has_actionable_post_quote_cta(message)
            unsolicited_mockup = MOCKUP_REFERENCE_RE.search(message) is not None and not buyer_mentioned_mockup
            if actionable_cta or unsolicited_mockup:
                violations.append(f"agent response {index} reopened mockup/email/send CTA during active price follow-up")
    checks.check(
        "post_quote_price_followup_no_cta",
        not violations,
        "; ".join(violations) if violations else "active price follow-ups must not reopen mockup/email/send CTA",
    )


def validate_allowed_labels(checks: Checks, messages: list[str], allowed: set[str]) -> set[str]:
    seen = unique_labels_seen(messages)
    ignored_labels = set()
    if not (allowed & CARE_PLAN_LABELS):
        ignored_labels.update(CARE_PLAN_LABELS)
    unexpected = sorted(seen - allowed - ignored_labels)
    checks.check(
        "approved_ranges_only_in_relevant_scenarios",
        not unexpected,
        f"unexpected approved ranges/plans: {unexpected}",
    )
    disallowed_matches: list[str] = []
    for message in messages:
        for match_text, labels in money_match_labels(message):
            if labels and labels <= (allowed | {"buyer_budget_reference"}):
                continue
            if labels and labels <= (allowed | ignored_labels | {"buyer_budget_reference"}):
                continue
            if not labels:
                disallowed_matches.append(match_text)
                continue
            unexpected_labels = labels - allowed - ignored_labels - {"buyer_budget_reference"}
            if unexpected_labels:
                disallowed_matches.append(match_text)
    checks.check(
        "no_unapproved_paid_price_ranges",
        not disallowed_matches,
        f"unsupported paid-price values detected: {disallowed_matches}",
    )
    return seen


def validate_price_gate(checks: Checks, expected: dict[str, Any], events: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    first_trigger = first_index(events, role="user", pattern=PRICE_TRIGGER_RE)
    first_paid = first_index(events, role="agent", pattern=PAID_PRICE_RE)
    checks.check(
        "unprompted_paid_price",
        first_paid is None or (first_trigger is not None and first_trigger < first_paid),
        "agent disclosed paid pricing before the first buyer price trigger",
    )
    if expected["requires_price_intent"]:
        checks.check("buyer_price_trigger_present", first_trigger is not None, "price-trigger scenario is missing a buyer price trigger")
    return first_trigger, first_paid


def scenario_no_price(checks: Checks, messages: list[str], first_paid: int | None) -> None:
    validate_allowed_labels(checks, messages, set())
    checks.check("no_paid_price_disclosure", first_paid is None, "scenario must not contain any paid-price disclosure")


def scenario_capability_no_price(checks: Checks, events: list[dict[str, Any]], messages: list[str], first_paid: int | None) -> None:
    scenario_no_price(checks, messages, first_paid)
    capability_index = first_index(events, role="user", pattern=CAPABILITY_REQUEST_RE)
    start_index = capability_index if capability_index is not None else 0
    violations = unsolicited_cta_messages(events, start_index=start_index)
    violations.extend(unsolicited_mockup_mentions(events, start_index=start_index))
    checks.check(
        "capability_chain_no_unsolicited_cta",
        not violations,
        f"capability/CRM answer reopened a mockup or email CTA: {violations}",
    )


def scenario_free_mockup_no_price(checks: Checks, events: list[dict[str, Any]], messages: list[str], first_paid: int | None) -> None:
    scenario_no_price(checks, messages, first_paid)
    violations = unsolicited_cta_messages(events)
    checks.check(
        "free_mockup_process_no_unsolicited_cta",
        not violations,
        f"free/process-risk chain reopened the mockup CTA before a buyer send signal: {violations}",
    )


def scenario_basic_site(checks: Checks, events: list[dict[str, Any]], messages: list[str]) -> None:
    seen = validate_allowed_labels(checks, messages, {"basic_site"})
    checks.check("basic_site_expected_range", "basic_site" in seen, "basic-site range $900-$1,500 is required")
    checks.check("basic_site_scope_driver_present", any(DRIVER_RE.search(message) for message in messages), "basic-site answer must include one relevant scope driver")
    first_quote = first_agent_price_quote_index(events)
    start_index = first_quote if first_quote is not None else 0
    violations = unsolicited_cta_messages(events, start_index=start_index)
    violations.extend(unsolicited_mockup_mentions(events, start_index=start_index))
    checks.check(
        "basic_price_chain_no_unsolicited_cta",
        not violations,
        f"basic-site price/scope chain reopened a mockup CTA: {violations}",
    )


def scenario_existing_request_form(checks: Checks, events: list[dict[str, Any]], messages: list[str]) -> None:
    seen = validate_allowed_labels(checks, messages, {"request_form"})
    checks.check("existing_site_expected_add_on_range", "request_form" in seen, "existing-site request-form scenario requires only the $100-$250 add-on range")
    combined = " ".join(message for message in messages if "request_form" in approved_labels(message))
    checks.check(
        "existing_site_add_on_classification",
        EXISTING_SITE_RE.search(combined) is not None and ADD_ON_RE.search(combined) is not None and not contains_positive_whole_site_framing(combined),
        "existing-site request-form answer must frame the work as a compatible existing-site add-on, not a new-site/package quote",
    )
    first_quote = first_agent_price_quote_index(events)
    start_index = first_quote if first_quote is not None else 0
    violations = unsolicited_cta_messages(events, start_index=start_index)
    violations.extend(unsolicited_mockup_mentions(events, start_index=start_index))
    checks.check(
        "existing_site_price_chain_no_unsolicited_cta",
        not violations,
        f"existing-site price/setup/logistics chain reopened the mockup: {violations}",
    )


def scenario_new_site_booking(checks: Checks, events: list[dict[str, Any]], messages: list[str]) -> None:
    seen = validate_allowed_labels(checks, messages, {"basic_site", "integration_heavy"})
    checks.check("new_site_basic_range_present", "basic_site" in seen, "new-site booking scenario must include the base $900-$1,500 whole-project range")
    checks.check("new_site_integration_range_present", "integration_heavy" in seen, "live-calendar follow-up must move to the $4,000-$6,500 whole-project range")
    first_basic = next((index for index, message in enumerate(messages) if "basic_site" in approved_labels(message)), None)
    first_integrated = next((index for index, message in enumerate(messages) if "integration_heavy" in approved_labels(message)), None)
    checks.check(
        "new_site_whole_project_progression_order",
        first_basic is not None and first_integrated is not None and first_basic < first_integrated,
        "new-site pricing must progress from base whole-project range to higher integration whole-project range",
    )
    if first_integrated is not None:
        integrated_message = messages[first_integrated].lower()
        checks.check(
            "new_site_whole_project_classification",
            any(fragment in integrated_message for fragment in ("whole project", "new build", "new site")),
            "higher integration answer must keep the classification as a whole project, not an add-on",
        )
    first_quote = first_agent_price_quote_index(events)
    violations = unsolicited_cta_messages(events, start_index=first_quote if first_quote is not None else 0)
    checks.check(
        "new_site_price_chain_no_unsolicited_cta",
        not violations,
        f"new-site price/scope chain reopened a mockup CTA: {violations}",
    )


def scenario_multi_feature(checks: Checks, messages: list[str]) -> None:
    seen = validate_allowed_labels(checks, messages, {"integration_heavy"})
    checks.check("multi_feature_whole_project_range", "integration_heavy" in seen, "multi-feature scenario must use the $4,000-$6,500 whole-project band")
    arithmetic_violations = [
        message
        for message in messages
        if len(money_matches(message)) >= 2 and ARITHMETIC_RE.search(message)
    ]
    checks.check("no_arithmetic_total", not arithmetic_violations, f"multi-feature pricing must not stack or total ranges: {arithmetic_violations}")


def scenario_crm_existing_site(checks: Checks, events: list[dict[str, Any]], messages: list[str]) -> None:
    request_form_switch_index = next(
        (
            index
            for index, event in enumerate(events)
            if event["role"] == "user" and CRM_REQUEST_FORM_SWITCH_RE.search(event["message"])
        ),
        None,
    )
    switched_to_request_form = request_form_switch_index is not None
    first_direct_quote = next(
        (
            index
            for index, event in enumerate(events)
            if event["role"] == "agent" and "crm_api" in approved_labels(event["message"])
        ),
        None,
    )
    handoff_switch_index = next(
        (
            index
            for index, event in enumerate(events)
            if first_direct_quote is not None
            and index > first_direct_quote
            and event["role"] == "user"
            and CRM_HANDOFF_SWITCH_RE.search(event["message"])
        ),
        None,
    )
    switched_to_handoff = handoff_switch_index is not None
    if switched_to_request_form:
        allowed_labels = {"crm_api", "request_form"}
    elif switched_to_handoff:
        allowed_labels = {"crm_api", "crm_handoff"}
    else:
        allowed_labels = {"crm_api"}
    seen = validate_allowed_labels(checks, messages, allowed_labels)
    expected_label = "request_form" if switched_to_request_form else "crm_handoff" if switched_to_handoff else "crm_api"
    checks.check(
        "crm_existing_site_expected_range",
        expected_label in seen,
        "CRM scenario must use the direct range unless the buyer explicitly abandons CRM and asks for a simple request-form price",
    )
    checks.check(
        "crm_scope_caveat_present",
        switched_to_request_form or switched_to_handoff or any(CRM_SCOPE_RE.search(message) for message in messages),
        "direct CRM pricing must mention API/data-flow scope caveats",
    )
    lane_violations: list[str] = []
    for index, event in enumerate(events):
        if event["role"] != "agent":
            continue
        labels = set(approved_labels(event["message"]))
        quoted_lanes = labels & {"crm_api", "crm_handoff", "request_form"}
        if len(quoted_lanes) > 1:
            lane_violations.append(f"agent response {index} quoted multiple CRM/request-form lanes together: {sorted(quoted_lanes)}")
        if "crm_handoff" in labels and (handoff_switch_index is None or index <= handoff_switch_index):
            lane_violations.append(f"agent response {index} quoted the handoff range before a later explicit scope change")
        if "crm_api" in labels and handoff_switch_index is not None and index > handoff_switch_index:
            lane_violations.append(f"agent response {index} repeated the direct range after the handoff scope change")
        if "request_form" in labels and (request_form_switch_index is None or index <= request_form_switch_index):
            lane_violations.append(f"agent response {index} quoted the request-form range before a later explicit scope change")
        if "crm_api" in labels and request_form_switch_index is not None and index > request_form_switch_index:
            lane_violations.append(f"agent response {index} repeated the direct range after the request-form scope change")
    checks.check(
        "crm_one_lane_only",
        not lane_violations,
        "; ".join(lane_violations) if lane_violations else "CRM price answers must stay in one lane",
    )
    crm_cta_messages = [message for message in messages if has_actionable_post_quote_cta(message)]
    checks.check(
        "crm_chain_no_mockup_or_email_cta",
        not crm_cta_messages,
        f"CRM price/scope/logistics chain reopened a mockup or email CTA: {crm_cta_messages}",
    )
    invented_contact_messages = [message for message in messages if ATLAS_CONTACT_DETAIL_RE.search(message)]
    checks.check(
        "crm_no_invented_contact_details",
        not invented_contact_messages,
        f"CRM logistics response invented Atlas contact details: {invented_contact_messages}",
    )
    checks.check(
        "crm_no_everything_included_claim",
        not any(UNSUPPORTED_INCLUDED_RE.search(message) for message in messages),
        "CRM pricing must not imply every behavior is included by default",
    )


def scenario_portal_scope(checks: Checks, events: list[dict[str, Any]], messages: list[str], first_paid: int | None) -> None:
    validate_allowed_labels(checks, messages, set())
    numeric_messages = [message for message in messages if money_matches(message)]
    checks.check("portal_no_numeric_price", not numeric_messages and first_paid is None, f"portal scenario must not contain numeric pricing: {numeric_messages}")
    combined = " ".join(messages)
    scope_hits = sorted(label for label, pattern in PORTAL_SCOPE_RE.items() if pattern.search(combined))
    checks.check(
        "portal_scope_classification",
        ("custom" in combined.lower() or "scope" in combined.lower()) and len(scope_hits) >= 3,
        f"portal scenario must classify as scoped custom work with accounts/data/permissions/security/integrations; found {scope_hits}",
    )
    buyer_mentioned_mockup = any(
        event["role"] == "user" and MOCKUP_REFERENCE_RE.search(event["message"])
        for event in events
    )
    portal_cta_messages = [
        message
        for message in messages
        if has_actionable_post_quote_cta(message) or (MOCKUP_REFERENCE_RE.search(message) and not buyer_mentioned_mockup)
    ]
    checks.check("portal_no_mockup_cta", not portal_cta_messages, f"portal scope chain reopened mockup CTA: {portal_cta_messages}")


def scenario_budget_fit(checks: Checks, events: list[dict[str, Any]], messages: list[str]) -> None:
    first_budget_trigger = first_index(events, role="user", pattern=PRICE_TRIGGER_RE)
    advanced_price_trigger = next(
        (
            index
            for index, event in enumerate(events)
            if event["role"] == "user"
            and PRICE_TRIGGER_RE.search(event["message"])
            and ADVANCED_PRICE_FOLLOWUP_RE.search(event["message"])
        ),
        None,
    )
    advanced_price_is_later = (
        advanced_price_trigger is None
        or (first_budget_trigger is not None and advanced_price_trigger > first_budget_trigger)
    )
    checks.check(
        "budget_advanced_price_followup_is_later",
        advanced_price_is_later,
        "advanced-feature pricing must be requested in a later buyer turn after the initial budget-fit question",
    )
    allowed_labels = {"basic_site", "buyer_budget_reference"}
    if advanced_price_trigger is not None and advanced_price_is_later:
        allowed_labels.add("integration_heavy")
    seen = validate_allowed_labels(checks, messages, allowed_labels)
    integration_before_trigger = [
        event["message"]
        for index, event in enumerate(events)
        if event["role"] == "agent"
        and "integration_heavy" in approved_labels(event["message"])
        and (advanced_price_trigger is None or index < advanced_price_trigger)
    ]
    checks.check(
        "budget_advanced_price_only_after_ask",
        not integration_before_trigger,
        f"advanced whole-project pricing appeared before an explicit advanced-feature price question: {integration_before_trigger}",
    )
    checks.check("budget_fit_expected_range", "basic_site" in seen, "budget-fit scenario must answer against the $900-$1,500 basic-site range")
    combined = " ".join(messages)
    dialogue = " ".join(event["message"] for event in events)
    checks.check(
        "budget_fit_affirmative_answer_required",
        contains_affirmative_budget_fit(combined),
        "budget-fit scenario must give an affirmative fit answer for a $1,200 budget",
    )
    checks.check(
        "budget_fit_semantics",
        re.search(r"\$\s?1,200\b", dialogue) is not None
        and re.search(r"\$\s?900\s?(?:-|to)\s?\$?\s?1,500\b", combined, re.IGNORECASE) is not None
        and contains_affirmative_budget_fit(combined)
        and re.search(r"\b(?:within|in the .* range|in that range|stays in|fit|fits|work|works|can work)\b", combined, re.IGNORECASE) is not None,
        "budget-fit scenario must relate the buyer's $1,200 budget positively to the $900-$1,500 range",
    )
    first_quote = first_agent_price_quote_index(events)
    violations = unsolicited_cta_messages(events, start_index=first_quote if first_quote is not None else 0)
    checks.check(
        "budget_price_chain_no_unsolicited_cta",
        not violations,
        f"budget price/scope chain reopened a mockup CTA: {violations}",
    )


def scenario_care_plan(checks: Checks, events: list[dict[str, Any]], messages: list[str]) -> None:
    ongoing_trigger = first_index(events, role="user", pattern=ONGOING_COST_TRIGGER_RE)
    checks.check(
        "ongoing_cost_question_present",
        ongoing_trigger is not None,
        "care-plan scenario must include an explicit hosting/maintenance/monthly question",
    )
    project_price_allowed = False
    unasked_project_prices: list[str] = []
    if ongoing_trigger is not None:
        for event in events[ongoing_trigger + 1 :]:
            if event["role"] == "user" and PROJECT_PRICE_ASK_RE.search(event["message"]):
                project_price_allowed = True
            elif event["role"] == "agent":
                non_care_labels = set(approved_labels(event["message"])) - CARE_PLAN_LABELS
                if non_care_labels and not project_price_allowed:
                    unasked_project_prices.append(event["message"])
    checks.check(
        "care_chain_no_unasked_project_price",
        not unasked_project_prices,
        f"care-only chain disclosed project pricing without an explicit project-price question: {unasked_project_prices}",
    )
    editor_context = False
    editor_request_form_prices: list[str] = []
    for event in events[(ongoing_trigger or 0) + 1 :]:
        if event["role"] == "user" and SELF_UPDATE_EDITOR_RE.search(event["message"]):
            editor_context = True
        elif event["role"] == "agent" and editor_context and "request_form" in approved_labels(event["message"]):
            editor_request_form_prices.append(event["message"])
    checks.check(
        "editor_setup_no_request_form_price",
        not editor_request_form_prices,
        f"editor/CMS setup reused the appointment-request range: {editor_request_form_prices}",
    )
    violations = unsolicited_cta_messages(events, start_index=ongoing_trigger if ongoing_trigger is not None else 0)
    checks.check(
        "care_chain_no_unsolicited_cta",
        not violations,
        f"care/context chain treated a mockup reference as send permission: {violations}",
    )
    early_messages = [event["message"] for event in events[: ongoing_trigger or 0] if event["role"] == "agent"]
    early_labels = unique_labels_seen(early_messages) & CARE_PLAN_LABELS
    checks.check(
        "care_plan_only_after_ongoing_cost_intent",
        not early_labels,
        f"care-plan price appeared before the ongoing-cost question: {sorted(early_labels)}",
    )
    after_messages = [event["message"] for event in events[(ongoing_trigger or 0) + 1 :] if event["role"] == "agent"]
    care_labels = unique_labels_seen(after_messages) & CARE_PLAN_LABELS
    checks.check("care_plan_single_relevant_plan", len(care_labels) == 1, f"care-plan response must quote exactly one approved monthly plan; found {sorted(care_labels)}")
    checks.check("care_plan_scope_present", any(CARE_SCOPE_RE.search(message) for message in after_messages), "care-plan response must mention the ongoing scope")


def validate_run(run: dict[str, Any], *, expected_provider_test_id: str | None = None) -> dict[str, Any]:
    test_id = str(run.get("test_id", "")).strip()
    expected = EXPECTED_TESTS.get(test_id)
    checks = Checks()
    if expected is None:
        return {
            "test_id": test_id,
            "test_name": run.get("test_name"),
            "test_run_id": run.get("test_run_id"),
            "independent_status": "fail",
            "provider_status": run.get("status"),
            "provider_condition_result": run.get("condition_result"),
            "provider_evaluator_rationale": run.get("evaluator_rationale"),
            "assertions": [{"name": "expected_test_id", "passed": False, "detail": "unexpected test id"}],
            "failures": ["expected_test_id: unexpected test id"],
        }

    checks.check("expected_test_name", run.get("test_name") == expected["name"], f"expected test_name {expected['name']!r}")
    provider_test_id = run.get("provider_test_id")
    if provider_test_id is not None:
        checks.check(
            "provider_test_id_reconciled",
            expected_provider_test_id is not None and str(provider_test_id) == expected_provider_test_id,
            f"provider_test_id must reconcile through live_test_mapping for {test_id!r}",
        )

    events = extract_dialogue(run, checks)
    record_common_message_rules(checks, events)
    validate_post_quote_followup_cta_lock(checks, events)
    first_trigger, first_paid = validate_price_gate(checks, expected, events)
    messages = [event["message"] for event in events if event["role"] == "agent"]
    incomplete = not events or (
        bool(expected["requires_price_intent"])
        and first_trigger is None
        and first_paid is None
    )

    kind = expected["kind"]
    if incomplete:
        pass
    elif kind == "capability_no_price":
        scenario_capability_no_price(checks, events, messages, first_paid)
    elif kind == "no_price":
        scenario_no_price(checks, messages, first_paid)
    elif kind == "free_mockup_no_price":
        scenario_free_mockup_no_price(checks, events, messages, first_paid)
    elif kind == "basic_site":
        scenario_basic_site(checks, events, messages)
    elif kind == "existing_request_form":
        scenario_existing_request_form(checks, events, messages)
    elif kind == "new_site_booking":
        scenario_new_site_booking(checks, events, messages)
    elif kind == "multi_feature":
        scenario_multi_feature(checks, messages)
    elif kind == "crm_existing_site":
        scenario_crm_existing_site(checks, events, messages)
    elif kind == "portal_scope":
        scenario_portal_scope(checks, events, messages, first_paid)
    elif kind == "budget_fit":
        scenario_budget_fit(checks, events, messages)
    elif kind == "care_plan":
        scenario_care_plan(checks, events, messages)
    else:
        checks.check("known_validation_kind", False, f"unknown validation kind {kind!r}")

    independent_status = "pass"
    if checks.failures:
        if incomplete and all(
            failure.startswith(("buyer_price_trigger_present:", "incomplete_simulation:", "ordered_agent_responses_present:"))
            for failure in checks.failures
        ):
            independent_status = "incomplete"
        else:
            independent_status = "fail"

    return {
        "test_id": test_id,
        "test_name": run.get("test_name"),
        "test_run_id": run.get("test_run_id"),
        "independent_status": independent_status,
        "provider_status": run.get("status"),
        "provider_condition_result": run.get("condition_result"),
        "provider_evaluator_rationale": run.get("evaluator_rationale"),
        "first_price_trigger_index": first_trigger,
        "first_agent_paid_price_index": first_paid,
        "assertions": checks.assertions,
        "failures": checks.failures,
    }


def validate_payload(payload: dict[str, Any], mapping: dict[str, str] | None = None) -> dict[str, Any]:
    global_failures: list[str] = []
    tests: list[dict[str, Any]] = []
    provider_mapping = dict(mapping or {})
    provider_mapping.update(provider_test_id_mapping(payload.get("live_test_mapping") if isinstance(payload.get("live_test_mapping"), dict) else None))

    if payload.get("agent_id") != EXPECTED_AGENT_ID:
        global_failures.append(f"agent_id must be {EXPECTED_AGENT_ID}")
    if payload.get("checkpoint_id") not in (None, "", CHECKPOINT_ID):
        global_failures.append(f"checkpoint_id must be {CHECKPOINT_ID}")

    runs_raw = payload.get("test_runs")
    if not isinstance(runs_raw, list):
        global_failures.append("payload.test_runs must be a list")
        runs_raw = []

    runs = [run for run in runs_raw if isinstance(run, dict)]
    if len(runs) != len(runs_raw):
        global_failures.append("all test_runs entries must be JSON objects")

    raw_input_test_ids = [str(run.get("test_id", "")).strip() for run in runs]
    id_counts = Counter(raw_input_test_ids)
    duplicate_ids = sorted(test_id for test_id, count in id_counts.items() if test_id and count > 1)
    missing_ids = [test_id for test_id in EXPECTED_TEST_ORDER if id_counts[test_id] == 0]
    unexpected_ids = sorted(test_id for test_id in id_counts if test_id and test_id not in EXPECTED_TESTS)
    if duplicate_ids:
        global_failures.append(f"duplicate test ids: {duplicate_ids}")
    if missing_ids:
        global_failures.append(f"missing test ids: {missing_ids}")
    if unexpected_ids:
        global_failures.append(f"unexpected test ids: {unexpected_ids}")
    if len(runs) != len(EXPECTED_TEST_ORDER):
        global_failures.append(f"expected exactly {len(EXPECTED_TEST_ORDER)} test runs, found {len(runs)}")
    if not duplicate_ids and not missing_ids and not unexpected_ids and len(runs) == len(EXPECTED_TEST_ORDER):
        runs_by_id = {str(run.get("test_id", "")).strip(): run for run in runs}
        runs = [runs_by_id[test_id] for test_id in EXPECTED_TEST_ORDER]
        ids_in_order = list(EXPECTED_TEST_ORDER)
    else:
        ids_in_order = raw_input_test_ids

    tests = [
        validate_run(run, expected_provider_test_id=provider_mapping.get(str(run.get("test_id", "")).strip()))
        for run in runs
    ]
    if global_failures or any(test["independent_status"] == "fail" for test in tests):
        independent_status = "fail"
    elif any(test["independent_status"] == "incomplete" for test in tests):
        independent_status = "incomplete"
    else:
        independent_status = "pass"
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "agent_id": payload.get("agent_id"),
        "invocation_id": payload.get("invocation_id"),
        "independent_status": independent_status,
        "input_test_ids": ids_in_order,
        "raw_input_test_ids": raw_input_test_ids,
        "global_failures": global_failures,
        "provider_labels": {
            "status_entries": [
                {
                    "test_id": test.get("test_id"),
                    "test_run_id": test.get("test_run_id"),
                    "status": test.get("provider_status"),
                }
                for test in tests
            ],
            "condition_result_entries": [
                {
                    "test_id": test.get("test_id"),
                    "test_run_id": test.get("test_run_id"),
                    "condition_result": test.get("provider_condition_result"),
                }
                for test in tests
            ],
        },
        "tests": tests,
    }


def validate_partial_canary_payload(payload: dict[str, Any], mapping: dict[str, str] | None = None) -> dict[str, Any]:
    return validate_partial_test_payload(payload, partial_test_id="sim_040_basic_site_direct_price", mapping=mapping, validation_mode="partial_canary_basic_site")


def validate_partial_test_payload(
    payload: dict[str, Any],
    *,
    partial_test_id: str,
    mapping: dict[str, str] | None = None,
    validation_mode: str = "partial_test",
) -> dict[str, Any]:
    global_failures: list[str] = []
    provider_mapping = dict(mapping or {})
    provider_mapping.update(provider_test_id_mapping(payload.get("live_test_mapping") if isinstance(payload.get("live_test_mapping"), dict) else None))

    if partial_test_id not in EXPECTED_TESTS:
        global_failures.append(f"partial_test_id must be one known expected test id; found {partial_test_id!r}")
    if payload.get("agent_id") != EXPECTED_AGENT_ID:
        global_failures.append(f"agent_id must be {EXPECTED_AGENT_ID}")
    if payload.get("checkpoint_id") not in (None, "", CHECKPOINT_ID):
        global_failures.append(f"checkpoint_id must be {CHECKPOINT_ID}")
    runs_raw = payload.get("test_runs")
    if not isinstance(runs_raw, list):
        global_failures.append("payload.test_runs must be a list")
        runs_raw = []
    runs = [run for run in runs_raw if isinstance(run, dict)]
    if len(runs) != len(runs_raw):
        global_failures.append("all test_runs entries must be JSON objects")
    ids_in_order = [str(run.get("test_id", "")).strip() for run in runs]
    if ids_in_order != [partial_test_id]:
        global_failures.append(f"partial validation expects exactly {[partial_test_id]}, found {ids_in_order}")

    tests = [
        validate_run(run, expected_provider_test_id=provider_mapping.get(str(run.get("test_id", "")).strip()))
        for run in runs
    ]
    if global_failures or any(test["independent_status"] == "fail" for test in tests):
        independent_status = "fail"
    elif any(test["independent_status"] == "incomplete" for test in tests):
        independent_status = "incomplete"
    else:
        independent_status = "pass"
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "agent_id": payload.get("agent_id"),
        "invocation_id": payload.get("invocation_id"),
        "validation_mode": validation_mode,
        "partial_test_id": partial_test_id,
        "independent_status": independent_status,
        "input_test_ids": ids_in_order,
        "global_failures": global_failures,
        "provider_labels": {
            "status_entries": [
                {
                    "test_id": test.get("test_id"),
                    "test_run_id": test.get("test_run_id"),
                    "status": test.get("provider_status"),
                }
                for test in tests
            ],
            "condition_result_entries": [
                {
                    "test_id": test.get("test_id"),
                    "test_run_id": test.get("test_run_id"),
                    "condition_result": test.get("provider_condition_result"),
                }
                for test in tests
            ],
        },
        "tests": tests,
    }


def make_event(role: str, message: str) -> dict[str, Any]:
    return {"role": role, "message": message}


def make_run(test_id: str, agent_messages: list[str], user_messages: list[str]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    for index, user_message in enumerate(user_messages):
        events.append(make_event("user", user_message))
        if index < len(agent_messages):
            events.append(make_event("agent", agent_messages[index]))
    return {
        "test_id": test_id,
        "test_name": f"{CHECKPOINT_ID}::{test_id}",
        "test_run_id": f"run::{test_id}",
        "status": "passed",
        "condition_result": {"result": "pass"},
        "agent_responses": events,
    }


def valid_runs() -> list[dict[str, Any]]:
    return [
        make_run(
            "sim_040_capability_question_no_unprompted_price",
            ["Yes, we can build booking, CRM, and payments. The main split is whether you need a simple handoff or a real integration."],
            ["Can you add booking, CRM, and payments?"],
        ),
        make_run(
            "sim_040_free_mockup_question_no_paid_price",
            ["No payment or contract."],
            ["Is the mockup really free or is there a catch?"],
        ),
        make_run(
            "sim_040_basic_site_direct_price",
            ["A straightforward three-to-five-page local-business site is usually in the $900-$1,500 range, depending on the page count and content work."],
            ["What does a basic three-to-five-page local-business site cost?"],
        ),
        make_run(
            "sim_040_existing_site_request_form_add_on",
            ["If your existing site is compatible, adding a simple appointment-request form is usually $100-$250, depending on the routing and fields."],
            ["We already have a compatible site. What does it cost to add a simple appointment-request form?"],
        ),
        make_run(
            "sim_040_new_site_booking_whole_project",
            [
                "For a new straightforward site with a simple request form, that usually sits in the $900-$1,500 range, depending on the page count and content structure.",
                "If you want a live calendar integration as part of the new site, that usually moves the whole project toward the $4,000-$6,500 range because of the workflow and testing.",
            ],
            [
                "What would a new straightforward site with a simple request form cost?",
                "What about live calendar integration?",
            ],
        ),
        make_run(
            "sim_040_multi_feature_no_price_stacking",
            ["With booking, CRM, payments, service-area pages, and a blog in one new build, that likely lands in the $4,000-$6,500 range because the connected workflow is broader than a basic site."],
            ["I need a new site with booking, CRM, payments, service-area pages, and a blog. What's the total cost?"],
        ),
        make_run(
            "sim_040_direct_crm_integration_existing_site",
            ["On a compatible existing site, a direct CRM integration is usually $1,000-$2,500+ because the API, field mapping, and sync behavior need to be scoped."],
            ["We have an existing compatible site. What does a direct CRM integration cost?"],
        ),
        make_run(
            "sim_040_portal_requires_scope",
            ["A working parent portal is custom, so I would need to scope the accounts, data, permissions, security, and integrations before giving you a real number."],
            ["How much does a parent portal with accounts and progress dashboards cost?"],
        ),
        make_run(
            "sim_040_budget_fit_direct_answer",
            ["Yes, a $1,200 budget can fit a basic site if the scope stays in the $900-$1,500 band and the content is straightforward."],
            ["Our budget is $1,200. Does that fit a basic site?"],
        ),
        make_run(
            "sim_040_care_plan_only_when_asked",
            [
                "Yes, we can build the site and help keep it updated.",
                "For ongoing hosting and maintenance, the most relevant care plan is $79 per month if you just need updates, backups, and monitoring.",
            ],
            [
                "Can you build the site and help keep it updated?",
                "What do hosting and maintenance cost each month?",
            ],
        ),
    ]


def make_payload(runs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "invocation_id": "invocation-test",
        "agent_id": EXPECTED_AGENT_ID,
        "test_runs": runs,
    }


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_status(result: dict[str, Any], test_id: str) -> str | None:
    for test in result.get("tests", []):
        if test.get("test_id") == test_id:
            return str(test.get("independent_status"))
    return None


def failure_names(result: dict[str, Any], test_id: str) -> set[str]:
    for test in result.get("tests", []):
        if test.get("test_id") == test_id:
            return {item.get("name") for item in test.get("assertions", []) if item.get("passed") is False}
    return set()


def run_self_test() -> int:
    import capture_elevenlabs_040_test_invocation as capture

    assert_true(capture.CHECKPOINT_ID == CHECKPOINT_ID, "capture checkpoint id mismatch")
    assert_true(capture.EXPECTED_SYNTHETIC_EMAILS == set(), "040 capture must not whitelist synthetic emails")

    valid_result = validate_payload(make_payload(valid_runs()))
    assert_true(valid_result["independent_status"] == "pass", "valid 040 fixture should pass")
    for focused_valid in (
        "sim_040_existing_site_request_form_add_on",
        "sim_040_multi_feature_no_price_stacking",
        "sim_040_portal_requires_scope",
        "sim_040_care_plan_only_when_asked",
    ):
        assert_true(test_status(valid_result, focused_valid) == "pass", f"{focused_valid} valid fixture should pass")

    canary_cta_invalid = validate_partial_canary_payload(
        make_payload(
            [
                make_run(
                    "sim_040_basic_site_direct_price",
                    [
                        "A basic site is usually in the $900-$1,500 range, depending on content.",
                        "The lower end is when content is ready. The free mockup is a good next step, and I can send it over first.",
                    ],
                    [
                        "What does a basic website cost?",
                        "What makes it cost more or less?",
                    ],
                )
            ]
        )
    )
    assert_true("post_quote_price_followup_no_cta" in failure_names(canary_cta_invalid, EXPECTED_TEST_ORDER[2]), "partial canary must reject renewed mockup CTA during active price follow-up")

    canary_cta_valid = validate_partial_canary_payload(
        make_payload(
            [
                make_run(
                    "sim_040_basic_site_direct_price",
                    [
                        "A basic site is usually in the $900-$1,500 range, depending on content.",
                        "The lower end is when copy and photos are ready; it moves higher when we need to write, organize, or polish more pages.",
                    ],
                    [
                        "What does a basic website cost?",
                        "What makes it cost more or less?",
                    ],
                )
            ]
        )
    )
    assert_true(canary_cta_valid["independent_status"] == "pass", "partial canary should pass direct driver answer without CTA")

    raw_provider_id_runs = valid_runs()
    provider_mapping = []
    for index, run in enumerate(raw_provider_id_runs, start=1):
        source_id = str(run["test_id"])
        provider_id = f"test_provider_040_{index:02d}"
        run["provider_test_id"] = provider_id
        provider_mapping.append(
            {
                "source_test_id": source_id,
                "provider_test_id": provider_id,
                "provider_test_name": f"{CHECKPOINT_ID}::{source_id}",
            }
        )
    raw_provider_id_payload = make_payload(raw_provider_id_runs)
    raw_provider_id_payload["live_test_mapping"] = {"tests": provider_mapping}
    raw_provider_id_result = validate_payload(raw_provider_id_payload)
    assert_true(raw_provider_id_result["independent_status"] == "pass", "raw provider test_* IDs should reconcile through live_test_mapping")

    empty_response_runs = valid_runs()
    empty_response_runs[0]["agent_responses"] = []
    empty_response_result = validate_payload(make_payload(empty_response_runs))
    empty_response_failures = failure_names(empty_response_result, EXPECTED_TEST_ORDER[0])
    assert_true("incomplete_simulation" in empty_response_failures, "empty agent_responses must be classified as incomplete_simulation")
    assert_true("ordered_agent_responses_present" in empty_response_failures, "empty agent_responses must fail ordered response extraction")

    normalized_range_valid = valid_runs()
    normalized_range_valid[2]["agent_responses"] = [
        make_event("user", "What does a basic three-to-five-page local-business site cost?"),
        make_event("agent", "A straightforward site is usually in the $900 to $1,500 range, depending on the page count and content work."),
    ]
    normalized_range_result = validate_payload(make_payload(normalized_range_valid))
    assert_true(test_status(normalized_range_result, EXPECTED_TEST_ORDER[2]) == "pass", "equivalent to-separator approved range should pass")

    budget_affirmative_caveat_valid = valid_runs()
    budget_affirmative_caveat_valid[8]["agent_responses"] = [
        make_event("user", "Our budget is $1,200. Does that fit a basic site?"),
        make_event("agent", "Yes, $1,200 fits within $900-$1,500; the exact number depends on scope."),
    ]
    budget_affirmative_caveat_result = validate_payload(make_payload(budget_affirmative_caveat_valid))
    assert_true(test_status(budget_affirmative_caveat_result, EXPECTED_TEST_ORDER[8]) == "pass", "explicit affirmative fit with later scope caveat should pass")

    unprompted = valid_runs()
    unprompted[0]["agent_responses"] = [
        make_event("user", "Can you add booking, CRM, and payments?"),
        make_event("agent", "Yes, and that usually runs $4,000-$6,500."),
    ]
    unprompted_result = validate_payload(make_payload(unprompted))
    assert_true("unprompted_paid_price" in failure_names(unprompted_result, EXPECTED_TEST_ORDER[0]), "must detect unprompted paid price")

    portal_invalid = valid_runs()
    portal_invalid[7]["agent_responses"] = [
        make_event("user", "How much does a parent portal with accounts and progress dashboards cost?"),
        make_event("agent", "That would be around $6,500 maximum for a portal like that."),
    ]
    portal_invalid_result = validate_payload(make_payload(portal_invalid))
    assert_true("portal_no_numeric_price" in failure_names(portal_invalid_result, EXPECTED_TEST_ORDER[7]), "must reject numeric portal price")

    care_invalid = valid_runs()
    care_invalid[9]["agent_responses"] = [
        make_event("user", "Can you build the site and help keep it updated?"),
        make_event("agent", "Yes, and the care plan is $79 per month."),
        make_event("user", "What do hosting and maintenance cost each month?"),
        make_event("agent", "The most relevant plan is still $79 per month."),
    ]
    care_invalid_result = validate_payload(make_payload(care_invalid))
    assert_true("care_plan_only_after_ongoing_cost_intent" in failure_names(care_invalid_result, EXPECTED_TEST_ORDER[9]), "must reject early care-plan pricing")

    existing_invalid = valid_runs()
    existing_invalid[3]["agent_responses"] = [
        make_event("user", "We already have a compatible site. What does it cost to add a simple appointment-request form?"),
        make_event("agent", "That would usually be $900-$1,500 as part of the site."),
    ]
    existing_invalid_result = validate_payload(make_payload(existing_invalid))
    assert_true("existing_site_expected_add_on_range" in failure_names(existing_invalid_result, EXPECTED_TEST_ORDER[3]), "must reject whole-project pricing for existing-site add-on")

    multi_invalid = valid_runs()
    multi_invalid[5]["agent_responses"] = [
        make_event("user", "I need a new site with booking, CRM, payments, service-area pages, and a blog. What's the total cost?"),
        make_event("agent", "I would stack $900-$1,500 for the site plus $1,000-$2,500+ for CRM, so call it about $4,000 total."),
    ]
    multi_invalid_result = validate_payload(make_payload(multi_invalid))
    assert_true("no_arithmetic_total" in failure_names(multi_invalid_result, EXPECTED_TEST_ORDER[5]), "must reject arithmetic totals")

    extra_range_invalid = valid_runs()
    extra_range_invalid[2]["agent_responses"] = [
        make_event("user", "What does a basic three-to-five-page local-business site cost?"),
        make_event("agent", "A straightforward site is usually in the $900-$1,500 range, but some of these land around $2,000-$3,000 depending on extras."),
    ]
    extra_range_result = validate_payload(make_payload(extra_range_invalid))
    assert_true("no_unapproved_paid_price_ranges" in failure_names(extra_range_result, EXPECTED_TEST_ORDER[2]), "must reject unsupported extra dollar ranges")

    budget_negative_invalid = valid_runs()
    budget_negative_invalid[8]["agent_responses"] = [
        make_event("user", "Our budget is $1,200. Does that fit a basic site?"),
        make_event("agent", "No, $1,200 does not fit a basic site; the $900-$1,500 band is unrelated."),
    ]
    budget_negative_result = validate_payload(make_payload(budget_negative_invalid))
    budget_negative_failures = failure_names(budget_negative_result, EXPECTED_TEST_ORDER[8])
    assert_true("budget_fit_affirmative_answer_required" in budget_negative_failures, "must reject negative budget-fit polarity")
    assert_true("budget_fit_semantics" in budget_negative_failures, "must reject broken budget-fit semantics")

    budget_negated_bypass_invalid = valid_runs()
    budget_negated_bypass_invalid[8]["agent_responses"] = [
        make_event("user", "Our budget is $1,200. Does that fit a basic site?"),
        make_event("agent", "I don't think $1,200 fits a basic site; the $900-$1,500 band only works if scope changes."),
    ]
    budget_negated_bypass_result = validate_payload(make_payload(budget_negated_bypass_invalid))
    budget_negated_bypass_failures = failure_names(budget_negated_bypass_result, EXPECTED_TEST_ORDER[8])
    assert_true("budget_fit_affirmative_answer_required" in budget_negated_bypass_failures, "must reject negated budget-fit phrasing like don't think it fits")
    assert_true("budget_fit_semantics" in budget_negated_bypass_failures, "must reject negated budget-fit semantics like don't think it fits")

    for label, message in (
        ("maybe_can_fit", "Maybe $1,200 can fit a basic site; the $900-$1,500 range depends on scope."),
        ("might_fit", "$1,200 might fit a basic site within the $900-$1,500 range depending on scope."),
        ("possibly_fit", "It could possibly fit a basic site in the $900-$1,500 range depending on scope."),
        ("i_think_fit", "I think $1,200 fits within $900-$1,500, depending on scope."),
        ("not_sure_fit", "I'm not sure $1,200 fits a basic site even though the $900-$1,500 range exists."),
    ):
        hedged_budget_invalid = valid_runs()
        hedged_budget_invalid[8]["agent_responses"] = [
            make_event("user", "Our budget is $1,200. Does that fit a basic site?"),
            make_event("agent", message),
        ]
        hedged_budget_result = validate_payload(make_payload(hedged_budget_invalid))
        hedged_budget_failures = failure_names(hedged_budget_result, EXPECTED_TEST_ORDER[8])
        assert_true(
            "budget_fit_affirmative_answer_required" in hedged_budget_failures,
            f"{label} must fail budget_fit_affirmative_answer_required",
        )
        assert_true(
            "budget_fit_semantics" in hedged_budget_failures,
            f"{label} must fail budget_fit_semantics",
        )

    existing_frame_invalid = valid_runs()
    existing_frame_invalid[3]["agent_responses"] = [
        make_event("user", "We already have a compatible site. What does it cost to add a simple appointment-request form?"),
        make_event("agent", "For a new site, a simple appointment-request form is usually $100-$250 depending on the fields."),
    ]
    existing_frame_result = validate_payload(make_payload(existing_frame_invalid))
    assert_true("existing_site_add_on_classification" in failure_names(existing_frame_result, EXPECTED_TEST_ORDER[3]), "must reject wrong existing-site/add-on framing")

    existing_negated_clarification_valid = valid_runs()
    existing_negated_clarification_valid[3]["agent_responses"] = [
        make_event("user", "We already have a compatible site. What does it cost to add a simple appointment-request form?"),
        make_event("agent", "On your existing site, adding the form is usually $100-$250. This is not a new site package."),
    ]
    existing_negated_clarification_result = validate_payload(make_payload(existing_negated_clarification_valid))
    assert_true(test_status(existing_negated_clarification_result, EXPECTED_TEST_ORDER[3]) == "pass", "negated whole-site clarification should pass for existing-site add-on")

    existing_negated_whole_site_quote_valid = valid_runs()
    existing_negated_whole_site_quote_valid[3]["agent_responses"] = [
        make_event("user", "We already have a compatible site. What does it cost to add a simple appointment-request form?"),
        make_event("agent", "On your existing site, adding the form is usually $100-$250. This is not a whole-site quote."),
    ]
    existing_negated_whole_site_quote_result = validate_payload(make_payload(existing_negated_whole_site_quote_valid))
    assert_true(test_status(existing_negated_whole_site_quote_result, EXPECTED_TEST_ORDER[3]) == "pass", "negated whole-site quote clarification should pass for existing-site add-on")

    existing_affirmative_whole_site_invalid = valid_runs()
    existing_affirmative_whole_site_invalid[3]["agent_responses"] = [
        make_event("user", "We already have a compatible site. What does it cost to add a simple appointment-request form?"),
        make_event("agent", "On your existing site, adding the form is usually $100-$250, but this is a whole-site package quote."),
    ]
    existing_affirmative_whole_site_result = validate_payload(make_payload(existing_affirmative_whole_site_invalid))
    assert_true("existing_site_add_on_classification" in failure_names(existing_affirmative_whole_site_result, EXPECTED_TEST_ORDER[3]), "must still reject affirmative whole-site/package framing")

    print("self-test: pass")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return run_self_test()

    try:
        payload = capture_payload(read_json(args.input))
        mapping_document: dict[str, Any] | None = None
        mapping_path = args.mapping
        if mapping_path is None and args.input is not None:
            sibling = args.input.parent / "live_test_mapping.json"
            if sibling.is_file():
                mapping_path = sibling
        if mapping_path is not None:
            mapping_document = read_json(mapping_path)
        if args.partial_test_id:
            summary = validate_partial_test_payload(payload, partial_test_id=args.partial_test_id, mapping=provider_test_id_mapping(mapping_document))
        elif args.partial_canary:
            summary = validate_partial_canary_payload(payload, provider_test_id_mapping(mapping_document))
        else:
            summary = validate_payload(payload, provider_test_id_mapping(mapping_document))
    except ValueError as exc:
        summary = {
            "checkpoint_id": CHECKPOINT_ID,
            "agent_id": None,
            "invocation_id": None,
            "independent_status": "fail",
            "input_test_ids": [],
            "global_failures": [str(exc)],
            "provider_labels": {"status_entries": [], "condition_result_entries": []},
            "tests": [],
        }

    rendered = json.dumps(summary, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if summary["independent_status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
