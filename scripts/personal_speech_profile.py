#!/usr/bin/env python3
from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROFILE_ID = "VOICE-029-local-speech-profile-learning"

FILLER_MARKERS = {
    "en": ["so", "um", "uh", "erm", "okay", "like", "you know", "basically"],
    "de": ["also", "aeh", "aehm", "hm", "genau", "na ja"],
}

REPAIR_MARKERS = {
    "en": ["i mean", "what i mean", "let me rephrase", "what i am trying to say", "trying to say"],
    "de": ["ich meine", "anders gesagt", "genauer gesagt", "ich sage es so"],
}

PAUSE_MARKERS = ["...", "[pause]", "(pause)", "--", "[short pause]", "short pause"]

LANGUAGE_HINTS = {
    "de": [" ich ", " und ", " nicht ", " aber ", " also ", " eine ", " ist ", " natuerlich "],
    "en": [" i ", " the ", " and ", " but ", " what ", " should ", " would ", " actually "],
}


@dataclass(frozen=True)
class SpeechSample:
    sample_id: str
    language: str
    text: str
    source: str


def normalize_for_matching(text: str) -> str:
    normalized = text.lower()
    replacements = {
        "\u00e4": "ae",
        "\u00f6": "oe",
        "\u00fc": "ue",
        "\u00df": "ss",
    }
    for before, after in replacements.items():
        normalized = normalized.replace(before, after)
    return f" {normalized} "


def normalize_language(language: str | None, text: str = "") -> str:
    if language and str(language).lower().startswith("de"):
        return "de"
    if language and str(language).lower().startswith("en"):
        return "en"
    normalized = normalize_for_matching(text)
    scores = {
        code: sum(1 for hint in hints if hint in normalized)
        for code, hints in LANGUAGE_HINTS.items()
    }
    return "de" if scores["de"] > scores["en"] else "en"


def count_marker(text: str, marker: str) -> int:
    normalized = normalize_for_matching(text)
    marker_pattern = re.escape(marker)
    return len(re.findall(rf"(?<![a-z]){marker_pattern}(?![a-z])", normalized))


def count_markers(text: str, markers: list[str]) -> tuple[int, dict[str, int]]:
    counts = {marker: count_marker(text, marker) for marker in markers}
    return sum(counts.values()), {marker: count for marker, count in counts.items() if count > 0}


def count_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z']+", normalize_for_matching(text)))


def count_sentences(text: str) -> int:
    sentences = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    return max(1, len(sentences))


def count_contractions(text: str) -> int:
    return len(re.findall(r"\b[A-Za-z]+'[A-Za-z]+\b", text))


def count_pause_markers(text: str) -> tuple[int, dict[str, int]]:
    normalized = normalize_for_matching(text)
    counts: dict[str, int] = {}
    for marker in PAUSE_MARKERS:
        count = normalized.count(marker)
        if count:
            counts[marker] = count
    return sum(counts.values()), counts


def top_markers(marker_counts: dict[str, int], limit: int = 5) -> list[dict[str, Any]]:
    return [
        {"marker": marker, "count": count}
        for marker, count in sorted(marker_counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def merge_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def analyze_language_samples(language: str, samples: list[SpeechSample]) -> dict[str, Any]:
    word_count = 0
    sentence_count = 0
    filler_count = 0
    repair_count = 0
    contraction_count = 0
    pause_count = 0
    filler_counts: dict[str, int] = {}
    repair_counts: dict[str, int] = {}
    pause_counts: dict[str, int] = {}

    for sample in samples:
        text = sample.text
        word_count += count_words(text)
        sentence_count += count_sentences(text)
        contraction_count += count_contractions(text)
        sample_filler_count, sample_filler_counts = count_markers(text, FILLER_MARKERS[language])
        sample_repair_count, sample_repair_counts = count_markers(text, REPAIR_MARKERS[language])
        sample_pause_count, sample_pause_counts = count_pause_markers(text)
        filler_count += sample_filler_count
        repair_count += sample_repair_count
        pause_count += sample_pause_count
        merge_counts(filler_counts, sample_filler_counts)
        merge_counts(repair_counts, sample_repair_counts)
        merge_counts(pause_counts, sample_pause_counts)

    words_per_sentence = round(word_count / max(1, sentence_count), 2)
    filler_rate = round((filler_count / max(1, word_count)) * 100, 2)
    repair_rate = round((repair_count / max(1, word_count)) * 100, 2)
    pause_rate = round((pause_count / max(1, sentence_count)), 2)
    return {
        "sample_count": len(samples),
        "word_count": word_count,
        "sentence_count": sentence_count,
        "avg_words_per_sentence": words_per_sentence,
        "filler_marker_count": filler_count,
        "filler_rate_per_100_words": filler_rate,
        "repair_marker_count": repair_count,
        "repair_rate_per_100_words": repair_rate,
        "contraction_count": contraction_count,
        "pause_marker_count": pause_count,
        "pause_markers_per_sentence": pause_rate,
        "top_filler_markers": top_markers(filler_counts),
        "top_repair_markers": top_markers(repair_counts),
        "pause_marker_summary": top_markers(pause_counts),
    }


def build_runtime_profile_proposal(language_profiles: dict[str, Any]) -> dict[str, Any]:
    preferred_languages = sorted(language_profiles)
    max_filler_rate = max(
        (profile["filler_rate_per_100_words"] for profile in language_profiles.values()),
        default=0,
    )
    suggested_filler_intensity = "low" if max_filler_rate <= 3 else "medium"
    return {
        "apply_to_runtime_by_default": False,
        "requires_human_review": True,
        "safe_next_step": "Review the abstract profile, then manually map stable patterns into campaign-level voice settings.",
        "speech_realism": {
            "suggested_filler_intensity": suggested_filler_intensity,
            "preferred_placement": "sentence_or_thought_boundary",
            "avoid_mid_clause_insertion": True,
            "languages_observed": preferred_languages,
        },
        "speech_imperfections": {
            "enable_only_after_review": True,
            "suggested_max_imperfections_per_response": 1,
            "preferred_types": ["clarifying_rephrase", "soft_restart", "breath_pause"],
            "protected_text_stays_exact": True,
        },
        "not_inferred": [
            "identity",
            "speaker voiceprint",
            "raw transcript examples",
            "private personal facts",
        ],
    }


def summarize_samples(samples: list[SpeechSample]) -> dict[str, Any]:
    languages: dict[str, int] = {}
    sources: dict[str, int] = {}
    for sample in samples:
        languages[sample.language] = languages.get(sample.language, 0) + 1
        sources[sample.source] = sources.get(sample.source, 0) + 1
    return {
        "sample_count": len(samples),
        "languages": dict(sorted(languages.items())),
        "sources": dict(sorted(sources.items())),
    }


def build_profile(
    samples: list[SpeechSample],
    *,
    source_mode: str,
    private_input_read: bool,
) -> dict[str, Any]:
    grouped: dict[str, list[SpeechSample]] = {"en": [], "de": []}
    for sample in samples:
        grouped.setdefault(sample.language, []).append(sample)

    language_profiles = {
        language: analyze_language_samples(language, language_samples)
        for language, language_samples in sorted(grouped.items())
        if language_samples
    }
    safe_public_artifact = not private_input_read
    return {
        "voice_milestone": "VOICE-029",
        "profile_id": PROFILE_ID,
        "source_mode": source_mode,
        "summary": {
            **summarize_samples(samples),
            "safe_public_artifact": safe_public_artifact,
        },
        "privacy_boundary": {
            "private_input_read": private_input_read,
            "raw_audio_read": False,
            "provider_calls_made": False,
            "voice_cloning_used": False,
            "raw_transcript_exported": False,
            "raw_examples_included": False,
            "human_review_required_before_runtime_use": True,
            "safe_for_public_generated_artifacts": safe_public_artifact,
        },
        "pattern_profile": {
            "description": "Abstract aggregate speech-style signals only; no raw examples or private identifiers.",
            "languages": language_profiles,
        },
        "runtime_profile_proposal": build_runtime_profile_proposal(language_profiles),
    }


def samples_from_case(case: dict[str, Any]) -> list[SpeechSample]:
    samples = []
    for index, item in enumerate(case.get("synthetic_samples", [])):
        text = str(item.get("text", ""))
        language = normalize_language(item.get("language"), text)
        samples.append(
            SpeechSample(
                sample_id=str(item.get("sample_id", f"sample-{index}")),
                language=language,
                text=text,
                source=str(item.get("source", "synthetic_fixture")),
            )
        )
    return samples


def samples_from_directory(input_dir: Path) -> list[SpeechSample]:
    samples: list[SpeechSample] = []
    files = sorted(
        path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".txt", ".md"}
    )
    for index, path in enumerate(files):
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            continue
        samples.append(
            SpeechSample(
                sample_id=f"private-redacted-{index + 1}",
                language=normalize_language(None, text),
                text=text,
                source="private_redacted_transcript",
            )
        )
    return samples


def profile_without_samples(payload: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(payload)
