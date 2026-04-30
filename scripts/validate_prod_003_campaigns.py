#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-003-mixed-campaigns.json"


def main() -> None:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    assert isinstance(payload, dict), "PROD-003 should use a campaign wrapper object"
    assert isinstance(payload["campaigns"], list), "PROD-003 should define multiple campaigns"
    assert isinstance(payload["cases"], list), "PROD-003 should define cases"
    assert len(payload["campaigns"]) >= 4, "PROD-003 should cover multiple product categories"
    assert len(payload["cases"]) >= 8, "PROD-003 should include a mixed case set"

    campaign_ids = {campaign["campaign_id"] for campaign in payload["campaigns"]}
    case_campaign_ids = {case["campaign_id"] for case in payload["cases"]}
    assert case_campaign_ids <= campaign_ids, "Every case must reference a declared campaign"

    customer_types = {campaign["customer_type"] for campaign in payload["campaigns"]}
    assert "b2c" in customer_types, "PROD-003 should include B2C campaigns"
    assert "b2b" in customer_types, "PROD-003 should include at least one B2B campaign"


if __name__ == "__main__":
    main()
