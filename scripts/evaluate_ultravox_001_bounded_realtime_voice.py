#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]

OFFICIAL_HOST_SUFFIXES = {
    "docs.ultravox.ai",
    "ultravox.ai",
    "www.ultravox.ai",
    "github.com",
    "huggingface.co",
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


def enrich_sources(payload: dict) -> list[dict]:
    return [
        {
            **source,
            "official_primary": is_official_url(source["url"]),
        }
        for source in payload["sources"]
    ]


def enrich_candidates(payload: dict, sources: list[dict]) -> list[dict]:
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
            for source_id in candidate["source_ids"]
        ]
        candidates.append(
            {
                **candidate,
                "weighted_score": score,
                "score_breakdown": breakdown,
                "source_links": source_links,
            }
        )
    return sorted(candidates, key=lambda item: (-item["weighted_score"], item["candidate_id"]))


def first_role(candidates: list[dict], role: str) -> dict:
    for candidate in candidates:
        if candidate["recommended_role"] == role:
            return candidate
    raise SystemExit(f"No candidate found for role: {role}")


def summarize_candidate(candidate: dict) -> dict:
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_name": candidate["candidate_name"],
        "candidate_class": candidate["candidate_class"],
        "recommended_role": candidate["recommended_role"],
        "weighted_score": candidate["weighted_score"],
        "api_key_required": candidate["api_key_required"],
        "network_call_required_for_live": candidate["network_call_required_for_live"],
        "customer_audio_upload_if_live": candidate["customer_audio_upload_if_live"],
        "provider_owned_business_logic": candidate["provider_owned_business_logic"],
        "durable_provider_agent_required": candidate["durable_provider_agent_required"],
        "blocked_until": candidate["blocked_until"],
    }


def build_recommendations(candidates: list[dict]) -> dict:
    return {
        "first_bounded_evaluation": summarize_candidate(first_role(candidates, "recommended-first-bounded-evaluation")),
        "self_host_research_lane": summarize_candidate(first_role(candidates, "self-host-research-lane")),
        "do_not_productize_first": summarize_candidate(first_role(candidates, "do-not-productize-first")),
        "baseline_control": summarize_candidate(first_role(candidates, "baseline-control")),
    }


def summarize(payload: dict, sources: list[dict], candidates: list[dict]) -> dict:
    gate = payload["research_gate"]
    return {
        "candidate_count": len(candidates),
        "source_count": len(sources),
        "official_source_count": sum(1 for source in sources if source["official_primary"]),
        "case_count": len(payload["evaluation_cases"]),
        "api_calls_made": False,
        "audio_uploaded": False,
        "secrets_required": False,
        "integration_allowed": gate["integration_allowed"],
        "live_provider_calls_allowed": gate["live_provider_calls_allowed"],
        "customer_audio_upload_allowed": gate["customer_audio_upload_allowed"],
        "voice_cloning_allowed": gate["voice_cloning_allowed"],
        "provider_owned_business_logic_allowed": gate["provider_owned_business_logic_allowed"],
        "durable_provider_agent_allowed": gate["durable_provider_agent_allowed"],
        "opens_prod_102": gate["opens_prod_102"],
        "recommended_first_bounded_evaluation": first_role(candidates, "recommended-first-bounded-evaluation")["candidate_id"],
        "self_host_lane": first_role(candidates, "self-host-research-lane")["candidate_id"],
        "baseline_control": first_role(candidates, "baseline-control")["candidate_id"],
    }


def build_result(payload: dict) -> dict:
    sources = enrich_sources(payload)
    candidates = enrich_candidates(payload, sources)
    return {
        "evaluation_milestone": payload["evaluation_milestone"],
        "evaluation_scope": payload["evaluation_scope"],
        "retrieved_on": payload["retrieved_on"],
        "score_scale": payload["score_scale"],
        "research_gate": payload["research_gate"],
        "scoring_weights": payload["scoring_weights"],
        "summary": summarize(payload, sources, candidates),
        "recommendations": build_recommendations(candidates),
        "evaluation_cases": payload["evaluation_cases"],
        "sources": sources,
        "ranked_candidates": candidates,
        "decision": {
            "status": "bounded-evaluation-prepared",
            "recommended_next_action": "Run one hosted UltraVox API synthetic live test only after explicit live-provider approval and env-only key setup.",
            "do_not_do": [
                "Do not open PROD-102 from this evaluation.",
                "Do not create a durable UltraVox console agent as the product runtime.",
                "Do not upload customer audio.",
                "Do not clone voices.",
                "Do not move sales policy, protected text, or campaign logic out of this repository."
            ],
        },
    }


def render_report(result: dict) -> str:
    gate = result["research_gate"]
    summary = result["summary"]
    rec = result["recommendations"]
    lines = [
        "# ULTRAVOX-001 Bounded Realtime Voice Evaluation Report",
        "",
        "This report was generated by `scripts/evaluate_ultravox_001_bounded_realtime_voice.py`.",
        "",
        "No UltraVox API calls were made.",
        "",
        "No audio was uploaded.",
        "",
        "No API keys or voice identifiers are required for this dry-run evaluation.",
        "",
        "This does not open `PROD-102` and does not change runtime behavior.",
        "",
        "## Gate",
        "",
        f"- Sources retrieved on: `{result['retrieved_on']}`",
        f"- Integration allowed now: `{str(gate['integration_allowed']).lower()}`",
        f"- Live provider calls allowed now: `{str(gate['live_provider_calls_allowed']).lower()}`",
        f"- Synthetic inputs only: `{str(gate['synthetic_inputs_only']).lower()}`",
        f"- Customer audio upload allowed: `{str(gate['customer_audio_upload_allowed']).lower()}`",
        f"- Voice cloning allowed: `{str(gate['voice_cloning_allowed']).lower()}`",
        f"- Provider-owned business logic allowed: `{str(gate['provider_owned_business_logic_allowed']).lower()}`",
        f"- Durable provider agent allowed: `{str(gate['durable_provider_agent_allowed']).lower()}`",
        f"- Opens PROD-102: `{str(gate['opens_prod_102']).lower()}`",
        f"- API key storage rule: `{gate['api_key_storage_rule']}`",
        "",
        "## Recommendation",
        "",
        f"First bounded evaluation: `{rec['first_bounded_evaluation']['candidate_id']}`.",
        "",
        "Reason: this is the smallest experiment that can test UltraVox realtime latency and session behavior while keeping this repository as the source of truth for policy, protected responses, campaign logic, and evidence.",
        "",
        f"Self-host research lane: `{rec['self_host_research_lane']['candidate_id']}`.",
        "",
        f"Do not productize first: `{rec['do_not_productize_first']['candidate_id']}`.",
        "",
        f"Baseline control: `{rec['baseline_control']['candidate_id']}`.",
        "",
        "## Fixed Evaluation Cases",
        "",
    ]
    for case in result["evaluation_cases"]:
        lines.extend(
            [
                f"### {case['case_id']}",
                "",
                f"- Question: {case['question']}",
                f"- Required result: {case['required_result']}",
                "",
            ]
        )

    lines.extend(["## Ranked Candidates", ""])
    for index, candidate in enumerate(result["ranked_candidates"], start=1):
        blockers = ", ".join(candidate["blocked_until"]) if candidate["blocked_until"] else "none"
        notes = " ".join(candidate["decision_notes"])
        lines.extend(
            [
                f"### {index}. {candidate['candidate_id']}",
                "",
                f"- Candidate: {candidate['candidate_name']}",
                f"- Class: `{candidate['candidate_class']}`",
                f"- Recommended role: `{candidate['recommended_role']}`",
                f"- Weighted score: `{candidate['weighted_score']}`",
                f"- API key required for live: `{str(candidate['api_key_required']).lower()}`",
                f"- Network call required for live: `{str(candidate['network_call_required_for_live']).lower()}`",
                f"- Customer audio upload if live: `{str(candidate['customer_audio_upload_if_live']).lower()}`",
                f"- Provider-owned business logic: `{str(candidate['provider_owned_business_logic']).lower()}`",
                f"- Durable provider agent required: `{str(candidate['durable_provider_agent_required']).lower()}`",
                f"- Live allowed now: `{str(candidate['live_allowed_now']).lower()}`",
                f"- Blocked until: {blockers}",
                f"- Notes: {notes}",
                "",
            ]
        )
        if candidate["source_links"]:
            lines.append("Sources:")
            for source in candidate["source_links"]:
                lines.append(f"- [{source['title']}]({source['url']}) retrieved on {source['retrieved_on']}")
            lines.append("")

    lines.extend(
        [
            "## Source Index",
            "",
            f"- Source count: `{summary['source_count']}`",
            f"- Official/primary source count: `{summary['official_source_count']}`",
            "",
        ]
    )
    for source in result["sources"]:
        official = "official/primary" if source["official_primary"] else "needs review"
        lines.append(f"- `{source['source_id']}`: [{source['title']}]({source['url']}) retrieved on {source['retrieved_on']} ({official})")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate UltraVox as a bounded realtime voice candidate without provider calls.")
    parser.add_argument("--cases", required=True, help="Path to the ULTRAVOX-001 evaluation JSON.")
    parser.add_argument("--out", required=True, help="Path to write JSON result.")
    parser.add_argument("--report-out", required=True, help="Path to write Markdown report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = load_json(resolve_project_path(args.cases))
    result = build_result(payload)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    write_json(out_path, result)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(result), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
