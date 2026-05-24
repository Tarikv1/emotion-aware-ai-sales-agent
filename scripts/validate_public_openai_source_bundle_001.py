#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PUBLIC-OPENAI-SOURCE-BUNDLE-001"
SOURCE_DIR = ROOT / "research" / "sources" / "public_openai_chatgpt_plans"
MANIFEST_PATH = SOURCE_DIR / "source_manifest.json"
NOTES_PATH = SOURCE_DIR / "source_notes.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

ALLOWED_DOMAINS = {"openai.com", "chatgpt.com", "help.openai.com", "platform.openai.com"}
REQUIRED_CLAIM_FIELDS = {
    "fact_id",
    "claim",
    "source_title",
    "source_url",
    "retrieved_at_utc",
    "source_type",
    "allowed_in_speech",
    "requires_caveat",
    "caveat_text",
    "plan_ids",
    "claim_category",
    "exact_quote_excerpt_optional",
    "normalized_speech_version",
}
REQUIRED_CATEGORIES = {
    "product_intro",
    "plan_catalog",
    "pricing",
    "feature",
    "api_usage_boundary",
    "privacy_training",
    "sign_up",
    "enterprise_sales",
    "usage_limits",
    "security_admin",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{path.relative_to(ROOT)} must be a JSON object")
    return payload


def domain_allowed(url: str) -> bool:
    parsed = urlparse(str(url or ""))
    host = parsed.netloc.lower()
    if not host:
        return False
    return any(host == domain or host.endswith("." + domain) for domain in ALLOWED_DOMAINS)


def assert_condition(failures: list[str], condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def write_evidence(result: dict[str, Any], report: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    failures: list[str] = []
    assert_condition(failures, MANIFEST_PATH.is_file(), "source_manifest.json is missing")
    assert_condition(failures, NOTES_PATH.is_file(), "source_notes.md is missing")
    manifest = load_json(MANIFEST_PATH) if MANIFEST_PATH.is_file() else {}

    sources = manifest.get("sources") or []
    claims = manifest.get("claims") or []
    assert_condition(failures, isinstance(sources, list) and bool(sources), "sources must be a populated list")
    assert_condition(failures, isinstance(claims, list) and bool(claims), "claims must be a populated list")

    source_urls: set[str] = set()
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            failures.append(f"sources[{index}] must be an object")
            continue
        for field in ("source_id", "source_title", "source_url", "source_type", "retrieved_at_utc"):
            assert_condition(failures, bool(str(source.get(field) or "").strip()), f"sources[{index}].{field} missing")
        url = str(source.get("source_url") or "")
        source_urls.add(url)
        assert_condition(failures, domain_allowed(url), f"sources[{index}] has non-OpenAI domain: {url}")

    categories = Counter()
    plan_claims = Counter()
    fact_ids: set[str] = set()
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            failures.append(f"claims[{index}] must be an object")
            continue
        missing = sorted(REQUIRED_CLAIM_FIELDS - set(claim))
        assert_condition(failures, not missing, f"claims[{index}] missing fields: {missing}")
        fact_id = str(claim.get("fact_id") or "")
        assert_condition(failures, bool(fact_id), f"claims[{index}].fact_id missing")
        assert_condition(failures, fact_id not in fact_ids, f"duplicate fact_id: {fact_id}")
        fact_ids.add(fact_id)

        url = str(claim.get("source_url") or "")
        assert_condition(failures, domain_allowed(url), f"{fact_id}: source_url has non-OpenAI domain: {url}")
        assert_condition(failures, url in source_urls, f"{fact_id}: source_url is not listed in sources")
        assert_condition(failures, bool(str(claim.get("source_title") or "").strip()), f"{fact_id}: source_title missing")
        assert_condition(failures, bool(str(claim.get("retrieved_at_utc") or "").strip()), f"{fact_id}: retrieved_at_utc missing")
        assert_condition(failures, isinstance(claim.get("plan_ids"), list), f"{fact_id}: plan_ids must be a list")
        assert_condition(failures, isinstance(claim.get("allowed_in_speech"), bool), f"{fact_id}: allowed_in_speech must be bool")
        assert_condition(failures, isinstance(claim.get("requires_caveat"), bool), f"{fact_id}: requires_caveat must be bool")
        if claim.get("allowed_in_speech"):
            assert_condition(
                failures,
                bool(str(claim.get("normalized_speech_version") or "").strip()),
                f"{fact_id}: allowed speech claim needs normalized_speech_version",
            )
        if claim.get("requires_caveat"):
            assert_condition(failures, bool(str(claim.get("caveat_text") or "").strip()), f"{fact_id}: caveat missing")
        category = str(claim.get("claim_category") or "")
        categories[category] += 1
        for plan_id in claim.get("plan_ids") or []:
            plan_claims[str(plan_id)] += 1

    missing_categories = sorted(REQUIRED_CATEGORIES - set(categories))
    assert_condition(failures, not missing_categories, f"missing required source categories: {missing_categories}")
    assert_condition(
        failures,
        any("api" in str(claim.get("claim_category") or "") and "separate" in str(claim.get("claim") or "").lower() for claim in claims if isinstance(claim, dict)),
        "API separate claim is missing",
    )
    for plan_id in ("free", "go", "plus", "pro", "business_codex", "business_chatgpt_codex", "enterprise"):
        assert_condition(failures, plan_claims[plan_id] > 0, f"no source-backed claim covers plan_id={plan_id}")

    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)),
        "source_notes": str(NOTES_PATH.relative_to(ROOT)),
        "source_count": len(sources),
        "claim_count": len(claims),
        "allowed_speech_claim_count": sum(1 for claim in claims if isinstance(claim, dict) and claim.get("allowed_in_speech")),
        "categories": dict(sorted(categories.items())),
        "plan_claims": dict(sorted(plan_claims.items())),
        "allowed_domains": sorted(ALLOWED_DOMAINS),
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "failures": failures,
    }
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Sources: `{result['source_count']}`",
            f"- Source-grounded claims: `{result['claim_count']}`",
            f"- Allowed speech claims: `{result['allowed_speech_claim_count']}`",
            f"- Required categories covered: `{not missing_categories}`",
            f"- API separate claim present: `{not any('API separate claim is missing' in item for item in failures)}`",
            f"- Failures: `{len(failures)}`",
            "",
        ]
    )
    write_evidence(result, report)
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(1)
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID, "claim_count": len(claims)}, indent=2))


if __name__ == "__main__":
    main()
