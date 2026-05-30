from __future__ import annotations

from collections import Counter, defaultdict
import math
import re
from typing import Any

from runtime.action_selector.action_selector_contract import (
    ActionSelectorInput,
    ActionSelectorOutput,
    action_labels,
    normalize_text,
    validate_selector_output,
)


def _contains(text: str, *needles: str) -> bool:
    return any(needle in text for needle in needles)


def _regex(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.I) is not None


def _boundary_sensitive_product_claim_question(text: str) -> bool:
    question_like = text.startswith(
        (
            "can ",
            "could ",
            "does ",
            "do ",
            "is ",
            "are ",
            "will ",
            "would ",
            "how ",
            "what if ",
            "what about ",
        )
    )
    if not question_like:
        return False
    claim_pressure = _contains(
        text,
        "guarantee",
        "guaranteed",
        "prove",
        "proof",
        "compliance",
        "compliant",
        "certification",
        "certified",
    )
    exact_security_verification = _contains(text, "security", "secure") and _contains(
        text,
        "exact",
        "exactly",
        "verify",
        "verification",
        "validate",
        "validated",
        "prove",
        "proof",
        "guarantee",
        "certify",
        "certified",
        "compliance",
        "compliant",
    )
    secure_integration_claim = (
        _contains(text, "integrate", "integration", "setup")
        and _contains(text, "salesforce", "hubspot", "crm")
        and _contains(text, "security", "secure")
    )
    return claim_pressure or exact_security_verification or secure_integration_claim


def _context_text(payload: dict[str, Any]) -> str:
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    parts = [
        payload.get("buyer_utterance_text"),
        context.get("buyer_utterance_text"),
        context.get("normalized_buyer_text"),
        context.get("memory_summary"),
        context.get("known_plan_interest"),
        context.get("known_team_status"),
        context.get("buyer_emotion"),
        context.get("buyer_confusion_level"),
        context.get("buyer_skepticism_level"),
        context.get("buyer_engagement_level"),
        " ".join(str(item) for item in context.get("known_use_case", []) if str(item or "").strip())
        if isinstance(context.get("known_use_case"), list)
        else "",
        " ".join(str(item) for item in context.get("known_tools", []) if str(item or "").strip())
        if isinstance(context.get("known_tools"), list)
        else "",
    ]
    return normalize_text(" ".join(str(part or "") for part in parts))


def payload_to_selector_input(payload: dict[str, Any]) -> ActionSelectorInput:
    context = payload.get("context") if isinstance(payload.get("context"), dict) else payload
    buyer_text = str(payload.get("buyer_utterance_text") or context.get("buyer_utterance_text") or "")
    merged = {
        "buyer_utterance_text": buyer_text,
        "normalized_buyer_text": context.get("normalized_buyer_text") or normalize_text(buyer_text),
        "memory_summary": context.get("memory_summary") or "",
        "known_use_case": context.get("known_use_case") or [],
        "known_tools": context.get("known_tools") or [],
        "known_plan_interest": context.get("known_plan_interest") or "",
        "known_team_status": context.get("known_team_status") or "",
        "buyer_emotion": context.get("buyer_emotion") or "",
        "buyer_confusion_level": context.get("buyer_confusion_level") or "",
        "buyer_skepticism_level": context.get("buyer_skepticism_level") or "",
        "buyer_engagement_level": context.get("buyer_engagement_level") or "",
        "last_action_id": context.get("last_action_id") or "",
        "last_answered_topic": context.get("last_answered_topic") or "",
        "safety_boundary_detected": context.get("safety_boundary_detected") is True,
    }
    return ActionSelectorInput.from_payload(merged)


class RuleBasedActionSelector:
    baseline_name = "rule_based"

    def __init__(self) -> None:
        self.allowed_labels = set(action_labels())

    def _output(
        self,
        action_id: str,
        confidence: float,
        reasons: list[str],
        matched: list[str],
        *,
        requires_clarification: bool = False,
        safety_block: bool = False,
        fallback_required: bool = False,
    ) -> ActionSelectorOutput:
        if action_id not in self.allowed_labels:
            action_id = "ask_use_case_gap"
            fallback_required = True
            reasons = [*reasons, "uncontrolled_action_fallback"]
        output = ActionSelectorOutput(
            action_id=action_id,
            confidence=confidence,
            reasons=reasons,
            matched_features=matched,
            requires_clarification=requires_clarification,
            safety_block=safety_block,
            fallback_required=fallback_required,
        )
        failures = validate_selector_output(output)
        if failures:
            return ActionSelectorOutput(
                action_id="ask_use_case_gap",
                confidence=0.2,
                reasons=["selector_output_validation_failed", *failures],
                matched_features=matched,
                fallback_required=True,
            )
        return output

    def select(self, payload: dict[str, Any]) -> ActionSelectorOutput:
        selector_input = payload_to_selector_input(payload)
        text = selector_input.normalized_buyer_text
        full_text = _context_text(payload)
        matched: list[str] = []
        if " and " in f" {text} ":
            matched.append("relation:and")
        if " or " in f" {text} ":
            matched.append("relation:or")
        if "voice" in text:
            matched.append("mode:voice")
        if "writing" in text:
            matched.append("mode:writing")
        if _contains(text, "not a team", "not team", "by myself", "just me", "personal use only"):
            matched.append("team:not_team")

        if _contains(text, "raw transcript", "exact call transcript", "raw audio", "what i say", "store what i say", "train on my data", "call data", "privacy", "data retention"):
            return self._output(
                "answer_privacy_boundary",
                0.94,
                ["privacy_or_transcript_boundary"],
                matched + ["safety:privacy"],
                safety_block=True,
            )

        if selector_input.safety_boundary_detected or _regex(text, r"\b(buy|purchase|book|schedule|send|email|update|log|create)\b.*\b(for me|crm|calendar|email|invite|account|ticket|purchase|plus)\b"):
            return self._output(
                "respect_boundary",
                0.96,
                ["unsupported_side_effect_or_boundary_first"],
                matched + ["safety:side_effect"],
                safety_block=True,
            )

        if _boundary_sensitive_product_claim_question(text):
            return self._output(
                "respect_boundary",
                0.9,
                ["boundary_sensitive_product_claim_question"],
                matched + ["safety:product_claim_boundary"],
                safety_block=True,
            )

        if _contains(text, "already told you", "i told you", "i said that already", "already said"):
            return self._output(
                "repair_already_told_you",
                0.96,
                ["buyer_reports_repeated_question"],
                matched + ["repair:already_told_you"],
            )

        if _contains(text, "you just asked", "you already asked", "asked that", "same question", "repeat yourself"):
            return self._output(
                "avoid_repetition_rephrase",
                0.94,
                ["repeat_risk_signal"],
                matched + ["repair:avoid_repetition"],
            )

        if _regex(text, r"\b(no|not|actually)\b.{0,24}\b(i said|said|meant|mean)\b") or (
            not text.startswith("why not") and _regex(text, r"\bnot\b.{0,24}\b(cloud|team|writing|voice)\b")
        ):
            return self._output(
                "repair_buyer_correction",
                0.86,
                ["buyer_correction_marker"],
                matched + ["repair:buyer_correction"],
            )

        if ("cloud" in text and "claude" in text) or _contains(text, "chat gbt", "chad gpt", "chat gpt maybe"):
            return self._output(
                "repair_asr_uncertainty",
                0.93,
                ["ambiguous_tool_or_asr"],
                matched + ["repair:asr_uncertainty"],
                requires_clarification=True,
            )

        if _regex(text, r"\b(thanks|thank you|that works|i will check|sounds good|sounds fine|ok i will|look later)\b") and not text.endswith("?"):
            return self._output("terminal_close", 0.9, ["terminal_acceptance_or_thanks"], matched + ["close:terminal"])

        if _contains(
            text,
            "not interested",
            "free plan is enough",
            "free is enough",
            "barely use ai",
            "do not need",
            "don't need",
            "wrong product",
            "no paid plan fits",
            "phone plan",
            "billing support",
            "not buying",
            "do not want to switch",
        ) or _regex(text, r"\b(gmail|calendar|spreadsheet|email)\b.*\bnot chatgpt\b"):
            return self._output("disqualify_no_fit", 0.93, ["no_fit_or_wrong_product"], matched + ["fit:no"])

        if _contains(text, "from openai", "are you openai", "affiliation", "who are you", "where is this recommendation", "source"):
            return self._output(
                "answer_source_or_affiliation",
                0.9,
                ["source_or_affiliation_question"],
                matched + ["topic:source_affiliation"],
            )

        if _contains(text, "sign up", "signup", "get started", "start using", "where do i start", "close this myself online"):
            return self._output("answer_signup_path", 0.92, ["signup_path_question"], matched + ["topic:signup"])

        if _contains(text, "upgrade later", "upgrade midcycle", "move up later", "change plan", "change plans", "start lower", "downgrade", "switch later"):
            return self._output("answer_plan_change", 0.91, ["plan_change_question"], matched + ["topic:plan_change"])

        if _contains(text, "expensive", "too much", "costs too much", "worth it", "pricey", "price matters"):
            return self._output("handle_price_objection", 0.9, ["price_value_objection"], matched + ["objection:price"])

        if _regex(text, r"\b(how much|what.*cost|price|pricing|cost)\b") and not _contains(text, "worth it", "expensive", "too much"):
            return self._output("answer_price", 0.92, ["direct_price_question"], matched + ["topic:price"])

        if (
            _regex(text, r"\bwhy not\b.*\b(claude|gemini|copilot|perplexity|other ai)\b")
            or _regex(text, r"\b(claude|gemini|copilot|perplexity)\b.*\binstead\b")
            or _regex(text, r"\b(chatgpt|current tool|claude|gemini|copilot|perplexity)\b.*\b(vs|versus|why switch|switch)\b")
            or _regex(text, r"\b(claude|gemini|copilot)\b.*\b(enough|covers)\b")
        ):
            return self._output(
                "handle_competitor_context",
                0.9,
                ["competitor_comparison_or_objection"],
                matched + ["objection:competitor"],
            )

        if _contains(text, "model vs subscription", "subscription vs model") or (_contains(text, "model") and _contains(text, "subscription", "plan")):
            return self._output(
                "explain_subscription_vs_model",
                0.89,
                ["subscription_model_confusion"],
                matched + ["topic:model_vs_subscription"],
            )

        if _contains(text, "what are the plans", "explain the plans", "plan categories", "plans actually", "options"):
            return self._output("orient_plan_options", 0.88, ["plan_orientation_question"], matched + ["topic:plan_options"])

        if _contains(text, "not a team", "not team", "by myself", "just me", "personal use only", "no company", "personal"):
            return self._output(
                "clarify_team_vs_individual",
                0.91,
                ["individual_not_team_context"],
                matched + ["team:individual"],
            )

        if _contains(text, "team", "employees", "company", "sso", "procurement", "enterprise", "admin controls", "legal review", "security controls"):
            return self._output(
                "recommend_business_or_enterprise",
                0.9,
                ["team_or_enterprise_context"],
                matched + ["team:business_enterprise"],
            )

        if _contains(text, "plus vs pro", "plus or pro"):
            return self._output("compare_plus_vs_pro", 0.9, ["plus_vs_pro_question"], matched + ["topic:plus_vs_pro"])

        if _contains(text, "which pro", "pro tier", "choose pro", "should i choose pro", "is pro better"):
            return self._output("compare_pro_tiers", 0.87, ["pro_choice_question"], matched + ["topic:pro_choice"])

        if _contains(text, "plus enough", "stay on plus", "would plus be enough", "is plus enough", "can i stay on plus"):
            return self._output("recommend_plus", 0.84, ["plus_sufficiency_question"], matched + ["topic:plus_fit"])

        if (_contains(text, "recommend one", "pick a plan", "which plan") and _contains(text, "daily", "every day", "heavy", "hit limits")) or _contains(full_text, "heavy_daily_use"):
            return self._output("recommend_pro", 0.86, ["heavy_individual_use_plan_recommendation"], matched + ["recommend:pro"])

        if _contains(text, "confused", "what are you asking", "what do you mean", "unclear"):
            return self._output(
                "clarify_question_scope",
                0.82,
                ["confused_or_unclear_question_scope"],
                matched + ["clarify:question_scope"],
                requires_clarification=True,
            )

        if _contains(text, "claude", "chatgpt", "gemini", "copilot") and _contains(text, "use"):
            return self._output("ask_use_case_gap", 0.84, ["current_tool_context"], matched + ["topic:current_tool"])

        if _contains(text, "coding", "code", "writing", "voice", "research", "workflow"):
            return self._output("ask_usage_intensity", 0.82, ["use_case_known_intensity_unknown"], matched + ["topic:use_case"])

        if not text:
            return self._output(
                "clarify_question_scope",
                0.45,
                ["empty_or_missing_buyer_text"],
                matched + ["fallback:empty_text"],
                requires_clarification=True,
                fallback_required=True,
            )

        return self._output(
            "ask_use_case_gap",
            0.55,
            ["default_diagnostic_next_step"],
            matched + ["fallback:diagnostic"],
            fallback_required=True,
        )


def token_set(text: str) -> set[str]:
    return {token for token in normalize_text(text).split() if len(token) > 1}


class StandardLibraryNearestLabelSelector:
    baseline_name = "nearest_label_stdlib"

    def __init__(self) -> None:
        self.label_tokens: dict[str, Counter[str]] = {}
        self.default_label = "ask_use_case_gap"

    def fit(self, rows: list[dict[str, Any]]) -> "StandardLibraryNearestLabelSelector":
        buckets: dict[str, Counter[str]] = defaultdict(Counter)
        label_counts: Counter[str] = Counter()
        for row in rows:
            label = str(row.get("target_action_id") or "")
            if not label:
                continue
            label_counts[label] += 1
            text = _context_text(row)
            buckets[label].update(token_set(text))
        self.label_tokens = dict(buckets)
        if label_counts:
            self.default_label = label_counts.most_common(1)[0][0]
        return self

    def select(self, payload: dict[str, Any]) -> ActionSelectorOutput:
        text_tokens = token_set(_context_text(payload))
        best_label = self.default_label
        best_score = 0.0
        for label, counts in self.label_tokens.items():
            if not counts:
                continue
            overlap = sum(counts[token] for token in text_tokens)
            denom = math.sqrt(sum(value * value for value in counts.values())) or 1.0
            score = overlap / denom
            if score > best_score:
                best_score = score
                best_label = label
        confidence = min(0.85, max(0.25, best_score / 4.0))
        return ActionSelectorOutput(
            action_id=best_label,
            confidence=confidence,
            reasons=["standard_library_nearest_label"],
            matched_features=[f"token_score:{best_score:.4f}"],
            fallback_required=best_score <= 0,
        )


class SklearnActionSelector:
    baseline_name = "sklearn_tfidf_logistic_regression"

    def __init__(self) -> None:
        self.available = False
        self.unavailable_reason = ""
        self.vectorizer: Any = None
        self.classifier: Any = None
        self.classes_: list[str] = []

    def fit(self, rows: list[dict[str, Any]]) -> "SklearnActionSelector":
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.linear_model import LogisticRegression
        except Exception as exc:  # pragma: no cover - depends on local environment
            self.available = False
            self.unavailable_reason = f"scikit-learn unavailable: {exc}"
            return self

        train_texts = [_context_text(row) for row in rows]
        labels = [str(row.get("target_action_id") or "") for row in rows]
        filtered = [(text, label) for text, label in zip(train_texts, labels) if text and label]
        if len({label for _text, label in filtered}) < 2:
            self.available = False
            self.unavailable_reason = "fewer than two labels in training data"
            return self
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=8000)
        matrix = self.vectorizer.fit_transform([text for text, _label in filtered])
        self.classifier = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=13)
        self.classifier.fit(matrix, [label for _text, label in filtered])
        self.classes_ = [str(label) for label in self.classifier.classes_]
        self.available = True
        self.unavailable_reason = ""
        return self

    def select(self, payload: dict[str, Any]) -> ActionSelectorOutput:
        if not self.available or self.vectorizer is None or self.classifier is None:
            return ActionSelectorOutput(
                action_id="ask_use_case_gap",
                confidence=0.2,
                reasons=[self.unavailable_reason or "sklearn_selector_not_fit"],
                matched_features=[],
                fallback_required=True,
            )
        matrix = self.vectorizer.transform([_context_text(payload)])
        predicted = str(self.classifier.predict(matrix)[0])
        confidence = 0.5
        matched = ["model:tfidf_logistic_regression"]
        if hasattr(self.classifier, "predict_proba"):
            probabilities = self.classifier.predict_proba(matrix)[0]
            best = max(float(value) for value in probabilities)
            confidence = best
            matched.append(f"probability:{best:.4f}")
        return ActionSelectorOutput(
            action_id=predicted,
            confidence=confidence,
            reasons=["sklearn_tfidf_logistic_regression"],
            matched_features=matched,
            fallback_required=False,
        )
