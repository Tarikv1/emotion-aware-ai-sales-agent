#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]

OFFICIAL_HOST_SUFFIXES = {
    "docs.cartesia.ai",
    "cartesia.ai",
    "elevenlabs.io",
    "platform.openai.com",
    "developers.openai.com",
    "learn.microsoft.com",
    "azure.microsoft.com",
    "cloud.google.com",
    "docs.cloud.google.com",
    "docs.aws.amazon.com",
    "aws.amazon.com",
    "developers.deepgram.com",
    "deepgram.com",
    "github.com",
}


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


def is_official_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host in OFFICIAL_HOST_SUFFIXES or any(host.endswith(f".{suffix}") for suffix in OFFICIAL_HOST_SUFFIXES)


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


def enriched_sources(payload: dict) -> list[dict]:
    return [
        {
            **source,
            "official_primary": is_official_url(source["url"]),
        }
        for source in payload["sources"]
    ]


def enriched_candidates(payload: dict, sources: list[dict]) -> list[dict]:
    weights = payload["scoring_weights"]
    source_by_id = {source["source_id"]: source for source in sources}
    candidates = []
    for candidate in payload["candidates"]:
        score, breakdown = weighted_score(candidate, weights)
        source_links = [
            {
                "source_id": source_id,
                "title": source_by_id[source_id]["title"],
                "url": source_by_id[source_id]["url"],
                "retrieved_on": source_by_id[source_id]["retrieved_on"],
            }
            for source_id in candidate["official_sources"]
        ]
        candidates.append(
            {
                **candidate,
                "weighted_score": score,
                "score_breakdown": breakdown,
                "source_links": source_links,
            }
        )
    return sorted(candidates, key=lambda item: (-item["weighted_score"], item["provider_id"]))


def first_role(candidates: list[dict], role: str) -> dict:
    for candidate in candidates:
        if candidate["recommended_role"] == role:
            return candidate
    raise SystemExit(f"No candidate found for recommended role: {role}")


def summarize_candidate(candidate: dict) -> dict:
    return {
        "provider_id": candidate["provider_id"],
        "provider_name": candidate["provider_name"],
        "model_or_voice_family": candidate["model_or_voice_family"],
        "provider_class": candidate["provider_class"],
        "recommended_role": candidate["recommended_role"],
        "requires_api_key": candidate["requires_api_key"],
        "language_support": candidate["language_support"],
        "streaming_support": candidate["streaming_support"],
        "latency_ms_claim": candidate["latency_ms_claim"],
        "weighted_score": candidate["weighted_score"],
        "fallback_path": candidate["fallback_path"],
        "blockers": candidate["blockers"],
    }


def build_recommendations(candidates: list[dict]) -> dict:
    return {
        "recommended_first_integration": summarize_candidate(first_role(candidates, "recommended-first-integration")),
        "quality_alternate": summarize_candidate(first_role(candidates, "quality-alternate")),
        "stack_simplest_alternate": summarize_candidate(first_role(candidates, "stack-simplest-alternate")),
        "enterprise_alternate": summarize_candidate(first_role(candidates, "enterprise-alternate")),
        "enterprise_backup": summarize_candidate(first_role(candidates, "enterprise-backup")),
        "do_not_integrate_first": summarize_candidate(first_role(candidates, "do-not-integrate-first")),
        "offline_research_lane": summarize_candidate(first_role(candidates, "offline-research-lane")),
    }


def summarize(payload: dict, sources: list[dict], candidates: list[dict]) -> dict:
    languages = set()
    for candidate in candidates:
        languages.update(candidate["language_support"])
    return {
        "candidate_count": len(candidates),
        "source_count": len(sources),
        "official_source_count": sum(1 for source in sources if source["official_primary"]),
        "languages_evaluated": sorted(languages),
        "api_calls_made": False,
        "audio_uploaded": False,
        "secrets_required": False,
        "cloud_candidates_key_gated": sum(
            1
            for candidate in candidates
            if candidate["requires_api_key"] and candidate["key_gate"] == "required-before-integration"
        ),
        "voice_clone_candidates_blocked": sum(
            1
            for candidate in candidates
            if (candidate["voice_cloning_available"] or candidate["custom_voice_available"])
            and candidate["voice_clone_allowed_for_first_integration"] is False
        ),
        "recommended_first_integration": first_role(candidates, "recommended-first-integration")["provider_id"],
        "research_retrieved_on": payload["research_gate"]["retrieved_on"],
    }


def build_result(payload: dict) -> dict:
    sources = enriched_sources(payload)
    candidates = enriched_candidates(payload, sources)
    return {
        "voice_milestone": payload["voice_milestone"],
        "comparison_scope": payload["comparison_scope"],
        "score_scale": payload["score_scale"],
        "research_gate": payload["research_gate"],
        "scoring_weights": payload["scoring_weights"],
        "summary": summarize(payload, sources, candidates),
        "recommendations": build_recommendations(candidates),
        "sources": sources,
        "ranked_candidates": candidates,
    }


def render_recommendations(result: dict) -> list[str]:
    rec = result["recommendations"]
    return [
        "## Recommendation",
        "",
        "Recommended first integration: "
        f"`{rec['recommended_first_integration']['provider_id']}` "
        f"({rec['recommended_first_integration']['provider_name']} {rec['recommended_first_integration']['model_or_voice_family']}).",
        "",
        "Why: it is the best fit in this checkpoint for German and English voice-agent TTS because the official sources reviewed here combine streaming support, low-latency positioning, emotional/speed controls, and telephony-oriented audio options.",
        "",
        f"- Quality/latency alternate: `{rec['quality_alternate']['provider_id']}`",
        f"- Stack-simplest alternate: `{rec['stack_simplest_alternate']['provider_id']}`",
        f"- Enterprise alternate: `{rec['enterprise_alternate']['provider_id']}`",
        f"- Enterprise backup: `{rec['enterprise_backup']['provider_id']}`",
        f"- Do not integrate first: `{rec['do_not_integrate_first']['provider_id']}`",
        f"- Offline research lane: `{rec['offline_research_lane']['provider_id']}`",
        "",
    ]


def render_report(result: dict) -> str:
    gate = result["research_gate"]
    summary = result["summary"]
    lines = [
        "# VOICE-009 TTS Provider Research Report",
        "",
        "This report was generated by `scripts/evaluate_voice_009_tts_provider_research.py`.",
        "",
        "No API calls were made.",
        "",
        "No audio was uploaded.",
        "",
        "VOICE-009 is provider research only; it does not integrate any vendor SDK or store any API key.",
        "",
        "## Research Gate",
        "",
        f"- Sources retrieved on 2026-05-01: `{summary['source_count']}` official/primary sources",
        f"- Runtime languages: German and English (`{', '.join(gate['runtime_languages'])}`)",
        f"- First response target: `{gate['first_response_target_ms']} ms`",
        f"- TTS start target: `{gate['tts_start_target_ms']} ms`",
        f"- API key storage rule: `{gate['api_key_storage_rule']}`",
        f"- Integration allowed in this checkpoint: `{str(gate['integration_allowed']).lower()}`",
        f"- Voice clone rule: {gate['voice_clone_rule']}",
        "",
    ]
    lines.extend(render_recommendations(result))
    lines.extend(
        [
            "## Ranked Candidates",
            "",
        ]
    )
    for index, candidate in enumerate(result["ranked_candidates"], start=1):
        blockers = ", ".join(candidate["blockers"]) if candidate["blockers"] else "none"
        notes = " ".join(candidate["decision_notes"])
        latency = candidate["latency_ms_claim"] if candidate["latency_ms_claim"] is not None else "not claimed in this checkpoint"
        lines.extend(
            [
                f"### {index}. {candidate['provider_id']}",
                "",
                f"- Provider: {candidate['provider_name']} `{candidate['model_or_voice_family']}`",
                f"- Recommended role: `{candidate['recommended_role']}`",
                f"- Language support evaluated: `{', '.join(candidate['language_support'])}`",
                f"- German support state: `{candidate['german_support_state']}`",
                f"- English support state: `{candidate['english_support_state']}`",
                f"- Streaming support: `{candidate['streaming_support']}`",
                f"- Latency claim used: `{latency}`",
                f"- Requires API key: `{str(candidate['requires_api_key']).lower()}`",
                f"- Launch allowed before review: `{str(candidate['launch_allowed']).lower()}`",
                f"- Voice cloning/custom voice available: `{str(candidate['voice_cloning_available'] or candidate['custom_voice_available']).lower()}`",
                f"- Voice cloning allowed for first integration: `{str(candidate['voice_clone_allowed_for_first_integration']).lower()}`",
                f"- Weighted score: `{candidate['weighted_score']}`",
                f"- Fallback path: {candidate['fallback_path']}",
                f"- Blockers: {blockers}",
                f"- Notes: {notes}",
                "",
                "Sources:",
            ]
        )
        for source in candidate["source_links"]:
            lines.append(f"- [{source['title']}]({source['url']}) retrieved on {source['retrieved_on']}")
        lines.append("")

    lines.extend(
        [
            "## Source Index",
            "",
        ]
    )
    for source in result["sources"]:
        official = "official/primary" if source["official_primary"] else "needs review"
        lines.append(f"- `{source['source_id']}`: [{source['title']}]({source['url']}) retrieved on {source['retrieved_on']} ({official})")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate VOICE-009 TTS provider research without API calls.")
    parser.add_argument("--candidates", required=True, help="Path to VOICE-009 TTS provider research JSON.")
    parser.add_argument("--out", required=True, help="Path to write JSON research result.")
    parser.add_argument("--report-out", required=True, help="Path to write Markdown research report.")
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
