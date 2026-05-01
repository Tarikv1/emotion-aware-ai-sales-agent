#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def resolve_project_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def weighted_score(candidate: dict, weights: dict) -> tuple[float, dict]:
    total = 0.0
    breakdown = {}
    for field, weight in weights.items():
        value = candidate[field]
        weighted = round(value * weight, 3)
        breakdown[field] = {
            "value": value,
            "weight": weight,
            "weighted_score": weighted,
        }
        total += weighted
    return round(total, 3), breakdown


def enriched_candidates(payload: dict) -> list[dict]:
    weights = payload["scoring_weights"]
    candidates = []
    for candidate in payload["candidates"]:
        score, breakdown = weighted_score(candidate, weights)
        candidates.append(
            {
                **candidate,
                "weighted_score": score,
                "score_breakdown": breakdown,
            }
        )
    return sorted(candidates, key=lambda item: (-item["weighted_score"], item["provider_id"]))


def first_candidate(candidates: list[dict], *, role: str, action: str) -> dict:
    for candidate in candidates:
        if candidate["role"] == role and candidate["recommended_next_action"] == action:
            return candidate
    raise SystemExit(f"No {role} candidate matched action {action}.")


def summarize_candidate(candidate: dict) -> dict:
    return {
        "provider_id": candidate["provider_id"],
        "provider_family": candidate["provider_family"],
        "role": candidate["role"],
        "provider_class": candidate["provider_class"],
        "requires_api_key": candidate["requires_api_key"],
        "uploads_customer_audio": candidate["uploads_customer_audio"],
        "language_support": candidate["language_support"],
        "weighted_score": candidate["weighted_score"],
        "recommended_next_action": candidate["recommended_next_action"],
        "fallback_path": candidate["fallback_path"],
        "blockers": candidate["blockers"],
    }


def build_recommendations(candidates: list[dict]) -> dict:
    return {
        "regression_baselines": {
            "asr": summarize_candidate(
                first_candidate(candidates, role="asr", action="keep-regression-baseline")
            ),
            "tts": summarize_candidate(
                first_candidate(candidates, role="tts", action="keep-regression-baseline")
            ),
        },
        "next_no_key_prototypes": {
            "asr": summarize_candidate(
                first_candidate(candidates, role="asr", action="next-no-key-prototype")
            ),
            "tts": summarize_candidate(
                first_candidate(candidates, role="tts", action="next-no-key-prototype")
            ),
        },
        "production_followups": {
            "asr": summarize_candidate(
                first_candidate(candidates, role="asr", action="production-followup-after-gates")
            ),
            "tts": summarize_candidate(
                first_candidate(candidates, role="tts", action="production-followup-after-gates")
            ),
        },
    }


def summarize(candidates: list[dict]) -> dict:
    role_counts = {}
    languages = set()
    for candidate in candidates:
        role_counts[candidate["role"]] = role_counts.get(candidate["role"], 0) + 1
        languages.update(candidate["language_support"])
    return {
        "candidate_count": len(candidates),
        "role_counts": role_counts,
        "languages_evaluated": sorted(languages),
        "api_calls_made": False,
        "audio_uploaded": False,
        "secrets_required": False,
        "cloud_candidates_blocked_until_review": sum(
            1
            for candidate in candidates
            if candidate["requires_api_key"] and candidate["launch_allowed"] is False
        ),
        "customer_audio_upload_candidates_gated": sum(
            1
            for candidate in candidates
            if candidate["uploads_customer_audio"]
            and candidate["customer_audio_upload_gate"] == "blocked-until-privacy-review"
        ),
    }


def build_result(payload: dict) -> dict:
    candidates = enriched_candidates(payload)
    return {
        "voice_milestone": payload["voice_milestone"],
        "comparison_scope": payload["comparison_scope"],
        "score_scale": payload["score_scale"],
        "readiness_gate": payload["readiness_gate"],
        "scoring_weights": payload["scoring_weights"],
        "summary": summarize(candidates),
        "recommendations": build_recommendations(candidates),
        "ranked_candidates": candidates,
    }


def render_report(result: dict) -> str:
    recommendations = result["recommendations"]
    gate = result["readiness_gate"]
    lines = [
        "# VOICE-007 Provider Readiness Report",
        "",
        "This report was generated by `scripts/evaluate_voice_provider_readiness.py`.",
        "",
        "No API calls were made.",
        "",
        "No audio was uploaded.",
        "",
        "VOICE-007 is a readiness gate, not a provider integration.",
        "",
        "## Gate Rules",
        "",
        f"- First response target: `{gate['first_response_target_ms']} ms`",
        f"- TTS start target: `{gate['tts_start_target_ms']} ms`",
        f"- API key storage rule: `{gate['api_key_storage_rule']}`",
        f"- Customer audio upload rule: {gate['customer_audio_upload_rule']}",
        "- Runtime languages: German and English",
        f"- Fallback requirement: {gate['fallback_requirement']}",
        "",
        "## Recommendations",
        "",
        f"- ASR regression baseline: `{recommendations['regression_baselines']['asr']['provider_id']}`",
        f"- TTS regression baseline: `{recommendations['regression_baselines']['tts']['provider_id']}`",
        f"- Next no-key ASR prototype: `{recommendations['next_no_key_prototypes']['asr']['provider_id']}`",
        f"- Next no-key TTS prototype: `{recommendations['next_no_key_prototypes']['tts']['provider_id']}`",
        f"- Production ASR follow-up after gates: `{recommendations['production_followups']['asr']['provider_id']}`",
        f"- Production TTS follow-up after gates: `{recommendations['production_followups']['tts']['provider_id']}`",
        "",
        "Cloud provider paths remain blocked until key management, privacy review, retention review, and provider terms are documented.",
        "",
        "## Ranked Candidates",
        "",
    ]
    for index, candidate in enumerate(result["ranked_candidates"], start=1):
        notes = " ".join(candidate["decision_notes"])
        blockers = ", ".join(candidate["blockers"]) if candidate["blockers"] else "none"
        lines.extend(
            [
                f"### {index}. {candidate['provider_id']}",
                "",
                f"- Role: `{candidate['role']}`",
                f"- Family: {candidate['provider_family']}",
                f"- Requires API key: `{str(candidate['requires_api_key']).lower()}`",
                f"- Uploads customer audio: `{str(candidate['uploads_customer_audio']).lower()}`",
                f"- Language support: `{', '.join(candidate['language_support'])}`",
                f"- Launch allowed before review: `{str(candidate['launch_allowed']).lower()}`",
                f"- Recommended next action: `{candidate['recommended_next_action']}`",
                f"- Weighted score: `{candidate['weighted_score']}`",
                f"- Fallback path: {candidate['fallback_path']}",
                f"- Blockers: {blockers}",
                f"- Notes: {notes}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate VOICE-007 ASR/TTS provider readiness without API calls.")
    parser.add_argument("--candidates", required=True, help="Path to VOICE-007 provider readiness candidates JSON.")
    parser.add_argument("--out", required=True, help="Path to write JSON readiness result.")
    parser.add_argument("--report-out", required=True, help="Path to write Markdown readiness report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_json(resolve_project_path(args.candidates))
    result = build_result(payload)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    write_json(out_path, result)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
