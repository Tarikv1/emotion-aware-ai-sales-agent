#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from generate_voice_response import resolve_project_path
from run_browser_speech_demo import DEFAULT_CASES_PATH, build_browser_decision_packet


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-005"
DEFAULT_RESULTS_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-005-latency-results.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-005-latency-report.md"

LATENCY_CASES = [
    {
        "case_id": "VOICE-005-C01",
        "case_title": "German price objection fast path",
        "campaign_id": "campaign-prod-005-b2c-telecom",
        "expected_response_language": "de",
        "stage": "relevance-check",
        "transcript": "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
    },
    {
        "case_id": "VOICE-005-C02",
        "case_title": "German claim boundary escalation fast path",
        "campaign_id": "campaign-prod-005-b2c-telecom",
        "expected_response_language": "de",
        "stage": "relevance-check",
        "transcript": "Nur wenn Sie garantieren koennen, dass es stabil ist.",
    },
    {
        "case_id": "VOICE-005-C03",
        "case_title": "German product detail lookup bridge path",
        "campaign_id": "campaign-prod-005-b2c-telecom",
        "expected_response_language": "de",
        "stage": "product-detail-check",
        "transcript": "Welcher genaue Tarif ist das und wie viel Datenvolumen ist enthalten?",
    },
    {
        "case_id": "VOICE-005-C04",
        "case_title": "German unknown signal follow-up path",
        "campaign_id": "campaign-prod-005-b2c-telecom",
        "expected_response_language": "de",
        "stage": "relevance-check",
        "transcript": "Koennen Sie mir erklaeren, warum ich dieses Gespraech heute ueberhaupt fuehren sollte?",
    },
    {
        "case_id": "VOICE-005-C05",
        "case_title": "English price objection fast path",
        "campaign_id": "campaign-prod-005-b2b-software",
        "expected_response_language": "en",
        "stage": "relevance-check",
        "transcript": "That sounds too expensive and I am not sure the review is worth the effort.",
    },
    {
        "case_id": "VOICE-005-C06",
        "case_title": "English claim boundary escalation fast path",
        "campaign_id": "campaign-prod-005-b2b-software",
        "expected_response_language": "en",
        "stage": "relevance-check",
        "transcript": "Can you guarantee the performance will be better?",
    },
    {
        "case_id": "VOICE-005-C07",
        "case_title": "English product detail lookup bridge path",
        "campaign_id": "campaign-prod-005-b2b-software",
        "expected_response_language": "en",
        "stage": "product-detail-check",
        "transcript": "Which exact service details are included?",
    },
    {
        "case_id": "VOICE-005-C08",
        "case_title": "English unknown signal follow-up path",
        "campaign_id": "campaign-prod-005-b2b-software",
        "expected_response_language": "en",
        "stage": "relevance-check",
        "transcript": "Can you explain why I should even take this call today?",
    },
]


def project_relative_string(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_latency_case(case: dict, cases_path: Path) -> dict:
    packet = build_browser_decision_packet(
        transcript=case["transcript"],
        campaign_id=case["campaign_id"],
        stage=case["stage"],
        input_type="speech-final",
        silence_count=0,
        cases_path=cases_path,
    )
    latency = packet["latency_measurement"]
    decision = packet["response_packet"]["decision"]
    return {
        "case_id": case["case_id"],
        "case_title": case["case_title"],
        "campaign_id": case["campaign_id"],
        "expected_response_language": case["expected_response_language"],
        "response_language": decision["response_language"],
        "stage": case["stage"],
        "sales_difficulty": decision["sales_difficulty"],
        "response_mode": decision["response_mode"],
        "call_control": decision["call_control"],
        "total_decision_loop_ms": latency["total_decision_loop_ms"],
        "observed_bucket": latency["observed_bucket"],
        "budget_pass": latency["budget_pass"],
        "segments": latency["segments"],
        "packet": packet,
    }


def summarize(cases: list[dict]) -> dict:
    totals = [case["total_decision_loop_ms"] for case in cases]
    bucket_counts = {
        "under-1s": 0,
        "under-2s": 0,
        "over-2s": 0,
    }
    language_counts = {}
    for case in cases:
        bucket_counts[case["observed_bucket"]] += 1
        language_counts[case["response_language"]] = language_counts.get(case["response_language"], 0) + 1
    return {
        "case_count": len(cases),
        "language_counts": language_counts,
        "response_language_match_count": sum(
            1 for case in cases if case["response_language"] == case["expected_response_language"]
        ),
        "min_total_decision_loop_ms": min(totals) if totals else None,
        "max_total_decision_loop_ms": max(totals) if totals else None,
        "avg_total_decision_loop_ms": round(sum(totals) / len(totals), 2) if totals else None,
        "under_1s_count": bucket_counts["under-1s"],
        "under_2s_count": bucket_counts["under-2s"],
        "over_2s_count": bucket_counts["over-2s"],
        "budget_pass_count": sum(1 for case in cases if case["budget_pass"]),
    }


def render_report(payload: dict) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-005 Browser Latency Report",
        "",
        "This report was generated by `scripts/measure_voice_005_latency.py`.",
        "",
        "No server was started. The measurement uses the same VOICE-004 one-shot decision path used by the validator.",
        "",
        "Browser ASR and browser TTS playback are not measured in VOICE-005. This checkpoint measures local Python latency after a final transcript is available.",
        "",
        "## Summary",
        "",
        f"- Cases: {summary['case_count']}",
        f"- Language counts: `{json.dumps(summary['language_counts'], sort_keys=True)}`",
        f"- Response-language matches: `{summary['response_language_match_count']} / {summary['case_count']}`",
        f"- Minimum local decision-loop latency: `{summary['min_total_decision_loop_ms']} ms`",
        f"- Maximum local decision-loop latency: `{summary['max_total_decision_loop_ms']} ms`",
        f"- Average local decision-loop latency: `{summary['avg_total_decision_loop_ms']} ms`",
        f"- Under 1s: `{summary['under_1s_count']}`",
        f"- Under 2s: `{summary['under_2s_count']}`",
        f"- Over 2s: `{summary['over_2s_count']}`",
        f"- Budget pass count: `{summary['budget_pass_count']} / {summary['case_count']}`",
        "",
        "## Segment Meaning",
        "",
        "- `campaign_load_ms`: load the configured SalesCampaign from the local case file",
        "- `realtime_decision_ms`: classify the turn and choose strategy, next action, and call control",
        "- `guarded_response_ms`: run RESP-001 guarded response generation and validation",
        "- `voice_packet_build_ms`: build the VOICE-001-style response packet for browser playback",
        "",
        "## Case Results",
        "",
    ]
    for case in payload["cases"]:
        lines.extend(
            [
                f"### {case['case_id']}: {case['case_title']}",
                "",
                f"- Response language: `{case['response_language']}`",
                f"- Sales difficulty: `{case['sales_difficulty']}`",
                f"- Response mode: `{case['response_mode']}`",
                f"- Call control: `{case['call_control']}`",
                f"- Total local decision-loop latency: `{case['total_decision_loop_ms']} ms`",
                f"- Observed bucket: `{case['observed_bucket']}`",
                f"- Budget pass: `{case['budget_pass']}`",
                f"- RESP-001 segment: `{case['segments']['guarded_response_ms']} ms`",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure VOICE-005 local browser decision latency.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper case file to load.")
    parser.add_argument("--out", default=str(DEFAULT_RESULTS_OUT), help="Path to write JSON latency results.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Path to write Markdown latency report.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    cases = [run_latency_case(case, cases_path) for case in LATENCY_CASES]
    payload = {
        "voice_milestone": VOICE_MILESTONE,
        "measurement_scope": "local-python-after-final-transcript",
        "server_started": False,
        "requires_api_key": False,
        "case_file": project_relative_string(cases_path),
        "summary": summarize(cases),
        "cases": cases,
    }
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
