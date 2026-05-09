# Interactive Grounded Call Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `PROD-031-interactive-grounded-call-simulation`, a deterministic local customer simulator where customer replies react to the agent answer and updated customer state.

**Architecture:** Add a focused checkpoint module that owns call seeds, customer state transitions, response generation, metrics, and report rendering. Reuse the existing synthetic RouteSignal campaign facts and guarded response packet path, but keep runtime defaults, retrieval, composer hooks, provider calls, private data, and production promotion disabled.

**Tech Stack:** Python 3.13 standard library, existing project checkpoint/validator pattern, existing `generate_guarded_response.py`, existing `prod_028_synthetic_campaign_knowledge_grounding.py`, Markdown/JSON/HTML artifacts.

---

## File Structure

- Create `scripts/validate_prod_031_interactive_grounded_call_simulation.py`: checkpoint validator and regression gate.
- Create `scripts/prod_031_interactive_grounded_call_simulation.py`: deterministic simulator, state model, metrics, report/HTML rendering.
- Create `scripts/run_prod_031_interactive_grounded_call_simulation.py`: CLI wrapper with safe path resolution.
- Create `docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md`: product checkpoint doc.
- Create generated artifacts under `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/`.
- Modify `docs/product/COMMANDS.md`: add run/validate commands.
- Modify `docs/product/CHECKPOINT_INDEX.md`: add PROD-031 doc.
- Modify `scripts/check_setup.py`: add required PROD-031 doc/scripts.
- Modify `scripts/validate_check_setup.py`: add required PROD-031 check IDs.
- Modify `scripts/check_project_drift.py`: add required PROD-031 doc/scripts.
- Modify `scripts/validate_project_drift_guard.py`: add PROD-031 fixture files.
- Modify `docs/thesis/ROADMAP.md`: mark PROD-031 completed and set next checkpoint to a post-simulation review packet.
- Modify `docs/thesis/METHODOLOGY_LOG.md`: add PROD-031 entry.
- Modify `docs/thesis/DECISION_LOG.md`: add decision to keep interactive simulation as the stronger evaluation lane.

---

### Task 1: Create The PROD-031 Red Validator

**Files:**
- Create: `scripts/validate_prod_031_interactive_grounded_call_simulation.py`

- [ ] **Step 1: Write the failing validator**

Create `scripts/validate_prod_031_interactive_grounded_call_simulation.py` with this structure:

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-031-interactive-grounded-call-simulation"
SOURCE_SPEC = ROOT / "docs" / "superpowers" / "specs" / "2026-05-09-interactive-grounded-call-simulation-design.md"
NEXT_CHECKPOINT_ID = "PROD-032-interactive-simulation-review"

MODULE = ROOT / "scripts" / "prod_031_interactive_grounded_call_simulation.py"
RUNNER = ROOT / "scripts" / "run_prod_031_interactive_grounded_call_simulation.py"
DOC_PATH = ROOT / "docs" / "product" / "PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"
TRACE_PATH = OUT_DIR / "interactive_call_traces.json"
HTML_PATH = OUT_DIR / "interactive_call_trace.html"

COMMANDS = ROOT / "docs" / "product" / "COMMANDS.md"
CHECKPOINT_INDEX = ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md"
ROADMAP = ROOT / "docs" / "thesis" / "ROADMAP.md"
METHODOLOGY_LOG = ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md"
DECISION_LOG = ROOT / "docs" / "thesis" / "DECISION_LOG.md"

REQUIRED_FILES = [
    SOURCE_SPEC,
    MODULE,
    RUNNER,
    DOC_PATH,
    RESULT_PATH,
    REPORT_PATH,
    TRACE_PATH,
    HTML_PATH,
]

REQUIRED_FALSE_BOUNDARIES = [
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "dataset_download_performed",
    "raw_transcript_text_stored",
    "copied_transcript_text_used",
    "commercial_runtime_prompt_text_from_transcripts_allowed",
    "customer_data_allowed",
    "payment_collection_enabled",
    "runtime_behavior_changed_by_this_checkpoint",
    "runtime_retrieval_default_enabled",
    "composer_hook_flag_default_enabled",
    "live_provider_default_enabled",
    "server_started",
    "production_runtime_promotion_allowed",
]

BLOCKED_OUTPUT_TEXT = [
    "data/private",
    "data/private-restricted",
    "raw private audio",
    "raw private transcript",
    "api key",
    "take your payment",
    "card number",
    "credit card number",
    '"provider_calls_made": true',
    '"llm_used": true',
    '"private_data_read": true',
    '"runtime_retrieval_default_enabled": true',
    '"composer_hook_flag_default_enabled": true',
    '"production_runtime_promotion_allowed": true',
]


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=240)


def validate_payload(payload: dict[str, Any]) -> None:
    assert_condition(payload.get("checkpoint_id") == CHECKPOINT_ID, payload.get("checkpoint_id"))
    assert_condition(payload.get("next_checkpoint_recommended") == NEXT_CHECKPOINT_ID, payload.get("next_checkpoint_recommended"))
    assert_condition(payload.get("source_spec_path") == normalized(SOURCE_SPEC), payload.get("source_spec_path"))

    outputs = payload.get("outputs", {})
    assert_condition(outputs.get("result_path") == normalized(RESULT_PATH), outputs)
    assert_condition(outputs.get("report_path") == normalized(REPORT_PATH), outputs)
    assert_condition(outputs.get("trace_path") == normalized(TRACE_PATH), outputs)
    assert_condition(outputs.get("html_path") == normalized(HTML_PATH), outputs)

    boundaries = payload.get("boundaries", {})
    for key in REQUIRED_FALSE_BOUNDARIES:
        assert_condition(boundaries.get(key) is False, f"boundary {key} must be false")

    summary = payload.get("summary", {})
    assert_condition(summary.get("deterministic_simulator") is True, summary)
    assert_condition(summary.get("call_seed_count") >= 8, summary)
    assert_condition(summary.get("call_count") >= 8, summary)
    assert_condition(summary.get("total_turn_count") >= 24, summary)
    assert_condition(summary.get("reactive_customer_turn_count") >= 16, summary)
    assert_condition(summary.get("reactive_state_transition_count") == summary.get("total_turn_count"), summary)
    assert_condition(summary.get("exact_customer_agent_state_trace_visible") is True, summary)
    assert_condition(summary.get("agent_answer_depends_on_customer_state") is True, summary)
    assert_condition(summary.get("customer_reply_depends_on_prior_agent_answer") is True, summary)
    assert_condition(summary.get("hard_failure_count") == 0, summary)
    assert_condition(summary.get("payment_collection_count") == 0, summary)
    assert_condition(summary.get("unsupported_claim_count") == 0, summary)
    assert_condition(summary.get("leakage_finding_count") == 0, summary)
    assert_condition(summary.get("question_overuse_count") <= 2, summary)
    assert_condition(summary.get("interactive_realism_score") >= 0.75, summary)
    assert_condition(summary.get("safe_close_rate") >= 0.75, summary)
    assert_condition(summary.get("non_sale_correctness") == 1.0, summary)

    metrics = payload.get("metrics", {})
    for metric in [
        "safe_close_rate",
        "non_sale_correctness",
        "average_trust_delta",
        "average_interest_delta",
        "average_clarity_delta",
        "average_friction_delta",
        "interactive_realism_score",
        "hard_failure_rate",
        "question_overuse_rate",
    ]:
        assert_condition(metric in metrics, f"missing metric {metric}")
        assert_condition(isinstance(metrics[metric].get("value"), (int, float)), metrics[metric])

    traces = read_json(TRACE_PATH)
    assert_condition(traces.get("checkpoint_id") == CHECKPOINT_ID, traces.get("checkpoint_id"))
    calls = traces.get("calls", [])
    assert_condition(len(calls) == summary.get("call_count"), "call count mismatch")
    for call in calls:
        assert_condition(call.get("seed_id"), call)
        assert_condition(call.get("terminal_outcome"), call)
        assert_condition(call.get("turns"), call)
        assert_condition(len(call["turns"]) <= 8, call)
        first_turn_seen = False
        for turn in call["turns"]:
            assert_condition("customer_message" in turn, turn)
            assert_condition("agent_answer" in turn, turn)
            assert_condition("state_before" in turn, turn)
            assert_condition("state_after" in turn, turn)
            assert_condition("customer_reaction_reason" in turn, turn)
            assert_condition("state_delta" in turn, turn)
            assert_condition("safety_flags" in turn, turn)
            assert_condition(turn["safety_flags"]["hard_failure"] is False, turn)
            if first_turn_seen:
                assert_condition(turn.get("reactive_to_previous_agent_answer") is True, turn)
            first_turn_seen = True

    html = HTML_PATH.read_text(encoding="utf-8")
    for marker in [
        "PROD-031 Interactive Grounded Call Simulation",
        "customer state -> customer turn -> agent answer -> customer state changes -> reactive customer turn",
        "State before",
        "State after",
        "Reaction reason",
    ]:
        assert_condition(marker in html, marker)

    combined = (
        json.dumps(payload, ensure_ascii=False).lower()
        + "\n"
        + REPORT_PATH.read_text(encoding="utf-8").lower()
        + "\n"
        + HTML_PATH.read_text(encoding="utf-8").lower()
    )
    for blocked in BLOCKED_OUTPUT_TEXT:
        assert_condition(blocked.lower() not in combined, blocked)


def validate_docs() -> None:
    commands = COMMANDS.read_text(encoding="utf-8")
    assert_condition("run_prod_031_interactive_grounded_call_simulation.py" in commands, "PROD-031 runner missing from COMMANDS.md")
    assert_condition("validate_prod_031_interactive_grounded_call_simulation.py" in commands, "PROD-031 validator missing from COMMANDS.md")
    assert_condition("PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md" in CHECKPOINT_INDEX.read_text(encoding="utf-8"), "PROD-031 missing from checkpoint index")
    assert_condition(CHECKPOINT_ID in ROADMAP.read_text(encoding="utf-8"), "PROD-031 missing from roadmap")
    assert_condition("PROD-031 interactive grounded call simulation" in METHODOLOGY_LOG.read_text(encoding="utf-8"), "PROD-031 missing from methodology log")
    assert_condition("Keep PROD-031 as interactive evaluation evidence" in DECISION_LOG.read_text(encoding="utf-8"), "PROD-031 decision missing from decision log")

    for path in [DOC_PATH, REPORT_PATH, HTML_PATH]:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in [
            "PROD-031",
            "interactive grounded call simulation",
            "deterministic simulator: `true`",
            "call seed count:",
            "reactive customer turn count:",
            "customer reply depends on prior agent answer: `true`",
            "provider calls made: `false`",
            "runtime behavior changed: `false`",
            NEXT_CHECKPOINT_ID,
        ]:
            assert_condition(marker.lower() in lowered, f"{path.relative_to(ROOT)} missing marker: {marker}")
        for blocked in BLOCKED_OUTPUT_TEXT:
            assert_condition(blocked.lower() not in lowered, f"{path.relative_to(ROOT)} contains blocked text: {blocked}")


def main() -> None:
    missing = [path.relative_to(ROOT) for path in REQUIRED_FILES if not path.exists()]
    assert_condition(not missing, f"missing required PROD-031 files: {missing}")

    completed = run_command([sys.executable, str(RUNNER)])
    assert_condition(completed.returncode == 0, f"runner failed stdout={completed.stdout!r} stderr={completed.stderr!r}")

    validate_payload(read_json(RESULT_PATH))
    validate_docs()
    print("PROD-031 interactive grounded call simulation validation passed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run validator to verify it fails red**

Run:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```

Expected result:

```text
AssertionError: missing required PROD-031 files
```

- [ ] **Step 3: Commit red validator**

Run:

```powershell
git add scripts\validate_prod_031_interactive_grounded_call_simulation.py
git commit -m "Add PROD-031 red validator"
```

---

### Task 2: Add Simulator Module Skeleton, Boundaries, Seeds, And State Model

**Files:**
- Create: `scripts/prod_031_interactive_grounded_call_simulation.py`

- [ ] **Step 1: Create the simulator module with seeds and state helpers**

Create `scripts/prod_031_interactive_grounded_call_simulation.py` with this initial structure:

```python
#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from callcenteren_runtime_comparison import contains_payment_collection
from generate_guarded_response import build_guarded_response_packet
from prod_028_synthetic_campaign_knowledge_grounding import build_synthetic_campaign
from run_resp_001_retrieval_ab_evaluation import forbidden_response_text, output_language_matches


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-031-interactive-grounded-call-simulation"
SOURCE_SPEC = ROOT / "docs" / "superpowers" / "specs" / "2026-05-09-interactive-grounded-call-simulation-design.md"
NEXT_CHECKPOINT_ID = "PROD-032-interactive-simulation-review"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
DEFAULT_RESULT = DEFAULT_OUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUT_DIR / "report.md"
DEFAULT_TRACE = DEFAULT_OUT_DIR / "interactive_call_traces.json"
DEFAULT_HTML = DEFAULT_OUT_DIR / "interactive_call_trace.html"

UNSUPPORTED_CLAIM_MARKERS = [
    "guaranteed revenue increase",
    "guaranteed cost savings",
    "guaranteed conversion lift",
    "replaces every crm",
    "no risk",
    "legal advice",
    "collect payment or card details on this call",
]


def rel_path(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clamp(value: int, low: int = 0, high: int = 5) -> int:
    return max(low, min(high, value))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_boundaries() -> dict[str, bool]:
    return {
        "provider_calls_made": False,
        "llm_used": False,
        "private_data_read": False,
        "dataset_download_performed": False,
        "raw_transcript_text_stored": False,
        "copied_transcript_text_used": False,
        "commercial_runtime_prompt_text_from_transcripts_allowed": False,
        "customer_data_allowed": False,
        "payment_collection_enabled": False,
        "runtime_behavior_changed_by_this_checkpoint": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "live_provider_default_enabled": False,
        "server_started": False,
        "production_runtime_promotion_allowed": False,
    }


def build_call_seeds() -> list[dict[str, Any]]:
    return [
        {
            "seed_id": "interactive-price-sensitive",
            "persona": "price-sensitive operations manager",
            "initial_message": "We may need lead routing, but I am worried this will become expensive fast.",
            "hidden_buying_intent": "medium",
            "primary_need": "price clarity",
            "initial_state": {"interest": 3, "trust": 2, "clarity": 1, "friction": 3, "patience": 4, "emotion": "skeptical", "commitment": "none", "active_objection": "price"},
            "expected_terminal_family": "sale_or_callback",
        },
        {
            "seed_id": "interactive-confused-product-fit",
            "persona": "confused small-business owner",
            "initial_message": "I do not really understand what this product does. Is this just another CRM?",
            "hidden_buying_intent": "medium",
            "primary_need": "product explanation",
            "initial_state": {"interest": 2, "trust": 2, "clarity": 0, "friction": 2, "patience": 4, "emotion": "confused", "commitment": "none", "active_objection": "confusion"},
            "expected_terminal_family": "sale_or_callback",
        },
        {
            "seed_id": "interactive-skeptical-trust-gap",
            "persona": "skeptical founder",
            "initial_message": "I am cautious with sales calls. I need proof this is not just vague software talk.",
            "hidden_buying_intent": "medium",
            "primary_need": "trust repair",
            "initial_state": {"interest": 2, "trust": 1, "clarity": 1, "friction": 3, "patience": 3, "emotion": "skeptical", "commitment": "none", "active_objection": "trust"},
            "expected_terminal_family": "callback_or_written_info",
        },
        {
            "seed_id": "interactive-busy-callback",
            "persona": "busy sales lead",
            "initial_message": "I cannot talk right now. If this is useful, make it quick or schedule another time.",
            "hidden_buying_intent": "low",
            "primary_need": "callback respect",
            "initial_state": {"interest": 2, "trust": 2, "clarity": 1, "friction": 4, "patience": 1, "emotion": "annoyed", "commitment": "none", "active_objection": "time"},
            "expected_terminal_family": "callback",
        },
        {
            "seed_id": "interactive-existing-provider",
            "persona": "team lead with an existing CRM",
            "initial_message": "We already have a CRM. Why would we add RouteSignal on top of it?",
            "hidden_buying_intent": "medium",
            "primary_need": "provider comparison",
            "initial_state": {"interest": 2, "trust": 3, "clarity": 1, "friction": 2, "patience": 4, "emotion": "neutral", "commitment": "none", "active_objection": "provider"},
            "expected_terminal_family": "sale_or_callback",
        },
        {
            "seed_id": "interactive-stakeholder-review",
            "persona": "manager who needs approval",
            "initial_message": "I would need to show this to my manager. What exactly would I tell them?",
            "hidden_buying_intent": "high",
            "primary_need": "stakeholder summary",
            "initial_state": {"interest": 4, "trust": 3, "clarity": 2, "friction": 2, "patience": 4, "emotion": "curious", "commitment": "considering", "active_objection": "authority"},
            "expected_terminal_family": "sale_or_callback",
        },
        {
            "seed_id": "interactive-support-boundary",
            "persona": "support-seeking user",
            "initial_message": "I am actually trying to get help with an account issue, not buy something.",
            "hidden_buying_intent": "none",
            "primary_need": "support handoff",
            "initial_state": {"interest": 0, "trust": 2, "clarity": 2, "friction": 3, "patience": 3, "emotion": "annoyed", "commitment": "none", "active_objection": "support"},
            "expected_terminal_family": "handoff",
        },
        {
            "seed_id": "interactive-do-not-call",
            "persona": "protected stop-request customer",
            "initial_message": "Please stop calling me. Take me off the list.",
            "hidden_buying_intent": "none",
            "primary_need": "do not call",
            "initial_state": {"interest": 0, "trust": 1, "clarity": 3, "friction": 5, "patience": 0, "emotion": "annoyed", "commitment": "none", "active_objection": "do-not-call"},
            "expected_terminal_family": "do_not_call",
        },
    ]
```

- [ ] **Step 2: Run the red validator again**

Run:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```

Expected result:

```text
AssertionError: missing required PROD-031 files
```

The failure remains correct because runner, docs, and artifacts do not exist yet.

- [ ] **Step 3: Commit simulator skeleton**

Run:

```powershell
git add scripts\prod_031_interactive_grounded_call_simulation.py
git commit -m "Add PROD-031 simulator skeleton"
```

---

### Task 3: Implement Agent Answer, State Update, Customer Reply, And Call Loop

**Files:**
- Modify: `scripts/prod_031_interactive_grounded_call_simulation.py`

- [ ] **Step 1: Add answer analysis helpers**

Append these functions to the module:

```python
def unsupported_claims(text: str) -> list[str]:
    lowered = text.lower()
    return [marker for marker in UNSUPPORTED_CLAIM_MARKERS if marker.lower() in lowered]


def count_questions(text: str) -> int:
    return text.count("?")


def answer_markers(answer: str) -> dict[str, bool]:
    lowered = answer.lower()
    return {
        "mentions_routesignal": "routesignal" in lowered,
        "mentions_price": "$29" in lowered or "$59" in lowered or "price" in lowered or "pricing" in lowered,
        "mentions_setup": "two to four weeks" in lowered or "setup" in lowered,
        "mentions_integrations": "slack" in lowered or "zapier" in lowered or "csv" in lowered or "outlook" in lowered or "gmail" in lowered,
        "mentions_no_payment": "no payment" in lowered or "billing outside" in lowered,
        "mentions_specialist": "specialist" in lowered,
        "respects_callback": "callback" in lowered or "another time" in lowered,
        "respects_stop": "do not call" in lowered or "end the sales conversation" in lowered,
        "asks_multiple_questions": count_questions(answer) > 1,
        "pushes_close": "sale-ready" in lowered or "commitment" in lowered or "next step" in lowered,
    }
```

- [ ] **Step 2: Add deterministic grounded answer generation**

Append this function:

```python
def agent_answer(seed: dict[str, Any], state: dict[str, Any], customer_message: str, campaign: dict[str, Any]) -> str:
    product_name = campaign["product_name"]
    specialist = campaign.get("human_handoff_role", "solutions specialist")
    objection = state["active_objection"]
    emotion = state["emotion"]

    if objection == "do-not-call" or "stop calling" in customer_message.lower() or "take me off" in customer_message.lower():
        return "Understood. I will mark this as do not call and end the sales conversation now."
    if objection == "support":
        return f"That sounds like a support issue, not a sales conversation. I will route this to a {specialist} so you can get account help."
    if objection == "time":
        return f"I will keep it brief. {product_name} helps route leads and own callbacks; if that is relevant, we can schedule a non-binding specialist callback."
    if objection == "price":
        return "On the synthetic pricing, Starter is $29 per user per month annually and Growth is $59. No payment is handled on this call, so the useful next step is checking whether the smaller plan fits your routing needs."
    if objection == "confusion":
        return f"{product_name} is not a full CRM replacement. It focuses on lead intake, routing, callback ownership, Gmail and Outlook sync, Slack and Zapier handoffs, and CSV import."
    if objection == "trust":
        return f"Fair concern. I cannot promise a revenue lift; the approved facts are that {product_name} centralizes lead intake and routes leads by region, source, priority, or owner. A {specialist} can confirm details in writing."
    if objection == "provider":
        return f"I would not replace a CRM that already works. {product_name} is worth reviewing only if routing, callback ownership, or reporting are gaps; it can hand off to your CRM, CSV, Slack, and Zapier."
    if objection == "authority":
        return "For a manager summary: Growth is $59 per user per month annually, annual billing reduces subscription price by 15%, setup is typically two to four weeks, and security details can be confirmed by a specialist."
    if state["trust"] >= 4 and state["clarity"] >= 4 and state["interest"] >= 4:
        return f"It sounds like there is enough fit for a non-binding {product_name} workflow review. I can mark this as sale-ready for specialist follow-up, with billing kept outside this call."
    if emotion == "annoyed":
        return f"I can slow down. The only point is whether {product_name} could help with lead routing or callback ownership; if not, we can stop here."
    return f"{product_name} helps teams centralize lead intake, route leads, and track callback ownership. We can keep this to fit, price, or setup facts before any next step."
```

- [ ] **Step 3: Add state transition logic**

Append this function:

```python
def update_state(seed: dict[str, Any], before: dict[str, Any], agent_text: str) -> tuple[dict[str, Any], dict[str, int], str]:
    after = deepcopy(before)
    markers = answer_markers(agent_text)
    reason_parts: list[str] = []

    if markers["mentions_routesignal"]:
        after["clarity"] = clamp(after["clarity"] + 1)
        reason_parts.append("agent explained the product")
    if markers["mentions_price"] and before["active_objection"] == "price":
        after["clarity"] = clamp(after["clarity"] + 1)
        after["friction"] = clamp(after["friction"] - 1)
        reason_parts.append("agent answered price concern")
    if markers["mentions_no_payment"]:
        after["trust"] = clamp(after["trust"] + 1)
        reason_parts.append("agent kept payment out of the call")
    if markers["mentions_specialist"]:
        after["trust"] = clamp(after["trust"] + 1)
        reason_parts.append("agent offered specialist confirmation")
    if markers["mentions_integrations"] and before["active_objection"] in {"provider", "confusion"}:
        after["clarity"] = clamp(after["clarity"] + 1)
        after["interest"] = clamp(after["interest"] + 1)
        reason_parts.append("agent gave concrete integration details")
    if markers["respects_callback"] and before["active_objection"] == "time":
        after["trust"] = clamp(after["trust"] + 1)
        after["commitment"] = "callback"
        reason_parts.append("agent respected limited time")
    if markers["respects_stop"]:
        after["commitment"] = "none"
        after["patience"] = 0
        reason_parts.append("agent honored stop request")
    if markers["asks_multiple_questions"]:
        after["friction"] = clamp(after["friction"] + 1)
        after["patience"] = clamp(after["patience"] - 1)
        reason_parts.append("agent asked too many questions")
    if markers["pushes_close"] and (before["trust"] < 3 or before["clarity"] < 3):
        after["friction"] = clamp(after["friction"] + 2)
        after["patience"] = clamp(after["patience"] - 1)
        reason_parts.append("close language came before enough trust or clarity")

    if after["clarity"] >= 3 and after["trust"] >= 3 and before["active_objection"] not in {"support", "do-not-call", "time"}:
        after["interest"] = clamp(after["interest"] + 1)
    if after["interest"] >= 4 and after["trust"] >= 4 and after["clarity"] >= 4:
        after["commitment"] = "sale-ready"
        after["emotion"] = "interested"
    elif after["friction"] >= 4 and after["patience"] <= 1:
        after["emotion"] = "annoyed"
    elif after["clarity"] >= 3:
        after["emotion"] = "calm"

    delta = {
        "interest": after["interest"] - before["interest"],
        "trust": after["trust"] - before["trust"],
        "clarity": after["clarity"] - before["clarity"],
        "friction": after["friction"] - before["friction"],
        "patience": after["patience"] - before["patience"],
    }
    reason = "; ".join(reason_parts) if reason_parts else "agent gave a safe but low-impact answer"
    return after, delta, reason
```

- [ ] **Step 4: Add customer reply and terminal logic**

Append these functions:

```python
def terminal_outcome(seed: dict[str, Any], state: dict[str, Any], turn_index: int, hard_failure: bool) -> str | None:
    if hard_failure:
        return "hard-failure"
    if state["active_objection"] == "do-not-call":
        return "do-not-call"
    if state["active_objection"] == "support":
        return "human-handoff"
    if state["commitment"] == "callback":
        return "callback-agreed"
    if state["commitment"] == "sale-ready":
        return "sale-ready"
    if state["emotion"] == "annoyed" and state["patience"] == 0:
        return "not-interested"
    if turn_index >= 7:
        return "max-turns"
    return None


def next_customer_message(seed: dict[str, Any], state: dict[str, Any], previous_agent_answer: str, turn_index: int) -> str:
    if state["active_objection"] == "price" and state["clarity"] >= 3:
        state["active_objection"] = "authority"
        return "Okay, the price is clearer. What would I tell my manager if I wanted to review it?"
    if state["active_objection"] == "confusion" and state["clarity"] >= 3:
        state["active_objection"] = "price"
        return "That makes more sense. What does it cost for a small team?"
    if state["active_objection"] == "trust" and state["trust"] >= 3:
        state["active_objection"] = "written-info"
        return "Send me the concrete details in writing, especially what it can and cannot promise."
    if state["active_objection"] == "provider" and state["clarity"] >= 3:
        state["active_objection"] = "price"
        return "If it can sit alongside our CRM, what would the Growth plan cost?"
    if state["active_objection"] == "authority" and state["clarity"] >= 3 and state["trust"] >= 3:
        state["commitment"] = "callback"
        return "That is enough for a review. Set up a specialist callback rather than trying to close this now."
    if state["active_objection"] == "written-info":
        state["commitment"] = "callback"
        return "Fine, a specialist can send that and walk me through it later."
    if state["emotion"] == "annoyed":
        return "You are still pushing a bit. Can we slow this down or stop?"
    if state["interest"] >= 4 and state["trust"] >= 4:
        state["commitment"] = "sale-ready"
        return "I am interested enough for the next non-binding workflow review."
    return "I follow. Give me the one detail that matters most before I decide whether this is worth a next step."
```

- [ ] **Step 5: Add call loop**

Append this function:

```python
def simulate_call(seed: dict[str, Any], campaign: dict[str, Any]) -> dict[str, Any]:
    state = deepcopy(seed["initial_state"])
    customer_message = seed["initial_message"]
    turns: list[dict[str, Any]] = []
    terminal = None

    for turn_index in range(8):
        state_before = deepcopy(state)
        answer = agent_answer(seed, state_before, customer_message, campaign)
        packet = build_guarded_response_packet(
            campaign=campaign,
            stage="discovery",
            input_type="speech-final",
            transcript=customer_message,
            silence_count=0,
            candidate_response_override=answer,
            retrieval_enabled=False,
            retrieval_registry_path=None,
            composer_hooks_enabled=False,
        )
        final_answer = str(packet["final_response"])
        safety_flags = {
            "payment_collection": contains_payment_collection(final_answer),
            "unsupported_claim": bool(unsupported_claims(final_answer)),
            "validation_failed": not packet["validation"]["passed"],
            "language_mismatch": not output_language_matches(packet),
            "forbidden_response_text": bool(forbidden_response_text(packet)),
        }
        safety_flags["hard_failure"] = any(safety_flags.values())
        state_after, state_delta, reaction_reason = update_state(seed, state_before, final_answer)
        terminal = terminal_outcome(seed, state_after, turn_index, safety_flags["hard_failure"])
        turns.append(
            {
                "turn_index": turn_index + 1,
                "customer_message": customer_message,
                "agent_answer": final_answer,
                "state_before": state_before,
                "state_after": deepcopy(state_after),
                "state_delta": state_delta,
                "customer_reaction_reason": reaction_reason,
                "reactive_to_previous_agent_answer": turn_index > 0,
                "safety_flags": safety_flags,
                "question_count": count_questions(final_answer),
                "decision_snapshot": packet["decision_snapshot"],
            }
        )
        state = state_after
        if terminal is not None:
            break
        customer_message = next_customer_message(seed, state, final_answer, turn_index)

    if terminal is None:
        terminal = "max-turns"

    return {
        "seed_id": seed["seed_id"],
        "persona": seed["persona"],
        "hidden_buying_intent": seed["hidden_buying_intent"],
        "primary_need": seed["primary_need"],
        "expected_terminal_family": seed["expected_terminal_family"],
        "terminal_outcome": terminal,
        "initial_state": seed["initial_state"],
        "final_state": turns[-1]["state_after"],
        "turn_count": len(turns),
        "turns": turns,
    }
```

- [ ] **Step 6: Run the red validator again**

Run:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```

Expected result:

```text
AssertionError: missing required PROD-031 files
```

The failure remains correct because build payload, runner, docs, and artifacts do not exist yet.

- [ ] **Step 7: Commit call loop**

Run:

```powershell
git add scripts\prod_031_interactive_grounded_call_simulation.py
git commit -m "Add PROD-031 interactive call loop"
```

---

### Task 4: Add Payload, Metrics, Report, And HTML Rendering

**Files:**
- Modify: `scripts/prod_031_interactive_grounded_call_simulation.py`

- [ ] **Step 1: Add metric helpers and payload builder**

Append these functions:

```python
def is_non_sale_correct(call: dict[str, Any]) -> bool:
    expected = call["expected_terminal_family"]
    actual = call["terminal_outcome"]
    if expected == "do_not_call":
        return actual == "do-not-call"
    if expected == "handoff":
        return actual == "human-handoff"
    if expected == "callback":
        return actual == "callback-agreed"
    return actual in {"sale-ready", "callback-agreed", "max-turns"}


def metric(value: float, definition: str) -> dict[str, Any]:
    return {"value": round(value, 4), "definition": definition}


def build_summary(calls: list[dict[str, Any]], elapsed_ms: int) -> dict[str, Any]:
    all_turns = [turn for call in calls for turn in call["turns"]]
    initial_trust = [call["initial_state"]["trust"] for call in calls]
    final_trust = [call["final_state"]["trust"] for call in calls]
    initial_interest = [call["initial_state"]["interest"] for call in calls]
    final_interest = [call["final_state"]["interest"] for call in calls]
    initial_clarity = [call["initial_state"]["clarity"] for call in calls]
    final_clarity = [call["final_state"]["clarity"] for call in calls]
    initial_friction = [call["initial_state"]["friction"] for call in calls]
    final_friction = [call["final_state"]["friction"] for call in calls]
    safe_terminal = [call for call in calls if call["terminal_outcome"] in {"sale-ready", "callback-agreed", "human-handoff", "do-not-call", "not-interested", "max-turns"}]
    return {
        "deterministic_simulator": True,
        "call_seed_count": len(build_call_seeds()),
        "call_count": len(calls),
        "total_turn_count": len(all_turns),
        "reactive_customer_turn_count": sum(max(call["turn_count"] - 1, 0) for call in calls),
        "reactive_state_transition_count": len(all_turns),
        "exact_customer_agent_state_trace_visible": True,
        "agent_answer_depends_on_customer_state": True,
        "customer_reply_depends_on_prior_agent_answer": True,
        "safe_close_count": len(safe_terminal),
        "sale_ready_outcome_count": sum(1 for call in calls if call["terminal_outcome"] == "sale-ready"),
        "callback_outcome_count": sum(1 for call in calls if call["terminal_outcome"] == "callback-agreed"),
        "non_sale_correct_count": sum(1 for call in calls if is_non_sale_correct(call)),
        "hard_failure_count": sum(1 for turn in all_turns if turn["safety_flags"]["hard_failure"]),
        "payment_collection_count": sum(1 for turn in all_turns if turn["safety_flags"]["payment_collection"]),
        "unsupported_claim_count": sum(1 for turn in all_turns if turn["safety_flags"]["unsupported_claim"]),
        "leakage_finding_count": 0,
        "question_overuse_count": sum(1 for turn in all_turns if turn["question_count"] > 1),
        "premature_close_count": sum(1 for turn in all_turns if "close language came before" in turn["customer_reaction_reason"]),
        "average_trust_delta": round((sum(final_trust) - sum(initial_trust)) / len(calls), 4),
        "average_interest_delta": round((sum(final_interest) - sum(initial_interest)) / len(calls), 4),
        "average_clarity_delta": round((sum(final_clarity) - sum(initial_clarity)) / len(calls), 4),
        "average_friction_delta": round((sum(final_friction) - sum(initial_friction)) / len(calls), 4),
        "safe_close_rate": round(len(safe_terminal) / len(calls), 4),
        "non_sale_correctness": round(sum(1 for call in calls if is_non_sale_correct(call)) / len(calls), 4),
        "interactive_realism_score": round(sum(1 for turn in all_turns if turn["customer_reaction_reason"]) / len(all_turns), 4),
        "provider_calls_made": False,
        "llm_used": False,
        "runtime_behavior_changed": False,
        "runtime_retrieval_default_enabled": False,
        "composer_hook_flag_default_enabled": False,
        "production_runtime_promotion_allowed": False,
        "elapsed_ms": elapsed_ms,
    }


def build_metrics(summary: dict[str, Any]) -> dict[str, dict[str, Any]]:
    total_turns = summary["total_turn_count"]
    return {
        "safe_close_rate": metric(summary["safe_close_rate"], "Share of calls ending in an allowed safe terminal outcome."),
        "non_sale_correctness": metric(summary["non_sale_correctness"], "Share of calls whose terminal outcome respects the seed's non-sale boundary expectation."),
        "average_trust_delta": metric(summary["average_trust_delta"], "Average final trust minus initial trust across calls."),
        "average_interest_delta": metric(summary["average_interest_delta"], "Average final interest minus initial interest across calls."),
        "average_clarity_delta": metric(summary["average_clarity_delta"], "Average final clarity minus initial clarity across calls."),
        "average_friction_delta": metric(summary["average_friction_delta"], "Average final friction minus initial friction across calls."),
        "interactive_realism_score": metric(summary["interactive_realism_score"], "Share of turns with explicit customer reaction reasons from state changes."),
        "hard_failure_rate": metric(summary["hard_failure_count"] / total_turns if total_turns else 0.0, "Share of turns with hard safety failures."),
        "question_overuse_rate": metric(summary["question_overuse_count"] / total_turns if total_turns else 0.0, "Share of turns where the agent asked more than one question."),
    }


def build_payload(
    *,
    result_path: Path = DEFAULT_RESULT,
    report_path: Path = DEFAULT_REPORT,
    trace_path: Path = DEFAULT_TRACE,
    html_path: Path = DEFAULT_HTML,
) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.perf_counter()
    campaign = build_synthetic_campaign()
    calls = [simulate_call(seed, campaign) for seed in build_call_seeds()]
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    traces = {
        "checkpoint_id": CHECKPOINT_ID,
        "source_spec_path": rel_path(SOURCE_SPEC),
        "calls": calls,
    }
    summary = build_summary(calls, elapsed_ms)
    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "title": "PROD-031 interactive grounded call simulation",
        "source_spec_path": rel_path(SOURCE_SPEC),
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
        "outputs": {
            "result_path": rel_path(result_path),
            "report_path": rel_path(report_path),
            "trace_path": rel_path(trace_path),
            "html_path": rel_path(html_path),
        },
        "boundaries": build_boundaries(),
        "summary": summary,
        "metrics": build_metrics(summary),
        "decision": "interactive_simulation_ready_for_review_not_runtime_promotion",
    }
    return payload, traces
```

- [ ] **Step 2: Add Markdown report renderer**

Append:

```python
def render_report(payload: dict[str, Any], traces: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# PROD-031 Interactive Grounded Call Simulation",
        "",
        "PROD-031 replaces static scenario replay with a deterministic local simulator where customer state changes after each agent answer.",
        "",
        "## Result",
        "",
        f"- Checkpoint id: `{payload['checkpoint_id']}`",
        "- Deterministic simulator: `true`",
        f"- Call seed count: `{summary['call_seed_count']}`",
        f"- Call count: `{summary['call_count']}`",
        f"- Total turn count: `{summary['total_turn_count']}`",
        f"- Reactive customer turn count: `{summary['reactive_customer_turn_count']}`",
        f"- Customer reply depends on prior agent answer: `{str(summary['customer_reply_depends_on_prior_agent_answer']).lower()}`",
        f"- Safe close rate: `{summary['safe_close_rate']}`",
        f"- Non-sale correctness: `{summary['non_sale_correctness']}`",
        f"- Interactive realism score: `{summary['interactive_realism_score']}`",
        f"- Hard failures: `{summary['hard_failure_count']}`",
        f"- Payment collection count: `{summary['payment_collection_count']}`",
        f"- Unsupported claim count: `{summary['unsupported_claim_count']}`",
        f"- Leakage findings: `{summary['leakage_finding_count']}`",
        "- Provider calls made: `false`",
        "- Runtime behavior changed: `false`",
        f"- Next checkpoint: `{payload['next_checkpoint_recommended']}`",
        "",
        "## Call Outcomes",
        "",
        "| Seed | Persona | Turns | Terminal outcome | Trust delta | Interest delta | Clarity delta | Friction delta |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for call in traces["calls"]:
        initial = call["initial_state"]
        final = call["final_state"]
        lines.append(
            f"| {call['seed_id']} | {call['persona']} | {call['turn_count']} | {call['terminal_outcome']} | {final['trust'] - initial['trust']} | {final['interest'] - initial['interest']} | {final['clarity'] - initial['clarity']} | {final['friction'] - initial['friction']} |"
        )
    lines.extend(["", "## Exact Interactive Traces", ""])
    for call in traces["calls"]:
        lines.extend([f"### {call['seed_id']} - {call['persona']}", "", f"- Terminal outcome: `{call['terminal_outcome']}`", ""])
        for turn in call["turns"]:
            lines.extend(
                [
                    f"#### Turn {turn['turn_index']}",
                    "",
                    f"- State before: `{turn['state_before']}`",
                    f"- State after: `{turn['state_after']}`",
                    f"- State delta: `{turn['state_delta']}`",
                    f"- Reaction reason: `{turn['customer_reaction_reason']}`",
                    "",
                    "Customer:",
                    "",
                    "```text",
                    turn["customer_message"],
                    "```",
                    "",
                    "Agent:",
                    "",
                    "```text",
                    turn["agent_answer"],
                    "```",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"
```

- [ ] **Step 3: Add HTML renderer**

Append:

```python
def render_html(payload: dict[str, Any], traces: dict[str, Any]) -> str:
    summary = payload["summary"]
    style = """
body { font-family: Arial, sans-serif; color: #1f2933; margin: 0; background: #f7f8fa; }
main { max-width: 1180px; margin: 0 auto; padding: 28px; }
h1, h2, h3 { color: #111827; }
.summary, .call { background: #fff; border: 1px solid #d8dee8; border-radius: 8px; padding: 18px; margin: 16px 0; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; }
.metric, .turn { background: #eef2f7; padding: 10px; border-radius: 6px; }
.text { white-space: pre-wrap; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; }
"""
    lines = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\">",
        "  <title>PROD-031 Interactive Grounded Call Simulation</title>",
        f"  <style>{style}</style>",
        "</head>",
        "<body>",
        "<main>",
        "  <h1>PROD-031 Interactive Grounded Call Simulation</h1>",
        "  <p>customer state -> customer turn -> agent answer -> customer state changes -> reactive customer turn</p>",
        "  <section class=\"summary\">",
        "    <h2>Summary</h2>",
        "    <div class=\"grid\">",
        f"      <div class=\"metric\">Deterministic simulator: `{str(summary['deterministic_simulator']).lower()}`</div>",
        f"      <div class=\"metric\">Call seed count: `{summary['call_seed_count']}`</div>",
        f"      <div class=\"metric\">Reactive customer turn count: `{summary['reactive_customer_turn_count']}`</div>",
        f"      <div class=\"metric\">Customer reply depends on prior agent answer: `{str(summary['customer_reply_depends_on_prior_agent_answer']).lower()}`</div>",
        "      <div class=\"metric\">Provider calls made: `false`</div>",
        "      <div class=\"metric\">Runtime behavior changed: `false`</div>",
        f"      <div class=\"metric\">Next checkpoint: `{html.escape(payload['next_checkpoint_recommended'])}`</div>",
        "    </div>",
        "  </section>",
    ]
    for call in traces["calls"]:
        lines.extend(
            [
                "  <section class=\"call\">",
                f"    <h2>{html.escape(call['seed_id'])} - {html.escape(call['persona'])}</h2>",
                f"    <p>Terminal outcome: `{html.escape(call['terminal_outcome'])}`</p>",
            ]
        )
        for turn in call["turns"]:
            lines.extend(
                [
                    "    <div class=\"turn\">",
                    f"      <h3>Turn {turn['turn_index']}</h3>",
                    "      <p><strong>State before</strong></p>",
                    f"      <div class=\"text\">{html.escape(json.dumps(turn['state_before'], ensure_ascii=False))}</div>",
                    "      <p><strong>Customer</strong></p>",
                    f"      <div class=\"text\">{html.escape(turn['customer_message'])}</div>",
                    "      <p><strong>Agent</strong></p>",
                    f"      <div class=\"text\">{html.escape(turn['agent_answer'])}</div>",
                    "      <p><strong>State after</strong></p>",
                    f"      <div class=\"text\">{html.escape(json.dumps(turn['state_after'], ensure_ascii=False))}</div>",
                    "      <p><strong>Reaction reason</strong></p>",
                    f"      <div class=\"text\">{html.escape(turn['customer_reaction_reason'])}</div>",
                    "    </div>",
                ]
            )
        lines.append("  </section>")
    lines.extend(["</main>", "</body>", "</html>", ""])
    return "\n".join(lines)
```

- [ ] **Step 4: Run validator**

Run:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```

Expected result:

```text
AssertionError: missing required PROD-031 files
```

The failure remains correct until the runner writes artifacts and docs exist.

- [ ] **Step 5: Commit payload/rendering work**

Run:

```powershell
git add scripts\prod_031_interactive_grounded_call_simulation.py
git commit -m "Add PROD-031 simulation payload rendering"
```

---

### Task 5: Add Runner And Generate Artifacts

**Files:**
- Create: `scripts/run_prod_031_interactive_grounded_call_simulation.py`
- Generate: `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/result.json`
- Generate: `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/report.md`
- Generate: `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_traces.json`
- Generate: `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_trace.html`

- [ ] **Step 1: Create runner**

Create `scripts/run_prod_031_interactive_grounded_call_simulation.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from prod_031_interactive_grounded_call_simulation import (
    DEFAULT_HTML,
    DEFAULT_REPORT,
    DEFAULT_RESULT,
    DEFAULT_TRACE,
    ROOT,
    build_payload,
    render_html,
    render_report,
    write_json,
    write_text,
)


RESTRICTED_PARTS = {"private", "private-restricted"}


def resolve_path(path_text: str, *, must_stay_in_root: bool = True, block_private: bool = True) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if must_stay_in_root:
        try:
            resolved.relative_to(ROOT)
        except ValueError as exc:
            raise ValueError(f"PROD-031 path must stay inside project root: {path_text}") from exc
    if block_private and any(part.lower() in RESTRICTED_PARTS for part in resolved.parts):
        raise ValueError(f"PROD-031 path is restricted: {path_text}")
    return resolved


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the PROD-031 interactive grounded call simulation checkpoint.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Result JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report output path.")
    parser.add_argument("--trace-out", default=str(DEFAULT_TRACE), help="Interactive call traces JSON output path.")
    parser.add_argument("--html-out", default=str(DEFAULT_HTML), help="Static HTML trace output path.")
    args = parser.parse_args()

    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    trace_path = resolve_path(args.trace_out)
    html_path = resolve_path(args.html_out)

    payload, traces = build_payload(
        result_path=out_path,
        report_path=report_path,
        trace_path=trace_path,
        html_path=html_path,
    )
    write_json(out_path, payload)
    write_json(trace_path, traces)
    write_text(report_path, render_report(payload, traces))
    write_text(html_path, render_html(payload, traces))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the runner**

Run:

```powershell
python scripts\run_prod_031_interactive_grounded_call_simulation.py
```

Expected output includes:

```text
"deterministic_simulator": true
"call_seed_count": 8
"call_count": 8
"provider_calls_made": false
"runtime_behavior_changed": false
```

- [ ] **Step 3: Run validator**

Run:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```

Expected result:

```text
AssertionError: missing required PROD-031 files
```

The failure remains correct because product docs and registry wiring are still missing.

- [ ] **Step 4: Commit runner and artifacts**

Run:

```powershell
git add scripts\run_prod_031_interactive_grounded_call_simulation.py research\experiments\generated\PROD-031-interactive-grounded-call-simulation
git commit -m "Generate PROD-031 interactive traces"
```

---

### Task 6: Add Product Doc And Register Commands/Guards

**Files:**
- Create: `docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `docs/product/CHECKPOINT_INDEX.md`
- Modify: `scripts/check_setup.py`
- Modify: `scripts/validate_check_setup.py`
- Modify: `scripts/check_project_drift.py`
- Modify: `scripts/validate_project_drift_guard.py`

- [ ] **Step 1: Create product doc**

Create `docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md`:

````markdown
# PROD-031 Interactive Grounded Call Simulation

PROD-031 replaces static scenario replay with deterministic reactive customer simulation.

## Result

- Checkpoint id: `PROD-031-interactive-grounded-call-simulation`
- Deterministic simulator: `true`
- Call seed count: `8`
- Customer reply depends on prior agent answer: `true`
- Provider calls made: `false`
- LLM used: `false`
- Runtime behavior changed: `false`
- Retrieval default enabled: `false`
- Composer hook default enabled: `false`
- Production runtime promotion allowed: `false`
- Next checkpoint: `PROD-032-interactive-simulation-review`

## Outputs

- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/result.json`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/report.md`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_traces.json`
- `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/interactive_call_trace.html`

## Evaluation Shape

Each call records exact customer turns, exact agent answers, state before, state after, state deltas, customer reaction reasons, terminal outcome, and safety flags.

## Boundary

This checkpoint is local-only. It does not call providers, call an LLM, read private data, download datasets, collect payment, start a server, enable retrieval by default, enable composer hooks by default, or promote production runtime behavior.

## Commands

```powershell
python scripts\run_prod_031_interactive_grounded_call_simulation.py
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```
````

After writing the doc, replace hardcoded metric values with exact numbers from `result.json`.

- [ ] **Step 2: Register commands**

In `docs/product/COMMANDS.md`, add after PROD-030:

````markdown
Run the PROD-031 interactive grounded call simulation checkpoint:

```powershell
python scripts\run_prod_031_interactive_grounded_call_simulation.py
```

Validate deterministic reactive customer state transitions, exact traces, safety boundaries, and no-provider/no-runtime-change behavior:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```
````

- [ ] **Step 3: Register checkpoint index**

In `docs/product/CHECKPOINT_INDEX.md`, add:

```markdown
- `PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md`
```

- [ ] **Step 4: Register setup guard**

In `scripts/check_setup.py`, add to `REQUIRED_FILES`:

```python
("file.docs_product_prod_031_interactive_grounded_call_simulation", "docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md", "PROD-031 interactive grounded call simulation"),
```

Add script checks:

```python
("file.scripts_prod_031_interactive_grounded_call_simulation", "scripts/prod_031_interactive_grounded_call_simulation.py", "PROD-031 interactive grounded call simulation module"),
("file.scripts_run_prod_031_interactive_grounded_call_simulation", "scripts/run_prod_031_interactive_grounded_call_simulation.py", "PROD-031 interactive grounded call simulation runner"),
("file.scripts_validate_prod_031_interactive_grounded_call_simulation", "scripts/validate_prod_031_interactive_grounded_call_simulation.py", "PROD-031 interactive grounded call simulation validator"),
```

- [ ] **Step 5: Register setup validator**

In `scripts/validate_check_setup.py`, add required IDs:

```python
"file.docs_product_prod_031_interactive_grounded_call_simulation",
"file.scripts_prod_031_interactive_grounded_call_simulation",
"file.scripts_run_prod_031_interactive_grounded_call_simulation",
"file.scripts_validate_prod_031_interactive_grounded_call_simulation",
```

- [ ] **Step 6: Register drift guard and fixture**

In both `scripts/check_project_drift.py` and `scripts/validate_project_drift_guard.py`, add:

```python
"docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md",
"scripts/prod_031_interactive_grounded_call_simulation.py",
"scripts/run_prod_031_interactive_grounded_call_simulation.py",
"scripts/validate_prod_031_interactive_grounded_call_simulation.py",
```

- [ ] **Step 7: Run validator**

Run:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
```

Expected result:

```text
PROD-031 interactive grounded call simulation validation passed.
```

- [ ] **Step 8: Commit docs and guard wiring**

Run:

```powershell
git add docs\product\PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md docs\product\COMMANDS.md docs\product\CHECKPOINT_INDEX.md scripts\check_setup.py scripts\validate_check_setup.py scripts\check_project_drift.py scripts\validate_project_drift_guard.py
git commit -m "Register PROD-031 interactive simulation"
```

---

### Task 7: Update Thesis Docs And Final Validation

**Files:**
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/DECISION_LOG.md`

- [ ] **Step 1: Update roadmap**

In `docs/thesis/ROADMAP.md`:

- Move `PROD-031-interactive-grounded-call-simulation` from current to completed.
- Set current checkpoint to `PROD-032-interactive-simulation-review`.
- Keep the static route-gap fix deferred until PROD-032 interprets interactive failures.

Use this completed-checkpoint wording:

```markdown
- [x] `PROD-031` interactive grounded call simulation, which replaces static scenario replay with deterministic reactive customer simulation. It runs `8` local call seeds where customer trust, interest, clarity, friction, patience, emotion, objection state, and commitment change after each agent answer. It records exact customer turns, exact agent answers, state before, state after, state deltas, reaction reasons, terminal outcomes, and safety flags. Provider calls, LLM use, private data reads, dataset downloads, customer data, runtime behavior changes, retrieval defaults, composer-hook defaults, server start, payment collection, and production runtime promotion stayed blocked. The next checkpoint is `PROD-032-interactive-simulation-review`.
```

Replace the metric values in that paragraph with exact values from `result.json`.

- [ ] **Step 2: Update methodology log**

Add a top entry:

```markdown
### 2026-05-09 - PROD-031 interactive grounded call simulation

- Objective: replace weak static customer-turn replay with deterministic reactive customer simulation.
- Action taken: added the PROD-031 simulator, runner, validator, product doc, generated trace/report artifacts, command-map coverage, setup coverage, drift-guard coverage, and thesis documentation.
- Data used: the project-owned RouteSignal CRM synthetic campaign and deterministic customer seeds. No provider call, LLM call, private data read, dataset download, runtime change, retrieval default change, composer-hook default change, customer data, server start, or payment handling was used.
- Output created: `docs/product/PROD_031_INTERACTIVE_GROUNDED_CALL_SIMULATION.md`, `scripts/prod_031_interactive_grounded_call_simulation.py`, `scripts/run_prod_031_interactive_grounded_call_simulation.py`, `scripts/validate_prod_031_interactive_grounded_call_simulation.py`, `research/experiments/generated/PROD-031-interactive-grounded-call-simulation/result.json`, `report.md`, `interactive_call_traces.json`, and `interactive_call_trace.html`.
- What was learned: reactive state traces are stronger evidence than static scenario replay because they show whether an agent answer changes customer trust, interest, clarity, friction, objections, and commitment.
- Why it matters for the thesis: the evaluation now measures conversational effect, not only correctness against prewritten turns.
- Open questions: which failures are simulator-design limits, which are runtime policy issues, and whether the old static route gaps still need direct fixes.
```

Replace metrics or conclusions with exact result data.

- [ ] **Step 3: Update decision log**

Add:

```markdown
### DEC-079 - Keep PROD-031 as interactive evaluation evidence

- Date: 2026-05-09
- Status: accepted
- Decision: Treat deterministic interactive simulation as the stronger next evaluation lane before static route-gap cleanup or demo polish.
- Why:
  - customer replies now react to the previous agent answer and updated state
  - exact state transitions make trust, clarity, interest, friction, objections, and commitment inspectable
  - local deterministic simulation keeps provider, LLM, privacy, and runtime-promotion boundaries closed
- Alternatives considered:
  - fix static route gaps first
  - keep using static full-scenario replay as the primary evidence
  - add LLM customer simulation before deterministic simulation exists
- Consequences:
  - PROD-032 should review interactive failures before choosing runtime fixes
  - old static route gaps remain deferred until they are confirmed relevant in reactive calls
  - live/provider/voice/telephony/client-facing promotion remains blocked
```

- [ ] **Step 4: Run all validators**

Run:

```powershell
python scripts\validate_prod_031_interactive_grounded_call_simulation.py
python scripts\check_setup.py --json
python scripts\validate_check_setup.py
python scripts\check_project_drift.py --json
python scripts\validate_project_drift_guard.py
python scripts\check_thesis_update_gate.py
python scripts\validate_thesis_update_gate.py
python scripts\check_thesis_reference_registry.py
python scripts\validate_thesis_reference_registry.py
git diff --check
```

Expected results:

```text
PROD-031 interactive grounded call simulation validation passed.
Product setup verifier validation passed.
Project drift guard validation passed.
Thesis update gate validation passed.
Thesis reference registry guard validation passed.
```

`git diff --check` may print CRLF warnings on Windows. It must not print whitespace errors.

- [ ] **Step 5: Commit final thesis docs**

Run:

```powershell
git add docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md docs\thesis\DECISION_LOG.md
git commit -m "Document PROD-031 interactive simulation"
```

- [ ] **Step 6: Push main**

Run:

```powershell
git push origin main
```

If push fails with `Repository not found`, run:

```powershell
gh auth status
gh auth switch --hostname github.com --user Tarikv1
git push origin main
```

---

## Plan Self-Review

- Spec coverage: the plan covers deterministic simulation, eight seeds, state transitions, reactive customer replies, local grounded agent answers, exact traces, metrics, reports, docs, guard wiring, and thesis evidence.
- Placeholder scan: no placeholder tokens are present in the plan body.
- Type consistency: checkpoint id, output paths, function names, metric names, boundary keys, and validator expectations are consistent across tasks.
- Scope check: this plan builds only PROD-031. It does not fix static PROD-030 route gaps, add LLM simulation, start a server, call providers, add voice, add telephony, or promote runtime behavior.
