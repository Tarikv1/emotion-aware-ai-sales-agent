#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "runtime" / "sales_knowledge" / "universal_sales_rag"
INDEX = BASE / "category_index.json"
COMPILED = BASE / "compiled" / "universal_sales_core.md"
PROVIDER_KB = ROOT / "runtime" / "providers" / "elevenlabs_agents" / "knowledge_base" / "universal_sales_core.md"


HEADER = """# Universal Sales Core Knowledge Base

Package: `RAG-023-universal-sales-category-files`

Compiled from category files by `scripts/compile_universal_sales_rag.py`.

This knowledge base gives the agent a compact, reusable sales operating model.
It is not a script and it is not a replacement for campaign-specific facts.
It teaches how to use selling points; the campaign profile and campaign overlay
supply what is actually true for a specific campaign.

## Operating Boundary

This knowledge base is advisory, not a script.

Campaign facts override universal sales advice.

Use the campaign's approved offer, claims, pricing rules, qualification fields,
handoff rules, compliance limits, language, and close. If campaign information
conflicts with this universal guidance, follow the campaign.

## Three-Layer Sales Knowledge Contract

Layer 1: Universal Sales RAG

This layer teaches reusable sales method: buyer moves, buyer journey jobs,
buyer enablement, stakeholder mapping, discovery design, qualification evidence,
value framing, objection handling, trust repair, proof handling, conversation
repair, next-step policy, decision process, negotiation, disqualification,
ethical persuasion, motion playbooks, vertical playbooks, post-sale handoff,
success/failure patterns, and call quality rubrics.

Layer 2: Campaign Sales Overlay

This layer adapts the universal method to one campaign. It says which discovery
questions, value frames, objection patterns, proof types, next steps, and call
quality rules fit the campaign. Campaign overlay overrides universal sales
guidance for that campaign.

Campaign overlay overrides universal sales guidance.

Layer 3: Campaign Profile And Facts

This layer owns the exact offer, approved product facts, prices, proof,
exclusions, forbidden claims, target buyer, handoff path, and compliance
boundaries. Campaign Profile facts override campaign overlay.

Universal sales guidance never creates campaign facts. If a fact is not in the
campaign profile or approved campaign material, do not invent it. If the layers
conflict, follow campaign profile facts first, campaign overlay second, and
universal sales guidance last.

Do not invent urgency, scarcity, guarantees, discounts, legal claims, or results.
Do not pressure a buyer after a clear refusal. Do not continue after a
do-not-call request, repeated silence, abuse, privacy objection, or human-transfer
request.

## Universal Sales Category Files
"""


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_compiled_text(index: dict[str, Any]) -> str:
    sections: list[str] = [HEADER.rstrip(), ""]
    categories = index.get("categories")
    if not isinstance(categories, list):
        raise ValueError("category_index.json must contain a categories list")

    sections.append("Category order:")
    sections.append("")
    for item in categories:
        sections.append(f"- {item['id']}: {item['title']}")
    sections.append("")

    for item in categories:
        path = ROOT / item["path"]
        text = path.read_text(encoding="utf-8").strip()
        sections.append(f"### {item['id']}")
        sections.append("")
        sections.append(text)
        sections.append("")

    return "\n".join(sections).rstrip() + "\n"


def update_index_hash(index: dict[str, Any], compiled_text: str) -> None:
    index["compiled_output"] = str(COMPILED.relative_to(ROOT)).replace("\\", "/")
    index["provider_output"] = str(PROVIDER_KB.relative_to(ROOT)).replace("\\", "/")
    index["compiled_sha256"] = sha256_text(compiled_text)
    INDEX.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile universal sales RAG category files.")
    parser.add_argument("--check", action="store_true", help="Verify compiled outputs without writing.")
    args = parser.parse_args()

    index = read_json(INDEX)
    compiled_text = build_compiled_text(index)

    if args.check:
        expected_hash = sha256_text(compiled_text)
        failures: list[str] = []
        if not COMPILED.is_file() or COMPILED.read_text(encoding="utf-8") != compiled_text:
            failures.append("compiled output is stale")
        if not PROVIDER_KB.is_file() or PROVIDER_KB.read_text(encoding="utf-8") != compiled_text:
            failures.append("provider KB output is stale")
        if index.get("compiled_sha256") != expected_hash:
            failures.append("category index compiled_sha256 is stale")
        if failures:
            raise SystemExit("; ".join(failures))
        print(json.dumps({"status": "pass", "compiled_sha256": expected_hash}, indent=2))
        return 0

    COMPILED.parent.mkdir(parents=True, exist_ok=True)
    COMPILED.write_text(compiled_text, encoding="utf-8")
    PROVIDER_KB.write_text(compiled_text, encoding="utf-8")
    update_index_hash(index, compiled_text)
    print(
        json.dumps(
            {
                "status": "compiled",
                "compiled_output": str(COMPILED.relative_to(ROOT)),
                "provider_output": str(PROVIDER_KB.relative_to(ROOT)),
                "compiled_sha256": sha256_text(compiled_text),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
