#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from statistics import mean
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


def summarize_numeric(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "min": None, "max": None, "avg": None}
    return {
        "count": len(values),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "avg": round(mean(values), 3),
    }


def language_counts(payloads: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for payload in payloads:
        language = str(payload.get("language", "unknown"))
        counts[language] = counts.get(language, 0) + 1
    return dict(sorted(counts.items()))


def build_review_payload(payloads: list[dict[str, Any]], *, private_root: Path) -> dict[str, Any]:
    runtime_summary = {
        key: summarize_numeric(numeric_values(payloads, key, source="runtime_learning_candidates"))
        for key in RUNTIME_CANDIDATE_FEATURES
    }
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
        "runtime_candidate_summary": runtime_summary,
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
        "## Runtime Candidate Summary",
        "",
    ]
    for key, value in payload["runtime_candidate_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
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
