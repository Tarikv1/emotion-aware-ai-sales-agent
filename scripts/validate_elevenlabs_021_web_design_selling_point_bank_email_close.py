#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
KB_ROOT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base"
PROMPT = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "prompts" / "web_design_atlas_sales_prompt.md"
OVERLAY = KB_ROOT / "atlas_web_studio_web_design_campaign_overlay.md"
PROFILE = KB_ROOT / "atlas_web_studio_web_design_campaign_profile.md"
MANIFEST = (
    ROOT
    / "runtime"
    / "providers"
    / "elevenlabs_agents"
    / "manifests"
    / "web_design_sales_spine_compression.package.json"
)
FULL_CORE_UPLOAD_PATH = "runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md"


REQUIRED_SELLING_MECHANISMS = (
    "New-discovery capture",
    "Social-to-booking bridge",
    "DM workload reduction",
    "Pre-qualification",
    "Trust stack",
    "After-hours action",
    "Owned channel",
    "Local search foundations",
)

BUYER_EXAMPLES = (
    "Instagram is good for people who already see your content.",
    "For a salon, that means services, starting prices if you want them shown, policies, reviews, FAQs, and the booking button in one flow.",
    "If someone is already comparing auto shops, the site can show services, diagnostics, hours, location, reviews, and the phone path before they call.",
    "Google Maps helps people find you. The website helps them decide: menu, hours, photos, location, reservation or order path, and what makes your place worth choosing.",
    "For plumbing, the site helps when someone is already stressed and searching.",
)

LOCAL_SEARCH_ALLOWED = (
    "basic local search foundations",
    "structured so Google can better understand your services and area",
    "service pages and location information",
    "search-friendly structure",
    "helps people who are already searching understand what you offer",
)

SEO_FORBIDDEN = (
    "this will rank you higher",
    "this will get you more customers",
    "this will bring more traffic",
    "this guarantees SEO results",
)

EMAIL_CLOSE_MARKERS = (
    "normalize obvious email spell-outs",
    "confirm the exact destination",
    "confirm delivery timing",
    "confirm they can reply there with questions",
    "Do not ask another discovery question after the buyer gives the email",
    "I'll send it to mike@northsideauto.com after this call, and you can reply there with questions.",
    "I'm sending it to mike@northsideauto.com now, and you can reply there with questions.",
)


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def read_text(path: Path) -> str:
    assert_condition(path.is_file(), f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(read_text(path))
    assert_condition(isinstance(payload, dict), f"{path.relative_to(ROOT)} must contain a JSON object")
    return payload


def assert_contains(label: str, text: str, markers: tuple[str, ...]) -> None:
    for marker in markers:
        assert_condition(marker in text, f"{label} missing marker: {marker}")


def assert_no_unbounded_claims(label: str, text: str) -> None:
    risky_patterns = (
        re.compile(r"\bwill (bring|get|create|generate) (you )?(more )?(customers|calls|bookings|patients|jobs|leads|rankings|traffic|revenue)\b"),
        re.compile(r"\bwill rank (you|your business|the business) higher\b"),
        re.compile(r"\bguarantee[sd]? (seo|traffic|rankings|customers|calls|bookings|revenue|roi)\b"),
        re.compile(r"\boptimi[sz]e (it|the site|the website) to attract more customers\b"),
    )
    safe_context = (
        "no ",
        "not ",
        "do not",
        "never",
        "can't",
        "cannot",
        "forbidden",
        "boundary",
        "without promising",
        "if asked",
        "unless explicitly softened",
    )
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lower()
        if any(pattern.search(line) for pattern in risky_patterns):
            assert_condition(
                any(marker in line for marker in safe_context),
                f"{label} line {line_number} contains an unbounded claim: {raw_line}",
            )


def assert_selling_point_bank(profile_text: str, overlay_text: str, prompt_text: str) -> None:
    combined = "\n".join((profile_text, overlay_text, prompt_text))
    assert_contains("selling point bank", combined, ("## Campaign-Safe Selling Point Bank",))
    assert_contains("selling mechanisms", combined, REQUIRED_SELLING_MECHANISMS)
    assert_contains("buyer-facing examples", combined, BUYER_EXAMPLES)
    assert_contains("local search allowed wording", combined, LOCAL_SEARCH_ALLOWED)
    assert_contains(
        "SEO pricing",
        combined,
        (
            "Basic local search setup can be part of how the site is structured. Ongoing SEO work would be a separate conversation if you wanted that later.",
        ),
    )
    for forbidden in SEO_FORBIDDEN:
        assert_condition(forbidden.lower() in combined.lower(), f"Missing forbidden SEO wording: {forbidden}")
    assert_no_unbounded_claims("selling point bank", combined)


def assert_email_close(prompt_text: str, overlay_text: str, profile_text: str) -> None:
    combined = "\n".join((prompt_text, overlay_text, profile_text))
    assert_contains("terminal email close rule", combined, EMAIL_CLOSE_MARKERS)
    assert_condition("mike at northsideauto dot com" in combined, "Email close examples must include spell-out normalization input")
    assert_condition("mike@northsideauto.com" in combined, "Email close examples must confirm normalized destination")
    assert_condition("reply there with questions" in combined, "Email close examples must confirm reply path")
    assert_condition("after this call" in combined, "Email close examples must cover non-immediate delivery timing")
    assert_condition("now, and you can reply there" in combined, "Email close examples must cover immediate delivery timing")


def assert_manifest(manifest: dict[str, Any]) -> None:
    active_docs = manifest.get("active_kb_recommendation", {}).get("recommended_upload_docs")
    assert_condition(isinstance(active_docs, list), "Manifest missing active recommended upload docs")
    assert_condition(FULL_CORE_UPLOAD_PATH not in active_docs, "Manifest must not recommend full universal_sales_core.md for active upload")


def main() -> None:
    prompt_text = read_text(PROMPT)
    overlay_text = read_text(OVERLAY)
    profile_text = read_text(PROFILE)
    manifest = read_json(MANIFEST)

    assert_selling_point_bank(profile_text, overlay_text, prompt_text)
    assert_email_close(prompt_text, overlay_text, profile_text)
    assert_manifest(manifest)

    diff_check = subprocess.run(["git", "diff", "--check"], cwd=ROOT, text=True, capture_output=True, check=False)
    assert_condition(diff_check.returncode == 0, diff_check.stderr or diff_check.stdout)

    print(
        json.dumps(
            {
                "status": "pass",
                "checkpoint_id": "ELEVENLABS-021-web-design-selling-point-bank-email-close",
                "selling_point_bank": True,
                "selling_mechanism_count": len(REQUIRED_SELLING_MECHANISMS),
                "email_close_repair": True,
                "full_universal_core_recommended_for_active_upload": False,
                "live_provider_calls_made": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
