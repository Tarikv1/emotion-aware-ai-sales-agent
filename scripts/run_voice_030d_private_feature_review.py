#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DATA_ROOT = ROOT / "data" / "private"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-030d-private-feature-review.json"
DEFAULT_PRIVATE_ROOT = PRIVATE_DATA_ROOT / "tarik-speech-samples"
FEATURES_RELATIVE = Path("derived") / "audio-features"
SUMMARY_RELATIVE = Path("derived") / "review" / "voice-030d-feature-review-summary.json"
REPORT_RELATIVE = Path("derived") / "review" / "voice-030d-feature-review-summary.md"
RUNTIME_CANDIDATE_FEATURES = ["speech_burst_count", "energy_variation", "mean_speech_rms"]
DIAGNOSTIC_ONLY_FEATURES = ["pause_ratio", "average_pause_ms", "longest_pause_ms", "silence_seconds"]
CONTEXT_ONLY_FEATURES = ["duration_seconds"]


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def project_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_project_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def ensure_private_root(private_root: Path, *, allow_private_read: bool) -> None:
    if not is_under(private_root, PRIVATE_DATA_ROOT):
        raise SystemExit("VOICE-030D private root must stay under data/private.")
    if not allow_private_read:
        raise SystemExit("Refusing to read private feature files without --allow-private-read.")


def load_feature_payloads(features_dir: Path) -> list[dict[str, Any]]:
    if not features_dir.is_dir():
        return []
    payloads = []
    for path in sorted(features_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("voice_milestone") != "VOICE-030C":
            continue
        payloads.append(payload)
    return payloads


def numeric_values(payloads: list[dict[str, Any]], key: str, *, source: str) -> list[float]:
    values = []
    for payload in payloads:
        container = payload.get(source, {})
        if key not in container:
            continue
        value = container[key]
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def candidate_numeric_values(payloads: list[dict[str, Any]], key: str) -> tuple[list[float], dict[str, int]]:
    values = []
    source_counts = {
        "from_runtime_learning_candidates": 0,
        "from_features_fallback": 0,
        "missing": 0,
    }
    for payload in payloads:
        runtime_candidates = payload.get("runtime_learning_candidates", {})
        runtime_value = runtime_candidates.get(key) if isinstance(runtime_candidates, dict) else None
        if isinstance(runtime_value, (int, float)):
            values.append(float(runtime_value))
            source_counts["from_runtime_learning_candidates"] += 1
            continue

        features = payload.get("features", {})
        feature_value = features.get(key) if isinstance(features, dict) else None
        if isinstance(feature_value, (int, float)):
            values.append(float(feature_value))
            source_counts["from_features_fallback"] += 1
            continue

        source_counts["missing"] += 1
    return values, source_counts


def speech_bursts_per_minute(payloads: list[dict[str, Any]]) -> list[float]:
    values = []
    for payload in payloads:
        features = payload.get("features", {})
        if not isinstance(features, dict):
            continue
        duration = features.get("duration_seconds")
        bursts = features.get("speech_burst_count")
        if not isinstance(duration, (int, float)) or not isinstance(bursts, (int, float)):
            continue
        if duration <= 0:
            continue
        values.append(float(bursts) / float(duration) * 60.0)
    return values


def quartile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 3)
    index = (len(ordered) - 1) * fraction
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 3)


def summarize_numeric(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "max": None, "avg": None, "median": None, "p25": None, "p75": None}
    return {
        "count": len(values),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "avg": round(mean(values), 3),
        "median": round(median(values), 3),
        "p25": quartile(values, 0.25),
        "p75": quartile(values, 0.75),
    }


def language_counts(payloads: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for payload in payloads:
        language = str(payload.get("language", "unknown"))
        counts[language] = counts.get(language, 0) + 1
    return dict(sorted(counts.items()))


def is_usable_for_pattern_summary(payload: dict[str, Any]) -> bool:
    features = payload.get("features", {})
    if not isinstance(features, dict):
        return False
    duration = features.get("duration_seconds")
    speech_seconds = features.get("speech_seconds")
    speech_burst_count = features.get("speech_burst_count")
    mean_speech_rms = features.get("mean_speech_rms")
    return (
        isinstance(duration, (int, float))
        and duration > 0
        and isinstance(speech_seconds, (int, float))
        and speech_seconds > 0
        and isinstance(speech_burst_count, (int, float))
        and speech_burst_count > 0
        and isinstance(mean_speech_rms, (int, float))
        and mean_speech_rms > 0
    )


def sample_quality_summary(payloads: list[dict[str, Any]], usable_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "feature_files_read": len(payloads),
        "usable_for_recurring_pattern_summary": len(usable_payloads),
        "excluded_from_recurring_pattern_summary": len(payloads) - len(usable_payloads),
        "exclusion_reason": (
            "Feature files with no measurable speech are counted for coverage but excluded from "
            "recurring delivery patterns so silence does not become a runtime target."
        ),
    }


def build_candidate_summaries(
    payloads: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, float | int | None]], dict[str, dict[str, int | str]]]:
    runtime_summary = {}
    extraction_summary = {}
    for key in RUNTIME_CANDIDATE_FEATURES:
        values, source_counts = candidate_numeric_values(payloads, key)
        runtime_summary[key] = summarize_numeric(values)
        extraction_summary[key] = {
            "source_priority": "runtime_learning_candidates_then_features",
            "total_values": len(values),
            **source_counts,
        }
    return runtime_summary, extraction_summary


def build_recurring_pattern_summary(
    payloads: list[dict[str, Any]],
    runtime_summary: dict[str, dict[str, float | int | None]],
) -> dict[str, dict[str, float | int | None]]:
    return {
        "speech_bursts_per_minute": summarize_numeric(speech_bursts_per_minute(payloads)),
        "energy_variation": runtime_summary["energy_variation"],
        "mean_speech_rms": runtime_summary["mean_speech_rms"],
    }


def avg_value(summary: dict[str, float | int | None]) -> float | None:
    value = summary.get("avg")
    if isinstance(value, (int, float)):
        return float(value)
    return None


def describe_burst_density(summary: dict[str, float | int | None]) -> str:
    value = avg_value(summary)
    if value is None:
        return "No stable speech-burst rhythm could be measured yet."
    if value >= 70:
        return "Recurring rhythm pattern: frequent short speech groups rather than long uninterrupted monologues."
    if value >= 35:
        return "Recurring rhythm pattern: moderate speech grouping with room for short listener-friendly breaks."
    return "Recurring rhythm pattern: longer speech groups; review before using this for a sales-agent rhythm target."


def describe_energy_variation(summary: dict[str, float | int | None]) -> str:
    value = avg_value(summary)
    if value is None:
        return "No stable energy-variation pattern could be measured yet."
    if value >= 0.30:
        return "Recurring expressiveness pattern: noticeably varied energy, useful as a candidate for less-flat delivery."
    if value >= 0.18:
        return "Recurring expressiveness pattern: moderate energy variation, useful as a bounded naturalness hint."
    return "Recurring expressiveness pattern: low energy variation; do not use this to make the agent flatter."


def describe_presence(summary: dict[str, float | int | None]) -> str:
    value = avg_value(summary)
    if value is None:
        return "No stable vocal-presence pattern could be measured yet."
    if value >= 0.23:
        return "Recurring presence pattern: stronger spoken presence, but provider loudness should still be controlled separately."
    if value >= 0.14:
        return "Recurring presence pattern: moderate spoken presence, usable only as a review hint."
    return "Recurring presence pattern: lower spoken presence; do not directly copy it into campaign delivery."


def build_plain_language_patterns(
    payloads: list[dict[str, Any]],
    runtime_summary: dict[str, dict[str, float | int | None]],
    recurring_summary: dict[str, dict[str, float | int | None]],
) -> list[str]:
    sample_count = len(payloads)
    if sample_count == 0:
        return ["No VOICE-030C feature files were available for recurring-pattern review."]
    return [
        (
            f"Coverage pattern: recurring-pattern extraction used {sample_count} feature files. "
            "Values missing the old runtime wrapper were derived from the same acoustic fields under `features`."
        ),
        describe_burst_density(recurring_summary["speech_bursts_per_minute"]),
        describe_energy_variation(runtime_summary["energy_variation"]),
        describe_presence(runtime_summary["mean_speech_rms"]),
        (
            "Pause pattern: pause length, pause ratio, and silence time remain diagnostic only. "
            "They can explain the private samples, but they must not slow down the sales agent automatically."
        ),
    ]


def build_review_payload(payloads: list[dict[str, Any]], *, private_root: Path) -> dict[str, Any]:
    usable_payloads = [payload for payload in payloads if is_usable_for_pattern_summary(payload)]
    runtime_summary, extraction_summary = build_candidate_summaries(usable_payloads)
    recurring_summary = build_recurring_pattern_summary(usable_payloads, runtime_summary)
    duration_summary = summarize_numeric(numeric_values(payloads, "duration_seconds", source="features"))
    return {
        "voice_milestone": "VOICE-030D",
        "created_at_utc": utc_now(),
        "summary": {
            "sample_count": len(payloads),
            "language_counts": language_counts(payloads),
            "duration_seconds": duration_summary,
            "duration_is_context_only": True,
        },
        "sample_quality_summary": sample_quality_summary(payloads, usable_payloads),
        "runtime_candidate_summary": runtime_summary,
        "candidate_extraction_summary": extraction_summary,
        "recurring_pattern_summary": recurring_summary,
        "plain_language_patterns": build_plain_language_patterns(usable_payloads, runtime_summary, recurring_summary),
        "diagnostic_only_summary": {
            "excluded_from_runtime_learning": DIAGNOSTIC_ONLY_FEATURES,
            "reason": "Owner samples can include long formulation pauses during complex instruction-giving; pause ratio and pause duration must not slow down the sales agent.",
        },
        "context_only_summary": {
            "features": CONTEXT_ONLY_FEATURES,
            "reason": "Duration helps interpret sample coverage but is not a behavior target.",
        },
        "review_decision": {
            "status": "needs_human_review",
            "runtime_settings_changed": False,
            "safe_next_step": "Review private aggregate patterns before mapping any candidate into runtime voice settings.",
        },
        "privacy_boundary": {
            "private_input_read": True,
            "outputs_stay_under_data_private": True,
            "stored_under_private_root": is_under(private_root, PRIVATE_DATA_ROOT),
            "provider_calls_made": False,
            "transcription_created": False,
            "voice_cloning_used": False,
            "runtime_profile_applied": False,
            "public_artifact_created": False,
            "raw_audio_paths_exported": False,
            "human_review_required_before_runtime_use": True,
        },
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# VOICE-030D Private Feature Review Summary",
        "",
        "This private report summarizes VOICE-030C derived acoustic feature files. It does not include raw audio paths, transcripts, provider calls, voice cloning, or runtime setting changes.",
        "",
        "## Summary",
        "",
        f"- Sample count: `{payload['summary']['sample_count']}`",
        f"- Language counts: `{payload['summary']['language_counts']}`",
        f"- Duration seconds: `{payload['summary']['duration_seconds']}`",
        f"- Duration is context only: `{payload['summary']['duration_is_context_only']}`",
        "",
        "## Sample Quality",
        "",
        f"- `{payload['sample_quality_summary']}`",
        "",
        "## Runtime Candidate Summary",
        "",
    ]
    for key, value in payload["runtime_candidate_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Candidate Extraction Coverage",
            "",
        ]
    )
    for key, value in payload["candidate_extraction_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Recurring Pattern Summary",
            "",
        ]
    )
    for key, value in payload["recurring_pattern_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Plain-Language Patterns",
            "",
        ]
    )
    for pattern in payload["plain_language_patterns"]:
        lines.append(f"- {pattern}")
    lines.extend(
        [
            "",
            "## Diagnostic-Only Features",
            "",
            f"- Excluded from runtime learning: `{payload['diagnostic_only_summary']['excluded_from_runtime_learning']}`",
            f"- Reason: {payload['diagnostic_only_summary']['reason']}",
            "",
            "## Review Decision",
            "",
            f"- Status: `{payload['review_decision']['status']}`",
            f"- Runtime settings changed: `{payload['review_decision']['runtime_settings_changed']}`",
            f"- Safe next step: {payload['review_decision']['safe_next_step']}",
            "",
            "## Boundary",
            "",
            "- Outputs stay under `data/private/`.",
            "- No raw audio path, transcript, provider request, voice clone, or runtime setting is exported.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a private VOICE-030D review summary from VOICE-030C feature files.")
    parser.add_argument("--case", default=str(CASE_PATH), help="VOICE-030D case/config JSON.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Private speech-sample workspace root.")
    parser.add_argument("--allow-private-read", action="store_true", help="Required for reading private feature files.")
    parser.add_argument("--print-json", action="store_true", help="Print the review payload after writing private outputs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    case_path = resolve_project_path(args.case, CASE_PATH)
    if not case_path.is_file():
        raise SystemExit(f"VOICE-030D case file is missing: {case_path}")
    private_root = resolve_project_path(args.private_root, DEFAULT_PRIVATE_ROOT)
    ensure_private_root(private_root, allow_private_read=args.allow_private_read)
    features_dir = private_root / FEATURES_RELATIVE
    summary_path = private_root / SUMMARY_RELATIVE
    report_path = private_root / REPORT_RELATIVE
    payloads = load_feature_payloads(features_dir)
    review_payload = build_review_payload(payloads, private_root=private_root)
    write_json(summary_path, review_payload)
    write_text(report_path, render_report(review_payload))
    if args.print_json:
        print(json.dumps(review_payload, indent=2, ensure_ascii=False))
    else:
        print(f"Wrote VOICE-030D private review JSON to {project_relative(summary_path)}")
        print(f"Wrote VOICE-030D private review report to {project_relative(report_path)}")


if __name__ == "__main__":
    main()
