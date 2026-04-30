#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-004-sales-difficulty-gauntlet.json"

REQUIRED_DIFFICULTIES = {
    "price-objection",
    "send-info-brushoff",
    "status-quo",
    "timing-delay",
    "authority-gap",
    "trust-credibility",
    "competitor-comparison",
    "fit-risk",
    "vague-interest",
    "angry-or-annoyed",
    "human-request",
    "claim-boundary",
}


def main() -> None:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    assert isinstance(payload, dict), "PROD-004 should use a multi-campaign wrapper object"
    assert isinstance(payload["campaigns"], list), "PROD-004 should define campaigns"
    assert isinstance(payload["cases"], list), "PROD-004 should define cases"
    assert len(payload["campaigns"]) >= 5, "PROD-004 should span several campaign contexts"
    assert len(payload["cases"]) >= 12, "PROD-004 should be a real difficulty gauntlet"

    campaign_ids = {campaign["campaign_id"] for campaign in payload["campaigns"]}
    case_campaign_ids = {case["campaign_id"] for case in payload["cases"]}
    assert case_campaign_ids <= campaign_ids, "Every case must reference a declared campaign"

    customer_types = {campaign["customer_type"] for campaign in payload["campaigns"]}
    assert {"b2b", "b2c"} <= customer_types, "PROD-004 should cover B2B and B2C"

    difficulties = {case["difficulty_type"] for case in payload["cases"]}
    missing = REQUIRED_DIFFICULTIES - difficulties
    assert not missing, f"Missing required difficulty types: {sorted(missing)}"


if __name__ == "__main__":
    main()
