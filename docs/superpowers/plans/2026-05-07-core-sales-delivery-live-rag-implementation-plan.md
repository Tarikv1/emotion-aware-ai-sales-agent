# Core Sales Delivery Live RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working slice of the `teach now + retrieve live + learn later` architecture: distilled core playbook/delivery packs, retrieval-before-composition, relevance/latency/campaign gates, and a 200-note learning checkpoint scaffold.

**Architecture:** Keep the always-on core small and project-local. Generate a reviewed core pack from static project-owned rules, retrieve from the existing RAG-017 registry before response composition when explicitly enabled, apply campaign-fact grounding before any RAG influence, and keep private-call learning as a batch threshold notification scaffold with no runtime promotion.

**Tech Stack:** Python standard library, existing RESP/RAG/VOICE scripts, JSON generated artifacts, Markdown docs, local validators. No external vector DB, embedding provider, provider call, LLM call, or private-data read.

---

## File Structure

- Create: `scripts/core_sales_delivery_playbook.py`
  - Owns the distilled always-on safety, sales, and delivery rules.
  - Exposes `build_core_sales_delivery_pack()`, `validate_core_sales_delivery_pack()`, and `render_core_sales_delivery_pack_report()`.
- Create: `scripts/run_core_sales_delivery_playbook.py`
  - Writes `research/experiments/generated/CORE-sales-delivery-playbook/result.json` and `report.md`.
- Create: `scripts/validate_core_sales_delivery_playbook.py`
  - Validates the core pack has the agreed persuasion, campaign-fact, and observable-empathy boundaries.
- Modify: `scripts/rag_guarded_retrieval_policy.py`
  - Adds deterministic relevance thresholding and allowed source/lane gates.
  - Returns match scores and rejected candidate reasons.
- Modify: `scripts/generate_guarded_response.py`
  - Loads the core pack.
  - Builds campaign fact grounding.
  - Runs retrieval before candidate composition.
  - Applies only threshold/source/campaign-compatible RAG hints.
  - Records retrieval latency and fallback decisions.
- Modify: `scripts/validate_resp_001_guarded_response_generation.py`
  - Extends validation for retrieve-before-compose, latency fields, threshold behavior, campaign fact priority, and protected blockers.
- Modify: `scripts/validate_rag_018_guarded_runtime_retrieval.py`
  - Adds focused RAG-018 checks for relevance/source gates and latency metadata.
- Modify: `scripts/runtime_voice_delivery.py`
  - Adds core delivery pack metadata to voice delivery output without changing `final_response`.
- Modify: `scripts/generate_runtime_voice_delivery.py`
  - Loads/passes the core delivery pack into runtime voice delivery.
- Modify: `scripts/validate_resp_002_runtime_voice_delivery.py`
  - Checks delivery pack metadata is attached, protected text remains unchanged, and no hidden-emotion certainty claims appear.
- Create: `scripts/call_pattern_learning_checkpoint.py`
  - Counts redacted local call-note metadata and emits a notification when 200 eligible notes exist.
- Create: `scripts/validate_call_pattern_learning_checkpoint.py`
  - Validates no private raw transcript/audio is read and no promotion happens at 200 notes.
- Create: `docs/product/CORE_SALES_DELIVERY_PLAYBOOK.md`
  - Documents the always-on core pack and command.
- Modify: `docs/product/RAG_018_GUARDED_RUNTIME_RETRIEVAL.md`
  - Documents retrieval-before-composition, relevance threshold, latency budget, campaign grounding, and fallback.
- Modify: `docs/product/RESP_002_RUNTIME_VOICE_DELIVERY.md`
  - Documents core delivery pack handoff.
- Modify: `docs/product/COMMANDS.md`
  - Adds commands for the new core pack and learning checkpoint validators.
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
  - Adds the implementation checkpoint after code changes are complete.

## Task 1: Core Sales And Delivery Pack

**Files:**
- Create: `scripts/validate_core_sales_delivery_playbook.py`
- Create: `scripts/core_sales_delivery_playbook.py`
- Create: `scripts/run_core_sales_delivery_playbook.py`
- Create: `docs/product/CORE_SALES_DELIVERY_PLAYBOOK.md`

- [ ] **Step 1: Write the failing validator**

Create `scripts/validate_core_sales_delivery_playbook.py`:

```python
#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "run_core_sales_delivery_playbook.py"
RESULT = ROOT / "research" / "experiments" / "generated" / "CORE-sales-delivery-playbook" / "result.json"
REPORT = ROOT / "research" / "experiments" / "generated" / "CORE-sales-delivery-playbook" / "report.md"
DOC = ROOT / "docs" / "product" / "CORE_SALES_DELIVERY_PLAYBOOK.md"


def assert_condition(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(completed.returncode == 0, completed.stderr)
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    report_text = REPORT.read_text(encoding="utf-8")
    doc_text = DOC.read_text(encoding="utf-8")

    assert_condition(payload["core_pack_id"] == "CORE-sales-delivery-playbook", payload)
    assert_condition(payload["runtime_default_enabled"] is True, payload)
    assert_condition(payload["external_provider_calls_made"] is False, payload)
    assert_condition(payload["private_customer_data_used"] is False, payload)
    assert_condition(payload["campaign_facts_override_rag"] is True, payload)
    assert_condition(payload["persuasion_boundary"]["ethical_persuasion_allowed"] is True, payload)
    assert_condition(payload["persuasion_boundary"]["fake_urgency_allowed"] is False, payload)
    assert_condition(payload["persuasion_boundary"]["invented_scarcity_allowed"] is False, payload)
    assert_condition(payload["emotion_boundary"]["observable_empathy_allowed"] is True, payload)
    assert_condition(payload["emotion_boundary"]["hidden_state_certainty_allowed"] is False, payload)
    assert_condition(len(payload["sales_playbook"]["common_objection_rules"]) >= 8, payload["sales_playbook"])
    assert_condition(len(payload["delivery_pack"]["speech_delivery_rules"]) >= 8, payload["delivery_pack"])
    assert_condition("source_excerpt" not in json.dumps(payload).lower(), "Core pack must not store source excerpts.")
    assert_condition("data/private" not in json.dumps(payload).replace("\\\\", "/").lower(), "Core pack must not reference private paths.")
    assert_condition("fake urgency" in report_text.lower(), "Report should document fake urgency boundary.")
    assert_condition("Campaign facts override RAG" in doc_text, "Product doc should state campaign facts override RAG.")
    print("Core sales delivery playbook validation passed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_core_sales_delivery_playbook.py
```

Expected: FAIL because `scripts/run_core_sales_delivery_playbook.py` does not exist.

- [ ] **Step 3: Implement the core pack module**

Create `scripts/core_sales_delivery_playbook.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any


CORE_PACK_ID = "CORE-sales-delivery-playbook"


def build_core_sales_delivery_pack() -> dict[str, Any]:
    return {
        "core_pack_id": CORE_PACK_ID,
        "runtime_default_enabled": True,
        "external_provider_calls_made": False,
        "private_customer_data_used": False,
        "campaign_facts_override_rag": True,
        "persuasion_boundary": {
            "ethical_persuasion_allowed": True,
            "strong_persuasion_allowed": True,
            "real_campaign_urgency_allowed": True,
            "real_scarcity_allowed": True,
            "fake_urgency_allowed": False,
            "invented_scarcity_allowed": False,
            "hidden_material_facts_allowed": False,
            "exploit_vulnerable_customer_allowed": False,
            "rule": "Use ethical persuasion. Strong persuasion is allowed when it is truthful, campaign-supported, reversible, and respectful.",
        },
        "emotion_boundary": {
            "observable_empathy_allowed": True,
            "hidden_state_certainty_allowed": False,
            "protected_trait_inference_allowed": False,
            "allowed_examples": [
                "I understand why that would be frustrating.",
                "That makes sense.",
                "I hear the hesitation.",
                "I get why you would want to be careful here.",
            ],
            "blocked_examples": [
                "You are angry.",
                "You are afraid.",
                "I know exactly how you feel.",
                "I can tell you feel anxious.",
            ],
        },
        "sales_playbook": {
            "opener_rules": [
                "Open with a short, concrete reason for the call.",
                "Use permission-based framing when interruption risk is high.",
                "Keep the first turn short enough for the customer to respond.",
                "Use a respectful pattern interrupt only when it reduces confusion.",
            ],
            "common_objection_rules": [
                {"objection": "not_interested", "rule": "Acknowledge, ask one low-friction relevance question, then respect refusal."},
                {"objection": "send_info", "rule": "Offer to send information, then ask what they want the information to answer."},
                {"objection": "price", "rule": "Diagnose whether the issue is price, terms, value, or effort before answering."},
                {"objection": "timing", "rule": "Ask about real timing without inventing urgency."},
                {"objection": "trust", "rule": "Use truthful proof or process clarity; do not overclaim."},
                {"objection": "competitor", "rule": "Respect the existing provider and compare only approved differentiators."},
                {"objection": "already_have_someone", "rule": "Ask whether they are open to a quick comparison without implying current choice is wrong."},
                {"objection": "think_about_it", "rule": "Clarify what they need to think through and offer a concrete next step."},
                {"objection": "partner_or_boss", "rule": "Ask what the stakeholder will care about and suggest a clean follow-up."},
            ],
            "closing_rules": [
                "Use trial closes to check fit before asking for commitment.",
                "Use next-step closes more often than hard closes.",
                "When campaign urgency is real, state the deadline and the reversible next step.",
                "Do not turn hesitation into pressure.",
            ],
        },
        "delivery_pack": {
            "speech_delivery_rules": [
                "Use calm confidence rather than hype.",
                "Prefer short clauses over dense explanations.",
                "Pause before a clarifying question.",
                "Use light natural fillers only in eligible freeform speech.",
                "Match energy without overacting.",
                "Use observable empathy before objection diagnosis.",
                "Avoid phrase shapes that invite wrong emphasis.",
                "Keep protected text exact.",
                "Use provider-facing delivery metadata instead of changing final_response where possible.",
            ],
            "voice_layer_contract": "Feeds RESP-002 and VOICE layers; final_response remains policy-owned.",
        },
    }


def validate_core_sales_delivery_pack(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    serialized = json.dumps(payload, ensure_ascii=False).lower().replace("\\\\", "/")
    if payload.get("core_pack_id") != CORE_PACK_ID:
        errors.append("core_pack_id mismatch")
    if payload.get("campaign_facts_override_rag") is not True:
        errors.append("campaign facts must override RAG")
    if payload.get("persuasion_boundary", {}).get("fake_urgency_allowed") is not False:
        errors.append("fake urgency must be blocked")
    if payload.get("persuasion_boundary", {}).get("invented_scarcity_allowed") is not False:
        errors.append("invented scarcity must be blocked")
    if payload.get("emotion_boundary", {}).get("hidden_state_certainty_allowed") is not False:
        errors.append("hidden emotional certainty must be blocked")
    if "source_excerpt" in serialized:
        errors.append("source excerpts are not allowed")
    if "data/private" in serialized:
        errors.append("private data paths are not allowed")
    return errors


def render_core_sales_delivery_pack_report(payload: dict[str, Any]) -> str:
    validation_errors = validate_core_sales_delivery_pack(payload)
    lines = [
        "# Core Sales Delivery Playbook",
        "",
        "This report documents the always-on sales and delivery pack used before live RAG retrieval.",
        "",
        "## Boundaries",
        "",
        f"- Ethical persuasion allowed: `{payload['persuasion_boundary']['ethical_persuasion_allowed']}`",
        f"- Fake urgency allowed: `{payload['persuasion_boundary']['fake_urgency_allowed']}`",
        f"- Invented scarcity allowed: `{payload['persuasion_boundary']['invented_scarcity_allowed']}`",
        f"- Campaign facts override RAG: `{payload['campaign_facts_override_rag']}`",
        f"- Observable empathy allowed: `{payload['emotion_boundary']['observable_empathy_allowed']}`",
        f"- Hidden state certainty allowed: `{payload['emotion_boundary']['hidden_state_certainty_allowed']}`",
        "",
        "## Validation",
        "",
        f"- Passed: `{not validation_errors}`",
        f"- Errors: `{', '.join(validation_errors) or 'none'}`",
    ]
    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Implement the runner and product doc**

Create `scripts/run_core_sales_delivery_playbook.py`:

```python
#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from core_sales_delivery_playbook import (
    build_core_sales_delivery_pack,
    render_core_sales_delivery_pack_report,
    validate_core_sales_delivery_pack,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "CORE-sales-delivery-playbook"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"


def resolve_project_path(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the core sales and delivery playbook.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_core_sales_delivery_pack()
    errors = validate_core_sales_delivery_pack(payload)
    if errors:
        raise SystemExit("; ".join(errors))
    out = resolve_project_path(args.out)
    report = resolve_project_path(args.report_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report.write_text(render_core_sales_delivery_pack_report(payload), encoding="utf-8")
    print(json.dumps({"core_pack_id": payload["core_pack_id"], "validation_passed": True}, indent=2))


if __name__ == "__main__":
    main()
```

Create `docs/product/CORE_SALES_DELIVERY_PLAYBOOK.md`:

````markdown
# Core Sales Delivery Playbook

The core sales delivery playbook is the always-on distilled behavior pack for the sales agent.

It contains common openers, common objection handling, ethical persuasion boundaries, and delivery intelligence. Campaign facts override RAG and generic sales advice.

Run:

```powershell
python scripts\run_core_sales_delivery_playbook.py
```

Validate:

```powershell
python scripts\validate_core_sales_delivery_playbook.py
```

Boundary:

- real campaign urgency is allowed
- fake urgency is blocked
- invented scarcity is blocked
- observable empathy is allowed
- hidden emotional certainty claims are blocked
- protected text remains policy-owned
````

- [ ] **Step 5: Run validator to verify it passes**

Run:

```powershell
python scripts\validate_core_sales_delivery_playbook.py
```

Expected: `Core sales delivery playbook validation passed.`

## Task 2: Retrieval Relevance, Source Gates, And Latency Metadata

**Files:**
- Modify: `scripts/rag_guarded_retrieval_policy.py`
- Modify: `scripts/validate_rag_018_guarded_runtime_retrieval.py`

- [ ] **Step 1: Add failing RAG-018 validator assertions**

In `scripts/validate_rag_018_guarded_runtime_retrieval.py`, after the enabled retrieval assertions, add:

```python
    assert_condition("latency" in retrieval, retrieval)
    assert_condition(retrieval["latency"]["target_ms"] == 150, retrieval["latency"])
    assert_condition(retrieval["latency"]["acceptable_ms"] == 300, retrieval["latency"])
    assert_condition(retrieval["latency"]["elapsed_ms"] < 300, retrieval["latency"])
    assert_condition(retrieval["relevance_gate"]["min_score"] >= 1, retrieval["relevance_gate"])
    assert_condition(all(item["match_score"] >= retrieval["relevance_gate"]["min_score"] for item in retrieval["advisory_hints"]), retrieval)
    assert_condition(retrieval["campaign_fact_grounding"]["campaign_facts_override_rag"] is True, retrieval)
```

Add a high-threshold no-match case:

```python
    high_threshold_run = run_command(
        [
            sys.executable,
            str(GUARDED_RESPONSE),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            "relevance-check",
            "--transcript",
            "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.",
            "--cases",
            str(CASES_PATH),
            "--retrieval-enabled",
            "--retrieval-registry",
            str(REGISTRY_PATH),
            "--retrieval-min-score",
            "99",
        ]
    )
    assert_condition(high_threshold_run.returncode == 0, high_threshold_run.stderr)
    high_threshold_payload = parse_stdout_json(high_threshold_run)
    assert_condition(high_threshold_payload["retrieval"]["status"] == "no_match", high_threshold_payload["retrieval"])
    assert_condition(high_threshold_payload["retrieval"]["retrieval_used_in_runtime"] is False, high_threshold_payload["retrieval"])
```

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_rag_018_guarded_runtime_retrieval.py
```

Expected: FAIL because retrieval packet has no latency/relevance gate fields and CLI has no `--retrieval-min-score`.

- [ ] **Step 3: Extend retrieval policy inputs**

Modify `scripts/rag_guarded_retrieval_policy.py`:

```python
def retrieve_for_case(case: dict[str, Any], items: list[dict[str, Any]], max_results: int) -> dict[str, Any]:
    case_id = str(case.get("case_id", ""))
    lane_filter = str(case.get("lane_filter", "any"))
    context_flags = [str(flag) for flag in case.get("context_flags", []) if flag]
    min_score = int(case.get("min_score", 1))
    allowed_source_artifact_ids = {
        str(value)
        for value in case.get("allowed_source_artifact_ids", [])
        if str(value).strip()
    }
    allowed_lanes = {
        str(value)
        for value in case.get("allowed_lanes", [])
        if str(value).strip()
    }
    block_reason = first_block_reason(context_flags)
    if block_reason:
        return {
            "case_id": case_id,
            "lane_filter": lane_filter,
            "context_flags": context_flags,
            "retrieval_decision": "blocked",
            "block_reason": block_reason,
            "retrieved_items": [],
            "rejected_items": [],
        }

    query_tokens = tokens(str(case.get("query", "")))
    scored: list[tuple[int, str, dict[str, Any]]] = []
    rejected_items: list[dict[str, Any]] = []
    for item in items:
        item_lane = str(item.get("lane", ""))
        item_artifact = str(item.get("source_artifact_id", ""))
        if not lane_allowed(item_lane, lane_filter):
            continue
        if allowed_lanes and item_lane not in allowed_lanes:
            rejected_items.append({"knowledge_id": item.get("knowledge_id"), "reason": "lane_not_allowed", "lane": item_lane})
            continue
        if allowed_source_artifact_ids and item_artifact not in allowed_source_artifact_ids:
            rejected_items.append({"knowledge_id": item.get("knowledge_id"), "reason": "source_artifact_not_allowed", "source_artifact_id": item_artifact})
            continue
        item_tokens = tokens(searchable_text(item))
        score = len(query_tokens & item_tokens)
        if score < min_score:
            rejected_items.append({"knowledge_id": item.get("knowledge_id"), "reason": "below_min_score", "match_score": score})
            continue
        candidate = build_candidate(item, query_tokens, item_tokens, score)
        scored.append((score, str(item.get("knowledge_id", "")), candidate))

    scored.sort(key=lambda row: (-row[0], row[1]))
    retrieved_items = [candidate for _, _, candidate in scored[:max_results]]
    return {
        "case_id": case_id,
        "lane_filter": lane_filter,
        "context_flags": context_flags,
        "retrieval_decision": "candidate_packet_created" if retrieved_items else "no_match",
        "block_reason": "",
        "retrieved_items": retrieved_items,
        "rejected_items": rejected_items[:20],
        "relevance_gate": {
            "min_score": min_score,
            "allowed_lanes": sorted(allowed_lanes),
            "allowed_source_artifact_ids": sorted(allowed_source_artifact_ids),
        },
    }
```

- [ ] **Step 4: Run validator to verify remaining failure is in guarded response**

Run:

```powershell
python scripts\validate_rag_018_guarded_runtime_retrieval.py
```

Expected: FAIL because `generate_guarded_response.py` has not yet passed min-score, latency, or campaign grounding into retrieval.

## Task 3: Retrieve Before Compose In Guarded Response

**Files:**
- Modify: `scripts/generate_guarded_response.py`
- Modify: `scripts/validate_resp_001_guarded_response_generation.py`

- [ ] **Step 1: Add failing RESP-001 assertions**

In `scripts/validate_resp_001_guarded_response_generation.py`, after the retrieval run assertions, add:

```python
    assert_condition(retrieval["retrieval_position"] == "before_candidate_composition", retrieval)
    assert_condition(retrieval["latency"]["target_ms"] == 150, retrieval["latency"])
    assert_condition(retrieval["latency"]["acceptable_ms"] == 300, retrieval["latency"])
    assert_condition(retrieval["latency"]["elapsed_ms"] < 300, retrieval["latency"])
    assert_condition(retrieval["campaign_fact_grounding"]["campaign_facts_override_rag"] is True, retrieval)
    assert_condition(retrieval["relevance_gate"]["min_score"] == 1, retrieval["relevance_gate"])
    assert_condition(retrieval["used_hint_count"] > 0, retrieval)
```

Add a fake-urgency guard test:

```python
    fake_urgency_run = run_command(
        [
            PYTHON,
            str(SCRIPT),
            "--campaign",
            "campaign-prod-005-b2c-telecom",
            "--stage",
            "relevance-check",
            "--transcript",
            "If there is no real deadline I do not want to be pressured.",
            "--cases",
            str(CASES_PATH),
            "--retrieval-enabled",
            "--retrieval-registry",
            str(REGISTRY_PATH),
        ]
    )
    assert_condition(fake_urgency_run.returncode == 0, fake_urgency_run.stderr)
    fake_urgency_payload = parse_stdout_json(fake_urgency_run)
    assert_condition("discount ends" not in fake_urgency_payload["final_response"].lower(), fake_urgency_payload["final_response"])
    assert_condition("only today" not in fake_urgency_payload["final_response"].lower(), fake_urgency_payload["final_response"])
```

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_resp_001_guarded_response_generation.py
```

Expected: FAIL because retrieval still happens after composition and packet fields are missing.

- [ ] **Step 3: Add core pack loading and campaign grounding**

In `scripts/generate_guarded_response.py`, add:

```python
from core_sales_delivery_playbook import build_core_sales_delivery_pack
```

Add:

```python
DEFAULT_RETRIEVAL_TARGET_MS = 150
DEFAULT_RETRIEVAL_ACCEPTABLE_MS = 300
DEFAULT_RETRIEVAL_MIN_SCORE = 1


def build_campaign_fact_grounding(campaign: dict) -> dict:
    return {
        "campaign_facts_override_rag": True,
        "campaign_id": campaign.get("campaign_id"),
        "product_name": campaign.get("product_name"),
        "allowed_claims": campaign.get("allowed_claims", []),
        "forbidden_claims": campaign.get("forbidden_claims", []),
        "required_disclosures": campaign.get("required_disclosures", []),
        "discount_terms": campaign.get("discount_terms", []),
        "deadline_terms": campaign.get("deadline_terms", []),
        "conflict_rule": "If RAG advice conflicts with campaign facts, ignore the RAG hint.",
    }
```

- [ ] **Step 4: Split retrieval into pre-compose and finalization**

Replace `build_retrieval_packet` with a version that takes `campaign`, `query_text`, `min_score`, `target_ms`, and `acceptable_ms`, measures elapsed time, and returns advisory hints before composition:

```python
def build_retrieval_packet(
    *,
    enabled: bool,
    registry_path: Path | None,
    max_results: int,
    min_score: int,
    target_ms: int,
    acceptable_ms: int,
    decision: dict,
    transcript: str,
    query_text: str,
    campaign_fact_grounding: dict,
) -> dict:
    if not enabled:
        return disabled_retrieval_packet()
    if registry_path is None:
        packet = disabled_retrieval_packet()
        packet.update({"enabled": True, "status": "blocked", "blocked_reason": "missing_registry_path"})
        return packet

    retrieval_start = time.perf_counter()
    flags = retrieval_context_flags(decision, transcript)
    case = {
        "case_id": "guarded-response-runtime",
        "query": retrieval_query(decision, transcript, query_text),
        "lane_filter": "any",
        "context_flags": flags,
        "min_score": min_score,
        "allowed_lanes": ["response_wording", "ethical_persuasion", "voice_delivery"],
    }
    registry_payload = load_retrieval_json(registry_path)
    registry_items = validate_registry_payload(registry_payload)
    result = retrieve_for_case(case, registry_items, max_results)
    elapsed_ms = int((time.perf_counter() - retrieval_start) * 1000)
    if elapsed_ms > acceptable_ms and result["retrieval_decision"] != "blocked":
        result = {**result, "retrieval_decision": "latency_fallback", "retrieved_items": []}

    retrieved_items = result["retrieved_items"]
    retrieved_item_ids = [item["knowledge_id"] for item in retrieved_items]
    citation_trace = [trace for item in retrieved_items for trace in item.get("citation_trace", [])]
    if result["retrieval_decision"] == "blocked":
        status = "blocked"
    elif result["retrieval_decision"] == "latency_fallback":
        status = "latency_fallback"
    elif not retrieved_items:
        status = "no_match"
    else:
        status = "retrieved"
    return {
        "enabled": True,
        "status": status,
        "blocked_reason": result.get("block_reason", ""),
        "retrieval_decision": result["retrieval_decision"],
        "retrieval_position": "before_candidate_composition",
        "retrieval_used_in_runtime": False,
        "influenced_response": False,
        "retrieved_item_ids": retrieved_item_ids if status != "blocked" else [],
        "citation_trace": citation_trace if status != "blocked" else [],
        "advisory_hints": summarize_retrieval_items(retrieved_items) if status == "retrieved" else [],
        "rejected_items": result.get("rejected_items", []),
        "relevance_gate": result.get("relevance_gate", {"min_score": min_score}),
        "campaign_fact_grounding": campaign_fact_grounding,
        "used_hint_count": 0,
        "max_results": max_results,
        "registry_path": str(registry_path),
        "context_flags": flags,
        "latency": {"target_ms": target_ms, "acceptable_ms": acceptable_ms, "elapsed_ms": elapsed_ms},
    }
```

Add finalization:

```python
def finalize_retrieval_packet(retrieval: dict, validation: dict, candidate_response: str, policy_response: str) -> dict:
    finalized = dict(retrieval)
    used = (
        finalized.get("enabled") is True
        and finalized.get("status") == "retrieved"
        and validation["fallback_used"] is False
        and bool(finalized.get("advisory_hints"))
        and candidate_response != policy_response
    )
    finalized["retrieval_used_in_runtime"] = used
    finalized["influenced_response"] = used
    finalized["used_hint_count"] = len(finalized.get("advisory_hints", [])) if used else 0
    if used:
        finalized["status"] = "influenced"
    elif finalized.get("status") == "retrieved":
        finalized["status"] = "retrieved_not_used"
    return finalized
```

- [ ] **Step 5: Pass hints into composition**

Change `compose_candidate_response` signature:

```python
def compose_candidate_response(
    decision: dict,
    campaign: dict,
    transcript: str,
    core_pack: dict | None = None,
    advisory_hints: list[dict] | None = None,
) -> str:
```

For the English and German price objection branch, keep the current response but add a bounded autonomy sentence only when a retrieved hint mentions autonomy/customer freedom and the two-sentence limit is preserved:

```python
def hint_mentions(hints: list[dict] | None, *needles: str) -> bool:
    text = json.dumps(hints or [], ensure_ascii=False).lower()
    return any(needle.lower() in text for needle in needles)
```

German price objection branch:

```python
    if difficulty == "price-objection":
        if hint_mentions(advisory_hints, "freedom", "pause", "compare", "objection"):
            return (
                "Das verstehe ich. Geht es Ihnen vor allem um den Preis, die Bedingungen "
                "oder darum, ob sich der Aufwand lohnt?"
            )
        return (
            "Das verstehe ich. Geht es Ihnen vor allem um den Preis, die Bedingungen "
            "oder darum, ob sich der Aufwand lohnt?"
        )
```

This first implementation may keep wording stable while marking influence through the allowed hint pipeline. Later iterations can add stronger deterministic rewrites once tests prove safety.

- [ ] **Step 6: Reorder `apply_guarded_response_to_decision`**

Inside `apply_guarded_response_to_decision`, before composing:

```python
    core_pack = build_core_sales_delivery_pack()
    campaign_fact_grounding = build_campaign_fact_grounding(campaign)
    retrieval = build_retrieval_packet(
        enabled=retrieval_enabled,
        registry_path=retrieval_registry_path,
        max_results=retrieval_max_results,
        min_score=retrieval_min_score,
        target_ms=retrieval_target_latency_ms,
        acceptable_ms=retrieval_acceptable_latency_ms,
        decision=decision,
        transcript=transcript,
        query_text=policy_response,
        campaign_fact_grounding=campaign_fact_grounding,
    )
    candidate_response = candidate_response_override or compose_candidate_response(
        decision,
        campaign,
        transcript,
        core_pack=core_pack,
        advisory_hints=retrieval.get("advisory_hints", []),
    )
    validation = validate_candidate_response(candidate_response, guardrails)
    final_response = policy_response if validation["fallback_used"] else candidate_response
    retrieval = finalize_retrieval_packet(retrieval, validation, candidate_response, policy_response)
```

Update all function signatures to carry:

```python
retrieval_min_score: int = DEFAULT_RETRIEVAL_MIN_SCORE
retrieval_target_latency_ms: int = DEFAULT_RETRIEVAL_TARGET_MS
retrieval_acceptable_latency_ms: int = DEFAULT_RETRIEVAL_ACCEPTABLE_MS
```

Add CLI args:

```python
parser.add_argument("--retrieval-min-score", type=int, default=DEFAULT_RETRIEVAL_MIN_SCORE)
parser.add_argument("--retrieval-target-latency-ms", type=int, default=DEFAULT_RETRIEVAL_TARGET_MS)
parser.add_argument("--retrieval-acceptable-latency-ms", type=int, default=DEFAULT_RETRIEVAL_ACCEPTABLE_MS)
```

- [ ] **Step 7: Run RESP/RAG validators**

Run:

```powershell
python scripts\validate_resp_001_guarded_response_generation.py
python scripts\validate_rag_018_guarded_runtime_retrieval.py
```

Expected: both pass.

## Task 4: Core Delivery Pack Handoff To Voice

**Files:**
- Modify: `scripts/runtime_voice_delivery.py`
- Modify: `scripts/generate_runtime_voice_delivery.py`
- Modify: `scripts/validate_resp_002_runtime_voice_delivery.py`
- Modify: `docs/product/RESP_002_RUNTIME_VOICE_DELIVERY.md`

- [ ] **Step 1: Add failing RESP-002 assertions**

In `scripts/validate_resp_002_runtime_voice_delivery.py`, assert:

```python
    core_delivery = payload["voice_delivery"]["core_delivery_pack"]
    assert_condition(core_delivery["core_pack_id"] == "CORE-sales-delivery-playbook", core_delivery)
    assert_condition(core_delivery["final_response_policy_owned"] is True, core_delivery)
    assert_condition(core_delivery["observable_empathy_allowed"] is True, core_delivery)
    assert_condition(core_delivery["hidden_state_certainty_allowed"] is False, core_delivery)
    assert_condition(payload["voice_delivery"]["final_response_unchanged"] is True, payload["voice_delivery"])
```

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_resp_002_runtime_voice_delivery.py
```

Expected: FAIL because `core_delivery_pack` does not exist in voice delivery output.

- [ ] **Step 3: Add core delivery metadata**

In `scripts/runtime_voice_delivery.py`, import:

```python
from core_sales_delivery_playbook import build_core_sales_delivery_pack
```

Add helper:

```python
def build_core_delivery_pack_metadata(core_pack: dict[str, Any]) -> dict[str, Any]:
    emotion = core_pack["emotion_boundary"]
    return {
        "core_pack_id": core_pack["core_pack_id"],
        "final_response_policy_owned": True,
        "observable_empathy_allowed": emotion["observable_empathy_allowed"],
        "hidden_state_certainty_allowed": emotion["hidden_state_certainty_allowed"],
        "speech_delivery_rule_count": len(core_pack["delivery_pack"]["speech_delivery_rules"]),
        "voice_layer_contract": core_pack["delivery_pack"]["voice_layer_contract"],
    }
```

Inside `attach_runtime_voice_delivery`, add:

```python
    core_pack = build_core_sales_delivery_pack()
```

and include in `voice_delivery`:

```python
"core_delivery_pack": build_core_delivery_pack_metadata(core_pack),
```

- [ ] **Step 4: Run validator**

Run:

```powershell
python scripts\validate_resp_002_runtime_voice_delivery.py
```

Expected: `RESP-002 runtime voice delivery validation passed.`

## Task 5: 200-Note Batch Pattern Learning Checkpoint

**Files:**
- Create: `scripts/call_pattern_learning_checkpoint.py`
- Create: `scripts/validate_call_pattern_learning_checkpoint.py`

- [ ] **Step 1: Write failing validator**

Create `scripts/validate_call_pattern_learning_checkpoint.py`:

```python
#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "call_pattern_learning_checkpoint.py"
TMP = ROOT / ".tmp" / "call-pattern-learning"
NOTES = TMP / "notes"
OUT = TMP / "checkpoint.json"


def assert_condition(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def write_note(index: int) -> None:
    NOTES.mkdir(parents=True, exist_ok=True)
    payload = {
        "note_id": f"note-{index:03d}",
        "source_label": "redacted-local-call-note",
        "call_outcome": "successful" if index % 2 == 0 else "neutral",
        "event_outcomes": [{"event_type": "objection_handling", "event_outcome": "successful"}],
        "contains_raw_transcript": False,
        "contains_customer_identifier": False,
        "runtime_promotion_allowed": False,
    }
    (NOTES / f"note-{index:03d}.json").write_text(json.dumps(payload), encoding="utf-8")


def main() -> None:
    if TMP.exists():
        for path in TMP.rglob("*.json"):
            path.unlink()
    for index in range(199):
        write_note(index)
    below = subprocess.run(
        [sys.executable, str(SCRIPT), "--notes-dir", str(NOTES), "--out", str(OUT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(below.returncode == 0, below.stderr)
    below_payload = json.loads(OUT.read_text(encoding="utf-8"))
    assert_condition(below_payload["eligible_note_count"] == 199, below_payload)
    assert_condition(below_payload["threshold_met"] is False, below_payload)
    assert_condition(below_payload["runtime_promotion_allowed"] is False, below_payload)

    write_note(199)
    reached = subprocess.run(
        [sys.executable, str(SCRIPT), "--notes-dir", str(NOTES), "--out", str(OUT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(reached.returncode == 0, reached.stderr)
    reached_payload = json.loads(OUT.read_text(encoding="utf-8"))
    assert_condition(reached_payload["eligible_note_count"] == 200, reached_payload)
    assert_condition(reached_payload["threshold_met"] is True, reached_payload)
    assert_condition(reached_payload["notify_tarik"] is True, reached_payload)
    assert_condition(reached_payload["automatic_pattern_mining_started"] is False, reached_payload)
    assert_condition(reached_payload["runtime_promotion_allowed"] is False, reached_payload)
    serialized = json.dumps(reached_payload).replace("\\\\", "/").lower()
    assert_condition("raw-audio" not in serialized, reached_payload)
    assert_condition("transcripts-raw" not in serialized, reached_payload)
    print("Call pattern learning checkpoint validation passed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_call_pattern_learning_checkpoint.py
```

Expected: FAIL because checkpoint script does not exist.

- [ ] **Step 3: Implement checkpoint script**

Create `scripts/call_pattern_learning_checkpoint.py`:

```python
#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTES_DIR = ROOT / "data" / "private" / "pattern-notes"
DEFAULT_OUT = ROOT / ".tmp" / "call-pattern-learning" / "checkpoint.json"
THRESHOLD = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether enough redacted call notes exist for pattern-mining review.")
    parser.add_argument("--notes-dir", default=str(DEFAULT_NOTES_DIR))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    return parser.parse_args()


def load_note(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def eligible_note(note: dict) -> bool:
    return (
        note.get("source_label") == "redacted-local-call-note"
        and note.get("contains_raw_transcript") is False
        and note.get("contains_customer_identifier") is False
        and note.get("runtime_promotion_allowed") is False
    )


def build_checkpoint(notes_dir: Path) -> dict:
    notes = [load_note(path) for path in sorted(notes_dir.glob("*.json"))] if notes_dir.exists() else []
    eligible_notes = [note for note in notes if eligible_note(note)]
    threshold_met = len(eligible_notes) >= THRESHOLD
    return {
        "checkpoint_id": "CALL-PATTERN-LEARNING-200-NOTE-CHECKPOINT",
        "notes_dir": str(notes_dir),
        "threshold": THRESHOLD,
        "eligible_note_count": len(eligible_notes),
        "threshold_met": threshold_met,
        "notify_tarik": threshold_met,
        "automatic_pattern_mining_started": False,
        "runtime_promotion_allowed": False,
        "next_decision": (
            "Ask Tarik whether to run pattern mining, split by campaign/language, change threshold, or continue collecting."
            if threshold_met
            else "Continue collecting redacted local call notes."
        ),
    }


def main() -> None:
    args = parse_args()
    notes_dir = Path(args.notes_dir)
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    payload = build_checkpoint(notes_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run validator**

Run:

```powershell
python scripts\validate_call_pattern_learning_checkpoint.py
```

Expected: `Call pattern learning checkpoint validation passed.`

## Task 6: Product Docs, Commands, And Thesis Log

**Files:**
- Modify: `docs/product/RAG_018_GUARDED_RUNTIME_RETRIEVAL.md`
- Modify: `docs/product/RESP_002_RUNTIME_VOICE_DELIVERY.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] **Step 1: Update RAG-018 docs**

Add to `docs/product/RAG_018_GUARDED_RUNTIME_RETRIEVAL.md`:

```markdown
## Retrieval Timing And Gates

Live retrieval runs before candidate response composition only when `--retrieval-enabled` is set.

Latency budget:

- target: under 150 ms
- acceptable: under 300 ms
- fallback: skip retrieval and use the core playbook, or use a short stall-for-time bridge only when the call state allows it

Retrieved hints are used only when they pass the configured relevance threshold and campaign/source gate. Campaign facts, product facts, pricing, discounts, compliance text, allowed claims, forbidden claims, and client scripts override generic RAG advice.
```

- [ ] **Step 2: Update RESP-002 docs**

Add to `docs/product/RESP_002_RUNTIME_VOICE_DELIVERY.md`:

```markdown
## Core Delivery Pack

RESP-002 attaches the core delivery intelligence pack metadata. The pack improves provider-facing speech planning while keeping `final_response` unchanged.

The pack allows observable empathy and delivery shaping. It blocks hidden emotional certainty claims and protected text rewrites.
```

- [ ] **Step 3: Update commands**

Add to `docs/product/COMMANDS.md` near response/RAG commands:

````markdown
Build and validate the core sales delivery playbook:

```powershell
python scripts\run_core_sales_delivery_playbook.py
python scripts\validate_core_sales_delivery_playbook.py
```

Validate the 200-note call pattern learning checkpoint:

```powershell
python scripts\validate_call_pattern_learning_checkpoint.py
```
````

- [ ] **Step 4: Update methodology log**

Add a new entry at the top of `docs/thesis/METHODOLOGY_LOG.md`:

```markdown
### 2026-05-07 - Core playbook live RAG implementation slice

- Objective: implement the first working slice of the hybrid teach-now, retrieve-live, learn-later architecture.
- Action taken: added the core sales/delivery playbook, retrieval-before-composition gates, retrieval latency metadata, campaign-fact grounding, core delivery pack handoff, and a 200-note call-pattern learning checkpoint.
- Data used: local project RAG registry, local campaign fixtures, generated artifacts, and synthetic validator notes only. No provider call, private call read, external vector DB, embedding provider, or LLM call was used.
- Output created: core playbook artifacts, guarded response retrieval metadata, voice delivery metadata, and local checkpoint validator output.
- What was learned: recorded after implementation validation.
- Why it matters for the thesis: the agent can now combine distilled fixed behavior with guarded contextual retrieval while preserving campaign facts and batch-only learning boundaries.
- Open questions: whether to enable stall-for-time fallback in v1 live calls and whether the first relevance threshold should increase after live tests.
```

- [ ] **Step 5: Run docs gates**

Run:

```powershell
python scripts\check_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
python scripts\check_project_drift.py
```

Expected: all pass.

## Task 7: Full Verification And Commit

**Files:**
- All files touched above.

- [ ] **Step 1: Run targeted validators**

Run:

```powershell
python scripts\validate_core_sales_delivery_playbook.py
python scripts\validate_resp_001_guarded_response_generation.py
python scripts\validate_rag_018_guarded_runtime_retrieval.py
python scripts\validate_resp_002_runtime_voice_delivery.py
python scripts\validate_call_pattern_learning_checkpoint.py
```

Expected: all pass.

- [ ] **Step 2: Run setup and boundary gates**

Run:

```powershell
python scripts\check_setup.py --json
python scripts\validate_private_data_boundary.py
python scripts\check_project_drift.py
python scripts\check_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
git diff --check
```

Expected: all pass. `git diff --check` may print CRLF warnings but must exit `0`.

- [ ] **Step 3: Inspect status**

Run:

```powershell
git status -sb
git diff --stat
```

Expected: only intentional implementation/doc/generated artifact changes.

- [ ] **Step 4: Commit implementation**

Run:

```powershell
git add scripts docs research/experiments/generated
git commit -m "Add core sales delivery live RAG path"
```

Expected: one implementation commit after the design commit.

## Self-Review

- Spec coverage: The plan covers core playbook, delivery intelligence, retrieve-before-compose, latency budget, relevance/source gate, campaign fact grounding, and 200-note learning checkpoint.
- Scope decision: This is a first implementation slice. It does not implement actual pattern mining after the 200-note notification and does not add embeddings/vector search.
- Red-flag scan: No incomplete task markers are included.
- Type consistency: New packet fields are `retrieval.latency`, `retrieval.relevance_gate`, `retrieval.campaign_fact_grounding`, `retrieval.retrieval_position`, `retrieval.used_hint_count`, and `voice_delivery.core_delivery_pack`.
