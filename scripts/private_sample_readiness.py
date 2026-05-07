#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_DATA_ROOT = ROOT / "data" / "private"
DEFAULT_PRIVATE_ROOT = PRIVATE_DATA_ROOT / "tarik-speech-samples"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "voice-033-private-sample-readiness.json"
README_NAME = "README.txt"

RAW_AUDIO_RELATIVE = Path("raw-audio")
CONVERTED_AUDIO_RELATIVE = Path("converted-audio")
WHATSAPP_RELATIVE = Path("whatsapp-voice-notes")
FEATURES_RELATIVE = Path("derived") / "audio-features"
QUEUE_RELATIVE = Path("derived") / "local-speech-learning-queue.jsonl"
CONVERSION_MANIFEST_RELATIVE = Path("derived") / "local-audio-conversion-manifest.jsonl"
READINESS_DIR_RELATIVE = Path("derived") / "readiness"
RESULT_RELATIVE = READINESS_DIR_RELATIVE / "voice-033-private-sample-readiness.json"
REPORT_RELATIVE = READINESS_DIR_RELATIVE / "voice-033-private-sample-readiness.md"

AUDIO_EXTENSIONS = {".wav", ".ogg", ".webm", ".mp3", ".m4a", ".aac", ".opus", ".flac", ".wma", ".caf", ".amr"}
CONVERSION_NEEDED_EXTENSIONS = AUDIO_EXTENSIONS - {".wav", ".ogg"}
DEFAULT_THRESHOLDS = {
    "first_review_min_analyzed_samples": 10,
    "stronger_pattern_review_min_analyzed_samples": 100,
    "best_case_target_samples": 150,
}


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


def ensure_private_root(private_root: Path, *, allow_private_metadata_read: bool) -> None:
    if not is_under(private_root, PRIVATE_DATA_ROOT):
        raise ValueError("VOICE-033 private root must stay under data/private/.")
    if not allow_private_metadata_read:
        raise ValueError("Refusing to scan private metadata without --allow-private-metadata-read.")


def load_case_thresholds(case_path: Path = CASE_PATH) -> dict[str, int]:
    if not case_path.is_file():
        return DEFAULT_THRESHOLDS.copy()
    payload = json.loads(case_path.read_text(encoding="utf-8"))
    thresholds = DEFAULT_THRESHOLDS.copy()
    thresholds.update(payload.get("thresholds", {}))
    return thresholds


def iter_audio_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.name != README_NAME and path.suffix.lower() in AUDIO_EXTENSIONS
    )


def count_extensions(paths: list[Path]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in paths:
        extension = path.suffix.lower()
        counts[extension] = counts.get(extension, 0) + 1
    return dict(sorted(counts.items()))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            records.append({"_malformed": True})
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def count_by_key(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(key, "unknown") or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def count_status(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    return count_by_key(records, key)


def build_readiness_status(analyzed_count: int, thresholds: dict[str, int]) -> str:
    if analyzed_count >= thresholds["stronger_pattern_review_min_analyzed_samples"]:
        return "enough_for_stronger_pattern_review"
    if analyzed_count >= thresholds["first_review_min_analyzed_samples"]:
        return "enough_for_first_review"
    return "not_enough_samples_yet"


def build_next_action(status: str) -> dict[str, str]:
    if status == "not_enough_samples_yet":
        return {
            "recommended_action": "collect_more_wav_samples",
            "reason": "There are not enough analyzed WAV feature files for a useful VOICE-030D review yet.",
        }
    if status == "enough_for_first_review":
        return {
            "recommended_action": "run_voice_030d_private_feature_review",
            "reason": "There are enough analyzed samples for a first private aggregate review.",
        }
    return {
        "recommended_action": "run_voice_030d_private_feature_review",
        "reason": "There are enough analyzed samples for a stronger private pattern review.",
    }


def build_recommendations(
    *,
    status: str,
    analyzed_count: int,
    thresholds: dict[str, int],
    whatsapp_ogg_waiting: int,
    other_non_wav: int,
    analysis_failed: int,
    conversion_failed: int,
    wav_unanalyzed_estimate: int,
) -> list[str]:
    recommendations: list[str] = []
    first_target = thresholds["first_review_min_analyzed_samples"]
    stronger_target = thresholds["stronger_pattern_review_min_analyzed_samples"]
    if status == "not_enough_samples_yet":
        recommendations.append(
            f"Keep collecting local WAV samples; {analyzed_count}/{first_target} analyzed samples are ready for a first VOICE-030D review."
        )
    elif status == "enough_for_first_review":
        recommendations.append(
            f"A first VOICE-030D review is available now; keep collecting toward {stronger_target} samples for stronger pattern evidence."
        )
    else:
        recommendations.append(
            "Run VOICE-030D when Tarik wants the next private aggregate review; sample volume is strong enough for pattern evidence."
        )

    if whatsapp_ogg_waiting:
        if shutil.which("ffmpeg"):
            recommendations.append("Run VOICE-032 to convert waiting WhatsApp .ogg files into WAV before the next review.")
        else:
            recommendations.append("Expose or install local ffmpeg so VOICE-032 can convert waiting WhatsApp .ogg files.")
    if other_non_wav:
        recommendations.append("Keep non-OGG legacy formats deferred until the conversion scope is intentionally widened.")
    if analysis_failed:
        recommendations.append("Review WAV samples marked analysis_failed_needs_review before treating the sample set as clean.")
    if conversion_failed:
        recommendations.append("Review conversion_failed_needs_review records before importing more WhatsApp voice notes.")
    if wav_unanalyzed_estimate:
        recommendations.append("Some WAV files may not have derived feature JSON yet; re-run or inspect the VOICE-030C queue.")
    return recommendations


def privacy_boundary() -> dict[str, Any]:
    return {
        "private_metadata_read": True,
        "raw_audio_content_read": False,
        "provider_calls_made": False,
        "transcription_created": False,
        "voice_cloning_used": False,
        "runtime_profile_applied": False,
        "public_artifact_created": False,
        "outputs_stay_under_data_private": True,
        "aggregate_counts_only": True,
        "human_review_required_before_runtime_use": True,
    }


def build_readiness_payload(
    private_root: Path,
    *,
    thresholds: dict[str, int] | None = None,
) -> dict[str, Any]:
    thresholds = thresholds or load_case_thresholds()
    raw_files = iter_audio_files(private_root / RAW_AUDIO_RELATIVE)
    converted_files = iter_audio_files(private_root / CONVERTED_AUDIO_RELATIVE)
    whatsapp_files = iter_audio_files(private_root / WHATSAPP_RELATIVE)
    feature_files = sorted((private_root / FEATURES_RELATIVE).glob("*.json")) if (private_root / FEATURES_RELATIVE).is_dir() else []
    queue_records = read_jsonl(private_root / QUEUE_RELATIVE)
    conversion_records = read_jsonl(private_root / CONVERSION_MANIFEST_RELATIVE)

    all_audio_files = raw_files + converted_files + whatsapp_files
    extension_counts = count_extensions(all_audio_files)
    wav_files_available = extension_counts.get(".wav", 0)
    analyzed_feature_files = len(feature_files)
    wav_unanalyzed_estimate = max(wav_files_available - analyzed_feature_files, 0)
    whatsapp_ogg_waiting = len([path for path in whatsapp_files if path.suffix.lower() == ".ogg"])
    other_non_wav = len([path for path in raw_files + converted_files + whatsapp_files if path.suffix.lower() in CONVERSION_NEEDED_EXTENSIONS])

    queue_status_counts = count_status(queue_records, "processing_status")
    conversion_status_counts = count_status(conversion_records, "conversion_status")
    analysis_failed = queue_status_counts.get("analysis_failed_needs_review", 0)
    conversion_failed = conversion_status_counts.get("conversion_failed_needs_review", 0)
    conversion_failed += conversion_status_counts.get("conversion_timeout_needs_review", 0)

    status = build_readiness_status(analyzed_feature_files, thresholds)
    return {
        "voice_milestone": "VOICE-033",
        "created_at_utc": utc_now(),
        "private_root_relative": project_relative(private_root),
        "readiness_status": status,
        "thresholds": thresholds,
        "sample_inventory": {
            "audio_files_detected": len(all_audio_files),
            "wav_files_available": wav_files_available,
            "analyzed_feature_files": analyzed_feature_files,
            "wav_unanalyzed_estimate": wav_unanalyzed_estimate,
            "whatsapp_ogg_waiting_conversion": whatsapp_ogg_waiting,
            "other_non_wav_needing_conversion": other_non_wav,
            "queue_records": len(queue_records),
            "conversion_records": len(conversion_records),
            "analysis_failed_needs_review": analysis_failed,
            "conversion_failed_needs_review": conversion_failed,
        },
        "extension_counts": extension_counts,
        "queue_status_counts": queue_status_counts,
        "conversion_status_counts": conversion_status_counts,
        "language_counts": count_by_key(queue_records, "language"),
        "source_counts": count_by_key(queue_records, "source_kind"),
        "next_action": build_next_action(status),
        "recommendations": build_recommendations(
            status=status,
            analyzed_count=analyzed_feature_files,
            thresholds=thresholds,
            whatsapp_ogg_waiting=whatsapp_ogg_waiting,
            other_non_wav=other_non_wav,
            analysis_failed=analysis_failed,
            conversion_failed=conversion_failed,
            wav_unanalyzed_estimate=wav_unanalyzed_estimate,
        ),
        "privacy_boundary": privacy_boundary(),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def render_readiness_report(payload: dict[str, Any]) -> str:
    inventory = payload["sample_inventory"]
    lines = [
        "# VOICE-033 Private Speech Sample Readiness",
        "",
        "VOICE-033 reports aggregate private sample readiness without reading raw audio content.",
        "",
        "## Status",
        "",
        f"- Readiness status: `{payload['readiness_status']}`",
        f"- Recommended action: `{payload['next_action']['recommended_action']}`",
        f"- Reason: {payload['next_action']['reason']}",
        "",
        "## Inventory",
        "",
        f"- Audio files detected: `{inventory['audio_files_detected']}`",
        f"- WAV files available: `{inventory['wav_files_available']}`",
        f"- Analyzed feature files: `{inventory['analyzed_feature_files']}`",
        f"- WAV unanalyzed estimate: `{inventory['wav_unanalyzed_estimate']}`",
        f"- WhatsApp OGG waiting conversion: `{inventory['whatsapp_ogg_waiting_conversion']}`",
        f"- Other non-WAV needing conversion: `{inventory['other_non_wav_needing_conversion']}`",
        f"- Analysis failed needs review: `{inventory['analysis_failed_needs_review']}`",
        f"- Conversion failed needs review: `{inventory['conversion_failed_needs_review']}`",
        "",
        "## Counts",
        "",
        f"- Extension counts: `{payload['extension_counts']}`",
        f"- Queue status counts: `{payload['queue_status_counts']}`",
        f"- Conversion status counts: `{payload['conversion_status_counts']}`",
        f"- Language counts: `{payload['language_counts']}`",
        f"- Source counts: `{payload['source_counts']}`",
        "",
        "## Recommendations",
        "",
    ]
    for recommendation in payload["recommendations"]:
        lines.append(f"- {recommendation}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Reads private metadata and directory entries only.",
            "- Does not read raw audio content.",
            "- Does not transcribe, upload, clone, call providers, or change runtime settings.",
            "- Writes private readiness outputs under `data/private/`.",
        ]
    )
    return "\n".join(lines) + "\n"
