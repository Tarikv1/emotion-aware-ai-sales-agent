#!/usr/bin/env python3
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.core.realtime_turns import build_runtime_decision, load_realtime_cases


DEFAULT_CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"


def find_campaign(campaigns: list[dict], campaign_id: str) -> dict:
    for campaign in campaigns:
        if campaign.get("campaign_id") == campaign_id:
            return campaign
    known = ", ".join(campaign.get("campaign_id", "<missing>") for campaign in campaigns)
    raise SystemExit(f"Unknown campaign_id {campaign_id!r}. Known campaigns: {known}")


def build_turn_case(
    campaign_id: str,
    stage: str,
    transcript: str,
    input_type: str,
    silence_count: int,
) -> dict:
    customer_input = {
        "input_type": input_type,
        "stage": stage,
        "transcript": transcript,
    }
    if input_type == "silence-timeout":
        customer_input["silence_count"] = silence_count
    return {
        "case_id": "REALTIME-CLI-TURN",
        "case_title": "Realtime CLI turn",
        "campaign_id": campaign_id,
        "runtime_scenario": "single-turn-cli",
        "customer_input": customer_input,
    }


def run_turn_decision(case: dict, campaign: dict | None = None) -> dict:
    start = time.perf_counter()
    decision = build_runtime_decision(case, campaign=campaign)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    decision["first_response_latency_ms"] = elapsed_ms
    decision["first_response_latency_observed_bucket"] = "under-1s" if elapsed_ms <= 1000 else (
        "under-2s" if elapsed_ms <= 2000 else "over-2s"
    )
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one realtime sales-agent turn from a transcript.")
    parser.add_argument("--campaign", required=True, help="Campaign ID to use.")
    parser.add_argument("--stage", required=True, help="Current call stage.")
    parser.add_argument("--transcript", default="", help="Customer transcript for this turn.")
    parser.add_argument(
        "--input-type",
        default="speech-final",
        choices=["speech-final", "voicemail-detected", "silence-timeout"],
        help="Runtime input type.",
    )
    parser.add_argument("--silence-count", type=int, default=0, help="Silence retry count for silence-timeout input.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper case file to load.")
    args = parser.parse_args()

    campaigns, _cases = load_realtime_cases(Path(args.cases))
    campaign = find_campaign(campaigns, args.campaign)
    case = build_turn_case(args.campaign, args.stage, args.transcript, args.input_type, args.silence_count)
    decision = run_turn_decision(case, campaign)
    output = {
        "campaign_id": campaign["campaign_id"],
        "campaign": {
            "product_name": campaign.get("product_name"),
            "product_category": campaign.get("product_category"),
            "customer_type": campaign.get("customer_type"),
            "language": campaign.get("language"),
        },
        "stage": args.stage,
        "input_type": args.input_type,
        "transcript": args.transcript,
        "decision": decision,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
