"""No-provider ElevenLabs prosody mapping prototype.

This module maps internal prosody plans to reviewable metadata and shaped text.
It does not import provider SDKs, call APIs, generate audio, or wire into live
runtime behavior.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).resolve().parent
POLICY_PATH = CONFIG_DIR / "elevenlabs_prosody_mapping_policy.json"
RAW_TAG_RE = re.compile(r"\[[^\]\n]{2,80}\]")
URL_RE = re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE)
LABEL_RE = re.compile(
    r"\b(?:clarity|tone|sales|source|unsafe|emotion_response|pacing|pause|repair|boundary|trust|closing|plan)\.[a-z0-9_.-]+",
    re.IGNORECASE,
)
INTERNAL_MARKERS = (
    "classifier",
    "confidence score",
    "internal label",
    "prosody label",
    "fish tag",
    "mapping layer",
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def load_elevenlabs_mapping_policy() -> dict[str, Any]:
    return _load_json(POLICY_PATH)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _sentence_split(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text.strip())
    if not clean:
        return []
    parts = re.split(r"(?<=[.!?])\s+", clean)
    return [part.strip() for part in parts if part.strip()]


def _ensure_terminal_punctuation(sentence: str, terminal: str = ".") -> str:
    sentence = sentence.strip()
    if not sentence:
        return sentence
    if sentence[-1] in ".!?":
        return sentence
    return f"{sentence}{terminal}"


def _split_long_sentence(sentence: str, max_words: int) -> list[str]:
    words = sentence.split()
    if len(words) <= max_words:
        return [_ensure_terminal_punctuation(sentence)]
    chunks: list[str] = []
    current: list[str] = []
    connectors = {"and", "but", "so", "because", "then", "while"}
    for word in words:
        stripped = word.strip(",;:")
        if len(current) >= max_words or (len(current) >= max_words - 4 and stripped.lower() in connectors):
            chunks.append(_ensure_terminal_punctuation(" ".join(current).strip(",;: ")))
            current = []
        current.append(word)
    if current:
        chunks.append(_ensure_terminal_punctuation(" ".join(current).strip(",;: ")))
    return chunks


def _labels(plan: dict[str, Any]) -> set[str]:
    return {str(value) for value in _as_list(plan.get("selected_prosody_labels"))}


def _max_words_for_plan(plan: dict[str, Any]) -> int:
    labels = _labels(plan)
    pace = str(plan.get("pace") or "").lower()
    if "clarity.one_idea_per_sentence" in labels or "clarity.short_sentence" in labels:
        return 14
    if "pacing.slow_down_for_confusion" in labels or pace in {"slow", "slower"}:
        return 16
    if "closing.concise_final_sentence" in labels or str(plan.get("voice_intent")) == "close":
        return 18
    return 22


def _sanitize_spoken_text(text: str) -> str:
    text = RAW_TAG_RE.sub("", text)
    text = URL_RE.sub("the official site", text)
    text = LABEL_RE.sub("", text)
    for marker in INTERNAL_MARKERS:
        text = re.sub(re.escape(marker), "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.!?])", r"\1", text)
    text = re.sub(r"!{2,}", ".", text)
    text = text.replace("...", ".")
    return text


def _remove_extra_questions(text: str, plan: dict[str, Any]) -> str:
    labels = _labels(plan)
    is_terminal = (
        "closing.concise_final_sentence" in labels
        or "closing.no_new_question" in labels
        or str(plan.get("voice_intent")) in {"close", "final_goodbye"}
    )
    boundary = any(label.startswith("boundary.") for label in labels)
    already_told = "repair.acknowledge_already_told_you" in labels
    if not (is_terminal or boundary or already_told):
        return text
    return text.replace("?", ".")


def _style_prompt_hint(plan: dict[str, Any]) -> str:
    labels = _labels(plan)
    pace = str(plan.get("pace") or "medium").replace("_", " ")
    warmth = str(plan.get("warmth") or "neutral warm").replace("_", " ")
    confidence = str(plan.get("confidence") or "calm").replace("_", " ")
    energy = str(plan.get("energy") or "medium").replace("_", " ")
    family = "clear conversational delivery"
    if any(label.startswith("boundary.") for label in labels):
        family = "respectful boundary-aware delivery"
    elif any(label.startswith("source.") or label.startswith("trust.") for label in labels):
        family = "transparent factual delivery"
    elif "clarity.one_idea_per_sentence" in labels or "pacing.slow_down_for_confusion" in labels:
        family = "patient explanatory delivery"
    elif "closing.concise_final_sentence" in labels:
        family = "brief final delivery"
    return f"{family}; {pace} pace; {warmth} warmth; {confidence} confidence; {energy} energy."


def _voice_settings_hint(plan: dict[str, Any]) -> dict[str, str]:
    pace = str(plan.get("pace") or "medium").lower()
    energy = str(plan.get("energy") or "medium").lower()
    confidence = str(plan.get("confidence") or "calm").lower()
    if pace in {"slow", "slower"}:
        pace_hint = "slightly_slower"
    elif pace in {"fast", "direct"}:
        pace_hint = "slightly_faster_but_clear"
    else:
        pace_hint = "natural"
    stability = "medium_high" if confidence in {"calm", "grounded", "steady"} else "medium"
    style = "low" if energy in {"low", "calm"} else "moderate"
    return {
        "pace": pace_hint,
        "stability": stability,
        "style": style,
        "similarity_boost": "unchanged",
        "speaker_boost": "unchanged",
    }


def _pause_punctuation_plan(shaped_text: str, plan: dict[str, Any]) -> dict[str, Any]:
    labels = _labels(plan)
    punctuation = []
    if "." in shaped_text:
        punctuation.append("period_sentence_breaks")
    if "," in shaped_text:
        punctuation.append("comma_clause_breaks")
    if "pause.pause_before_price" in labels or "pause.pause_after_price" in labels:
        intent = "use sentence breaks around price or value framing"
    elif any(label.startswith("boundary.") for label in labels):
        intent = "use a calm final sentence after the boundary"
    else:
        intent = "use ordinary punctuation only"
    return {
        "pause_policy": plan.get("pause_policy", "none"),
        "punctuation_used": punctuation or ["plain_sentence_endings"],
        "intent": intent,
        "raw_tags_used": False,
    }


def _emphasis_terms(plan: dict[str, Any], shaped_text: str) -> list[str]:
    text_lower = shaped_text.lower()
    terms: list[str] = []
    for value in _as_list(plan.get("emphasis_terms")):
        term = str(value).strip()
        if not term or RAW_TAG_RE.search(term) or LABEL_RE.search(term):
            continue
        if term.lower() in text_lower:
            terms.append(term)
    if not terms:
        for candidate in ("privacy", "price", "value", "Plus", "Pro", "official", "upgrade", "team"):
            if candidate.lower() in text_lower:
                terms.append(candidate)
    deduped: list[str] = []
    for term in terms:
        if term not in deduped:
            deduped.append(term)
    return deduped[:4]


def shape_text_for_voice(base_text: str, prosody_plan: dict[str, Any]) -> dict[str, Any]:
    sanitized = _sanitize_spoken_text(base_text)
    max_words = _max_words_for_plan(prosody_plan)
    shaped_sentences: list[str] = []
    for sentence in _sentence_split(sanitized):
        shaped_sentences.extend(_split_long_sentence(sentence, max_words))
    shaped_text = " ".join(shaped_sentences)
    shaped_text = _remove_extra_questions(_sanitize_spoken_text(shaped_text), prosody_plan)
    return {
        "original_text": base_text,
        "shaped_text": shaped_text,
        "pause_punctuation_plan": _pause_punctuation_plan(shaped_text, prosody_plan),
        "emphasis_terms": _emphasis_terms(prosody_plan, shaped_text),
    }


def map_prosody_plan_to_elevenlabs_hints(prosody_plan: dict[str, Any], base_text: str) -> dict[str, Any]:
    shaped = shape_text_for_voice(base_text, prosody_plan)
    mapped = {
        "original_text": shaped["original_text"],
        "shaped_text": shaped["shaped_text"],
        "style_prompt_hint": _style_prompt_hint(prosody_plan),
        "voice_settings_hint": _voice_settings_hint(prosody_plan),
        "pause_punctuation_plan": shaped["pause_punctuation_plan"],
        "emphasis_terms": shaped["emphasis_terms"],
        "safety_warnings": [],
        "raw_fish_tags_present": False,
        "internal_labels_exposed": False,
        "provider_call_required": False,
        "live_wiring_allowed": False,
    }
    mapped["safety_warnings"] = validate_elevenlabs_prosody_mapping(mapped)
    mapped["raw_fish_tags_present"] = any(has_raw for has_raw in (bool(RAW_TAG_RE.search(mapped["shaped_text"])),))
    mapped["internal_labels_exposed"] = bool(LABEL_RE.search(mapped["shaped_text"]))
    return mapped


def validate_elevenlabs_prosody_mapping(mapped: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    shaped_text = str(mapped.get("shaped_text") or "")
    style_prompt = str(mapped.get("style_prompt_hint") or "")
    if not shaped_text:
        warnings.append("shaped_text is empty")
    if RAW_TAG_RE.search(shaped_text):
        warnings.append("shaped_text contains a raw bracket tag")
    if LABEL_RE.search(shaped_text):
        warnings.append("shaped_text exposes an internal label id")
    if URL_RE.search(shaped_text):
        warnings.append("shaped_text contains a raw URL")
    lowered = shaped_text.lower()
    for marker in INTERNAL_MARKERS:
        if marker in lowered:
            warnings.append(f"shaped_text exposes internal marker: {marker}")
    unsafe_style_terms = ("manipulative", "fake laughter", "pressure them", "must buy", "guarantee outcome")
    if any(term in style_prompt.lower() for term in unsafe_style_terms):
        warnings.append("style_prompt_hint contains unsafe instruction language")
    if not isinstance(mapped.get("voice_settings_hint"), dict) or not mapped.get("voice_settings_hint"):
        warnings.append("voice_settings_hint is missing")
    for key in ("provider_call_required", "live_wiring_allowed"):
        if mapped.get(key) is not False:
            warnings.append(f"{key} must be false")
    return warnings
