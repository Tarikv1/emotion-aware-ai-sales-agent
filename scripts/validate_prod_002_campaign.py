#!/usr/bin/env python3
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-002-b2c-insurance.json"


def main() -> None:
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    assert isinstance(payload, dict), "PROD-002 should use a campaign wrapper object"
    assert payload["campaign"]["campaign_id"] == "campaign-prod-002-b2c-insurance"
    assert payload["campaign"]["customer_type"] == "b2c"
    assert payload["campaign"]["product_category"] == "insurance"
    assert payload["campaign"]["country_or_region"] == "DE"
    assert payload["campaign"]["language"] == "de"
    assert "dental insurance" in payload["campaign"]["product_name"].lower()
    assert len(payload["campaign"]["qualification_questions"]) >= 3
    assert len(payload["cases"]) >= 6


if __name__ == "__main__":
    main()
