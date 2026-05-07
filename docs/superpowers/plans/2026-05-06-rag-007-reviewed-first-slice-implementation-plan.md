# RAG-007 Reviewed First Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `RAG-007`, a local reviewed-first-slice gate that promotes a small paraphrased, source-tracked sales knowledge slice without enabling runtime retrieval.

**Architecture:** Add a focused Python builder that reads the RAG-006 review packet, RAG-005 chunk result, and RAG-004 source manifest, then emits `result.json` and `report.md` for the approved response-wording and voice-delivery slice. Add a runner, validator, case metadata, product docs, command-map entries, setup registration, and thesis checkpoint updates.

**Tech Stack:** Python standard library, JSON, Markdown, existing RAG-004/RAG-005/RAG-006 generated artifacts.

---

### File Structure

- Create: `scripts/rag_reviewed_first_slice.py`
  - Owns selected RAG-007 knowledge rules, source/chunk lookup, first-slice payload creation, report rendering, and safety-boundary metadata.
- Create: `scripts/run_rag_007_reviewed_first_slice.py`
  - CLI wrapper that writes official JSON and Markdown artifacts under `research/experiments/generated/RAG-007-reviewed-first-slice/`.
- Create: `scripts/validate_rag_007_reviewed_first_slice.py`
  - Offline validator with fixture coverage and generated-artifact checks.
- Create: `research/experiments/cases/rag-007-reviewed-first-slice.json`
  - Small case metadata file for setup and thesis traceability.
- Create: `docs/product/RAG_007_REVIEWED_FIRST_SLICE.md`
  - Product-facing checkpoint doc.
- Modify: `docs/product/COMMANDS.md`
  - Add run and validation commands after RAG-006.
- Modify: `scripts/check_setup.py`
  - Register RAG-007 doc, module, runner, validator, and case file as required project-local assets.
- Modify: `docs/thesis/ROADMAP.md`
  - Mark RAG-007 current/completed after generation and set the next RAG checkpoint to guarded retrieval-policy design.
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
  - Record inputs, outputs, counts, safety boundaries, and lessons.
- Generated: `research/experiments/generated/RAG-007-reviewed-first-slice/result.json`
- Generated: `research/experiments/generated/RAG-007-reviewed-first-slice/report.md`

### Task 1: Validator First

**Files:**
- Create: `scripts/validate_rag_007_reviewed_first_slice.py`

- [ ] **Step 1: Write the failing validator**

Create `scripts/validate_rag_007_reviewed_first_slice.py` with this structure:

```python
#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "rag_reviewed_first_slice.py"
RUNNER = ROOT / "scripts" / "run_rag_007_reviewed_first_slice.py"
CASE_PATH = ROOT / "research" / "experiments" / "cases" / "rag-007-reviewed-first-slice.json"
DOC_PATH = ROOT / "docs" / "product" / "RAG_007_REVIEWED_FIRST_SLICE.md"
TMP_DIR = ROOT / ".tmp" / "rag-007-validation"
TMP_RAG006 = TMP_DIR / "rag006-result.json"
TMP_RAG005 = TMP_DIR / "rag005-result.json"
TMP_MANIFEST = TMP_DIR / "rag004-result.json"
RESULT_PATH = TMP_DIR / "result.json"
REPORT_PATH = TMP_DIR / "report.md"

EXPECTED_ID = "RAG-007-reviewed-first-slice"
EXPECTED_CHUNK_IDS = {
    "rag005-chunk-017",
    "rag005-chunk-020",
    "rag005-chunk-022",
    "rag005-chunk-024",
    "rag005-chunk-025",
    "rag005-chunk-091",
    "rag005-chunk-098",
    "rag005-chunk-099",
    "rag005-chunk-101",
}
PRESSURE_CHUNK_IDS = {
    "rag005-chunk-071",
    "rag005-chunk-075",
    "rag005-chunk-076",
    "rag005-chunk-077",
    "rag005-chunk-087",
}


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_inputs() -> None:
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_id": "RAG-004-source-manifest-normalization",
        "source_manifest": {
            "sources": [
                {
                    "source_id": "rag004-source-086",
                    "canonical_title": "The Only Video You Need To Fix Your Communication Skills",
                    "metadata_status": "needs_human_review",
                    "rights_status": "needs_review",
                },
                {
                    "source_id": "rag004-source-063",
                    "canonical_title": "Non-Verbal Communication | SkillsYouNeed",
                    "metadata_status": "needs_human_review",
                    "rights_status": "needs_review",
                },
            ]
        },
    }
    selected_chunks = [
        {
            "chunk_candidate_id": "rag005-chunk-017",
            "source_title": "The Only Video You Need To Fix Your Communication Skills",
            "source_ids": ["rag004-source-086"],
            "topic_ids": ["objection_handling"],
            "principle": "Yes, And over Yes, But",
            "application": "Acknowledge concern before moving to a useful next step.",
            "when_not_to_use": "Correct factual or compliance errors directly.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
        {
            "chunk_candidate_id": "rag005-chunk-020",
            "source_title": "9 Habits for Clearer Speaking",
            "source_ids": ["rag004-source-016"],
            "topic_ids": ["ethical_persuasion_persuasive_dialogue"],
            "principle": "Declarative Statements vs. Rambling",
            "application": "Use short statements when clarity matters.",
            "when_not_to_use": "Do not sound robotic or curt.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
        {
            "chunk_candidate_id": "rag005-chunk-022",
            "source_title": "10 Speaking Techniques That Made Me A Top 1% Speaker",
            "source_ids": ["rag004-source-002"],
            "topic_ids": ["active_listening_human_like_sales_communication"],
            "principle": "The Empathy Echo",
            "application": "Reflect a key concern sparingly.",
            "when_not_to_use": "Do not repeat profanity or use mechanically.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
        {
            "chunk_candidate_id": "rag005-chunk-024",
            "source_title": "7 Communication Cheat Codes To Speak Like A Pro!",
            "source_ids": ["rag004-source-013"],
            "topic_ids": ["ethical_persuasion_persuasive_dialogue"],
            "principle": "The PREP Framework",
            "application": "Structure medium-length persuasive explanations.",
            "when_not_to_use": "Do not use for simple yes/no answers.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
        {
            "chunk_candidate_id": "rag005-chunk-025",
            "source_title": "Communication Is Hard Until You Structure Your Thinking First!",
            "source_ids": ["rag004-source-032"],
            "topic_ids": ["objection_handling"],
            "principle": "The 3-2-1 Framework",
            "application": "Constrain broad answers into a small structure.",
            "when_not_to_use": "Do not use when the customer asked for one direct fact.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
        {
            "chunk_candidate_id": "rag005-chunk-091",
            "source_title": "Think Fast, Talk Smart: Communication Techniques",
            "source_ids": ["rag004-source-087"],
            "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
            "principle": "Yes, and delivery posture",
            "application": "Sound constructive rather than defensive.",
            "when_not_to_use": "Do not sound agreeable while correcting a false claim.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
        {
            "chunk_candidate_id": "rag005-chunk-098",
            "source_title": "Non-Verbal Communication | SkillsYouNeed",
            "source_ids": ["rag004-source-063"],
            "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
            "principle": "Trust paralinguistics over words",
            "application": "Treat a tone mismatch as uncertainty.",
            "when_not_to_use": "Do not override explicit customer intent.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
        {
            "chunk_candidate_id": "rag005-chunk-099",
            "source_title": "The Impact of Tone of Voice on Users' Brand Perception",
            "source_ids": ["rag004-source-085"],
            "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
            "principle": "Trustworthiness over forced friendliness",
            "application": "Use straightforward, moderately warm delivery.",
            "when_not_to_use": "Avoid exaggerated cheer in serious contexts.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
        {
            "chunk_candidate_id": "rag005-chunk-101",
            "source_title": "How to Speak So That People Want to Listen",
            "source_ids": ["rag004-source-042"],
            "topic_ids": ["speech_tone_prosody_human_like_voice_behavior"],
            "principle": "Bounded vocal toolbox",
            "application": "Use controlled variation in pace, pitch, volume, warmth, and silence.",
            "when_not_to_use": "Do not imitate a source speaker.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
    ]
    pressure_chunks = [
        {
            "chunk_candidate_id": "rag005-chunk-075",
            "source_title": "Science Of Persuasion",
            "source_ids": ["rag004-source-075"],
            "topic_ids": ["ethical_persuasion_persuasive_dialogue"],
            "principle": "Scarcity & Loss Aversion",
            "application": "Highlight what the prospect loses by not acting.",
            "when_not_to_use": "Do not manufacture scarcity.",
            "source_excerpt_present": True,
            "source_excerpt_text_stored": False,
            "review_flags": ["quote_review_required"],
        },
    ]
    chunks = selected_chunks + pressure_chunks
    rag005 = {
        "normalization_id": "RAG-005-chunk-normalization",
        "summary": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
        },
        "chunk_candidates": chunks,
    }
    rag006 = {
        "review_packet_id": "RAG-006-chunk-review-packet",
        "rag005_result_path": "research/experiments/generated/RAG-005-chunk-normalization/result.json",
        "summary": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
        },
        "review_queues": {
            "quote_review_queue": [
                *[
                    {"chunk_id": chunk["chunk_candidate_id"], "review_flags": ["quote_review_required"]}
                    for chunk in selected_chunks
                ],
                {"chunk_id": "rag005-chunk-075", "review_flags": ["quote_review_required"]},
            ],
            "source_mapping_queue": [],
            "topic_mapping_queue": [],
        },
        "first_slice_candidates": [
            {"chunk_id": "rag005-chunk-017", "runtime_eligible_now": False}
        ],
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
        },
    }
    TMP_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    TMP_RAG005.write_text(json.dumps(rag005, indent=2), encoding="utf-8")
    TMP_RAG006.write_text(json.dumps(rag006, indent=2), encoding="utf-8")


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, timeout=60)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_module_contract() -> None:
    assert_condition(MODULE.exists(), "RAG-007 reviewed first slice module is missing.")
    sys.path.insert(0, str(ROOT / "scripts"))
    from rag_reviewed_first_slice import (  # noqa: PLC0415
        RAG_REVIEWED_FIRST_SLICE_ID,
        SELECTED_CHUNK_IDS,
        build_reviewed_first_slice,
        render_reviewed_first_slice_report,
    )

    assert_condition(RAG_REVIEWED_FIRST_SLICE_ID == EXPECTED_ID, RAG_REVIEWED_FIRST_SLICE_ID)
    assert_condition(set(SELECTED_CHUNK_IDS) == EXPECTED_CHUNK_IDS, SELECTED_CHUNK_IDS)
    write_fixture_inputs()
    payload = build_reviewed_first_slice(TMP_RAG006, TMP_RAG005, TMP_MANIFEST, root=ROOT)
    report = render_reviewed_first_slice_report(payload)
    text = json.dumps(payload, ensure_ascii=False)

    assert_condition(payload["reviewed_slice_id"] == EXPECTED_ID, payload)
    assert_condition(payload["summary"]["selected_chunk_count"] == len(EXPECTED_CHUNK_IDS), payload["summary"])
    assert_condition(payload["summary"]["knowledge_item_count"] == len(EXPECTED_CHUNK_IDS), payload["summary"])
    assert_condition(payload["summary"]["runtime_retrieval_enabled"] is False, payload["summary"])
    assert_condition(payload["summary"]["chunk_import_enabled"] is False, payload["summary"])
    assert_condition(payload["summary"]["auto_promoted_chunk_count"] == 0, payload["summary"])
    assert_condition(payload["summary"]["source_excerpt_text_stored"] is False, payload["summary"])
    assert_condition(payload["summary"]["private_customer_data_used"] is False, payload["summary"])
    assert_condition(payload["summary"]["external_provider_calls_made"] is False, payload["summary"])

    knowledge_ids = {item["source_chunk_ids"][0] for item in payload["knowledge_items"]}
    assert_condition(knowledge_ids == EXPECTED_CHUNK_IDS, knowledge_ids)
    assert_condition(not knowledge_ids.intersection(PRESSURE_CHUNK_IDS), knowledge_ids)
    assert_condition({item["lane"] for item in payload["knowledge_items"]} == {"response_wording", "voice_delivery"}, payload["knowledge_items"])
    assert_condition(all(item["runtime_eligible_now"] is False for item in payload["knowledge_items"]), payload["knowledge_items"])
    assert_condition(all(item["retrieval_eligible_now"] is False for item in payload["knowledge_items"]), payload["knowledge_items"])
    assert_condition(all(item["review_verdict"] == "manual_first_slice_paraphrased" for item in payload["knowledge_items"]), payload["knowledge_items"])
    assert_condition('"source_excerpt_text":' not in text, text)
    assert_condition("quote_review_required" not in text, text)
    assert_condition("data/private" not in text.replace("\\", "/"), text)
    assert_condition("insurance" not in text.lower(), text)

    tone_items = [item for item in payload["knowledge_items"] if "098" in item["source_chunk_ids"][0]]
    assert_condition(len(tone_items) == 1, tone_items)
    tone_text = json.dumps(tone_items[0], ensure_ascii=False).lower()
    assert_condition("uncertainty" in tone_text, tone_items[0])
    assert_condition("clarification" in tone_text or "clarify" in tone_text, tone_items[0])
    assert_condition("emotion certainty" not in tone_text, tone_items[0])
    assert_condition("override explicit" in tone_text, tone_items[0])
    assert_condition("Runtime retrieval remains disabled" in report, report)
    assert_condition("Response wording" in report, report)
    assert_condition("Voice delivery" in report, report)


def validate_runner_contract() -> None:
    assert_condition(RUNNER.exists(), "RAG-007 reviewed first slice runner is missing.")
    assert_condition(CASE_PATH.exists(), "RAG-007 case file is missing.")
    assert_condition(DOC_PATH.exists(), "RAG-007 product doc is missing.")
    write_fixture_inputs()
    completed = run_command(
        [
            sys.executable,
            str(RUNNER),
            "--rag006-packet",
            str(TMP_RAG006),
            "--rag005-result",
            str(TMP_RAG005),
            "--source-manifest",
            str(TMP_MANIFEST),
            "--out",
            str(RESULT_PATH),
            "--report-out",
            str(REPORT_PATH),
        ]
    )
    assert_condition(completed.returncode == 0, f"Runner failed. stdout={completed.stdout!r} stderr={completed.stderr!r}")
    assert_condition(RESULT_PATH.exists(), "RAG-007 JSON result was not created.")
    assert_condition(REPORT_PATH.exists(), "RAG-007 Markdown report was not created.")
    payload = load_json(RESULT_PATH)
    report = REPORT_PATH.read_text(encoding="utf-8")
    assert_condition(payload["summary"]["knowledge_item_count"] == len(EXPECTED_CHUNK_IDS), payload["summary"])
    assert_condition("rag005-chunk-098" in report, report)
    assert_condition("Runtime retrieval remains disabled" in report, report)


def main() -> None:
    validate_module_contract()
    validate_runner_contract()
    print("RAG-007 reviewed first slice validation passed.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run validator to verify RED**

Run:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
```

Expected:

```text
AssertionError: RAG-007 reviewed first slice module is missing.
```

- [ ] **Step 3: Commit validator**

Run:

```powershell
git add scripts\validate_rag_007_reviewed_first_slice.py
git commit -m "test: add RAG-007 reviewed slice validator"
```

### Task 2: Reviewed Slice Module

**Files:**
- Create: `scripts/rag_reviewed_first_slice.py`

- [ ] **Step 1: Add constants and selected paraphrased rules**

Create `scripts/rag_reviewed_first_slice.py` with these top-level constants:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


RAG_REVIEWED_FIRST_SLICE_ID = "RAG-007-reviewed-first-slice"

SELECTED_KNOWLEDGE_RULES: list[dict[str, Any]] = [
    {
        "knowledge_id": "rag007-response-yes-and-objection-framing",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-017"],
        "project_rule": "Acknowledge the customer's concern before moving to a useful next step; do not use agreement language to blur factual or compliance boundaries.",
        "safe_application": "Use when the customer raises a normal objection such as price, timing, complexity, or uncertainty and the agent can acknowledge the concern without validating a false claim.",
        "do_not_use_when": "Do not use when the customer states an incorrect fact, legal claim, medical claim, pricing detail, contract term, refusal, or do-not-call request; correct or honor that boundary directly.",
        "guardrail_notes": "Campaign facts, compliance language, refusal handling, human escalation, and do-not-call policy override this wording rule.",
    },
    {
        "knowledge_id": "rag007-response-declarative-clarity",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-020"],
        "project_rule": "Use short declarative statements when clarity matters, especially after an objection or broad question.",
        "safe_application": "Use to reduce rambling in explanations, next-step summaries, and concise value statements.",
        "do_not_use_when": "Do not make the agent sound clipped, robotic, dismissive, or aggressive; keep warmth and natural transitions.",
        "guardrail_notes": "This rule shapes freeform wording only and must not shorten required disclosures or campaign scripts.",
    },
    {
        "knowledge_id": "rag007-response-empathy-echo",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-022"],
        "project_rule": "Reflect a customer's key concern or emotional phrase sparingly before responding, so the reply shows listening without mechanical repetition.",
        "safe_application": "Use when the customer expresses frustration, confusion, hesitation, or a specific concern that should be acknowledged before the next question or explanation.",
        "do_not_use_when": "Do not repeat profanity, insults, private details, or the same phrase on every turn.",
        "guardrail_notes": "The echo is not an emotion diagnosis and must not override explicit customer intent.",
    },
    {
        "knowledge_id": "rag007-response-prep-structure",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-024"],
        "project_rule": "For a persuasive explanation, state the point, give the reason, add one concrete example, and return to the point.",
        "safe_application": "Use for medium-length answers where the customer needs a clear reason to continue or compare an option.",
        "do_not_use_when": "Do not use for simple yes/no answers, pleasantries, required compliance text, or urgent refusal handling.",
        "guardrail_notes": "Examples must be campaign-approved and truthful; the structure cannot invent claims or guarantees.",
    },
    {
        "knowledge_id": "rag007-response-3-2-1-structure",
        "lane": "response_wording",
        "source_chunk_ids": ["rag005-chunk-025"],
        "project_rule": "When an answer could sprawl, constrain it into a small numbered structure such as three points, two options, or one key takeaway.",
        "safe_application": "Use when the customer asks a broad or unexpected question and the agent needs a concise, organized response.",
        "do_not_use_when": "Do not use when the customer asked for one direct factual answer or when numbering would sound evasive.",
        "guardrail_notes": "Numbered structure cannot remove mandatory disclosures, uncertainty statements, or escalation language.",
    },
    {
        "knowledge_id": "rag007-voice-yes-and-posture",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-091"],
        "project_rule": "Use a non-defensive delivery posture when acknowledging objections; the voice should sound constructive rather than argumentative.",
        "safe_application": "Use to guide delivery tone for ordinary resistance where the agent can acknowledge and continue.",
        "do_not_use_when": "Do not sound agreeable when correcting a false claim, honoring a refusal, or delivering a compliance boundary.",
        "guardrail_notes": "This is delivery guidance only; it does not change the guarded text.",
    },
    {
        "knowledge_id": "rag007-voice-tone-mismatch-uncertainty",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-098"],
        "project_rule": "If words and vocal delivery appear misaligned, treat that as uncertainty and ask a gentle clarification instead of assuming hidden emotion or intent.",
        "safe_application": "Use when a customer says something positive or neutral but sounds hesitant, strained, or unsure, and a clarification would reduce pressure.",
        "do_not_use_when": "Do not override explicit consent, refusal, factual statements, compliance boundaries, or customer-stated preferences.",
        "guardrail_notes": "The agent must not claim it knows the customer's real emotion from tone; tone is only a weak signal for choosing a low-pressure clarification.",
    },
    {
        "knowledge_id": "rag007-voice-trustworthy-not-forced-friendly",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-099"],
        "project_rule": "Prefer a trustworthy, straightforward, moderately warm delivery over forced friendliness or entertainment.",
        "safe_application": "Use as the default delivery target across serious B2B and B2C sales campaigns.",
        "do_not_use_when": "Do not use exaggerated cheer, jokes, or overfamiliar phrasing in high-stakes or regulated contexts.",
        "guardrail_notes": "Campaign persona can adjust warmth, but trust and clarity remain the default delivery priority.",
    },
    {
        "knowledge_id": "rag007-voice-bounded-vocal-toolbox",
        "lane": "voice_delivery",
        "source_chunk_ids": ["rag005-chunk-101"],
        "project_rule": "Use controlled variation in pace, pitch, volume, warmth, and silence to support clarity and engagement.",
        "safe_application": "Use to guide TTS delivery metadata and human-review rubrics for freeform sales responses.",
        "do_not_use_when": "Do not imitate a source speaker's identity, accent, personal style, or theatrical performance.",
        "guardrail_notes": "Protected campaign scripts and compliance text must stay exact even when delivery metadata changes.",
    },
]

SELECTED_CHUNK_IDS = tuple(rule["source_chunk_ids"][0] for rule in SELECTED_KNOWLEDGE_RULES)
PRESSURE_TACTIC_CHUNK_IDS = {
    "rag005-chunk-071",
    "rag005-chunk-075",
    "rag005-chunk-076",
    "rag005-chunk-077",
    "rag005-chunk-087",
}
```

- [ ] **Step 2: Add JSON loading, relative paths, and source lookup**

Append:

```python
def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path | str) -> dict[str, Any]:
    json_path = Path(path)
    return json.loads(json_path.read_text(encoding="utf-8"))


def load_manifest_sources(path: Path | str) -> dict[str, dict[str, Any]]:
    payload = load_json(path)
    manifest = payload.get("source_manifest", payload)
    return {str(source.get("source_id", "")): source for source in manifest.get("sources", [])}


def index_rag005_chunks(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(chunk.get("chunk_candidate_id", "")): chunk for chunk in payload.get("chunk_candidates", [])}


def rag006_chunk_locations(payload: dict[str, Any]) -> dict[str, list[str]]:
    locations: dict[str, list[str]] = {}
    for item in payload.get("first_slice_candidates", []):
        locations.setdefault(str(item.get("chunk_id", "")), []).append("first_slice_candidates")
    queues = payload.get("review_queues", {})
    for item in queues.get("quote_review_queue", []):
        locations.setdefault(str(item.get("chunk_id", "")), []).append("quote_review_queue")
    for item in queues.get("topic_mapping_queue", []):
        locations.setdefault(str(item.get("chunk_id", "")), []).append("topic_mapping_queue")
    for group in queues.get("source_mapping_queue", []):
        for chunk_id in group.get("chunk_ids", []):
            locations.setdefault(str(chunk_id), []).append("source_mapping_queue")
    return locations
```

- [ ] **Step 3: Add payload builder**

Append:

```python
def source_metadata_for(source_ids: list[str], sources: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    metadata = []
    for source_id in source_ids:
        source = sources.get(source_id, {})
        metadata.append(
            {
                "source_id": source_id,
                "canonical_title": str(source.get("canonical_title", "")),
                "metadata_status": str(source.get("metadata_status", "needs_human_review")),
                "rights_status": str(source.get("rights_status", "needs_review")),
            }
        )
    return metadata


def build_knowledge_item(
    rule: dict[str, Any],
    *,
    chunk_index: dict[str, dict[str, Any]],
    locations: dict[str, list[str]],
    sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    chunk_id = rule["source_chunk_ids"][0]
    if chunk_id not in chunk_index:
        raise ValueError(f"Selected RAG-007 chunk is missing from RAG-005 input: {chunk_id}")
    if chunk_id not in locations:
        raise ValueError(f"Selected RAG-007 chunk is missing from RAG-006 input: {chunk_id}")
    if chunk_id in PRESSURE_TACTIC_CHUNK_IDS:
        raise ValueError(f"Pressure tactic chunk cannot be promoted in RAG-007: {chunk_id}")
    chunk = chunk_index[chunk_id]
    source_ids = list(chunk.get("source_ids", []))
    if not source_ids:
        raise ValueError(f"Selected RAG-007 chunk has no mapped source IDs: {chunk_id}")
    if "source_mapping_queue" in locations[chunk_id] or "topic_mapping_queue" in locations[chunk_id]:
        raise ValueError(f"Selected RAG-007 chunk still needs source or topic mapping: {chunk_id}")
    return {
        "knowledge_id": rule["knowledge_id"],
        "lane": rule["lane"],
        "source_chunk_ids": list(rule["source_chunk_ids"]),
        "source_ids": source_ids,
        "source_titles": [str(chunk.get("source_title", ""))],
        "source_metadata": source_metadata_for(source_ids, sources),
        "topic_ids": list(chunk.get("topic_ids", [])),
        "review_verdict": "manual_first_slice_paraphrased",
        "quote_dependency_resolved": True,
        "project_rule": rule["project_rule"],
        "safe_application": rule["safe_application"],
        "do_not_use_when": rule["do_not_use_when"],
        "guardrail_notes": rule["guardrail_notes"],
        "rag006_locations": sorted(set(locations[chunk_id])),
        "runtime_eligible_now": False,
        "retrieval_eligible_now": False,
    }
```

- [ ] **Step 4: Add main builder and report renderer**

Append:

```python
def build_reviewed_first_slice(
    rag006_packet_path: Path | str,
    rag005_result_path: Path | str,
    source_manifest_path: Path | str,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    root_path = root or Path(__file__).resolve().parents[1]
    rag006_path = Path(rag006_packet_path)
    rag005_path = Path(rag005_result_path)
    manifest_path = Path(source_manifest_path)
    if not rag006_path.is_absolute():
        rag006_path = root_path / rag006_path
    if not rag005_path.is_absolute():
        rag005_path = root_path / rag005_path
    if not manifest_path.is_absolute():
        manifest_path = root_path / manifest_path

    rag006_payload = load_json(rag006_path)
    rag005_payload = load_json(rag005_path)
    chunk_index = index_rag005_chunks(rag005_payload)
    locations = rag006_chunk_locations(rag006_payload)
    sources = load_manifest_sources(manifest_path)
    knowledge_items = [
        build_knowledge_item(rule, chunk_index=chunk_index, locations=locations, sources=sources)
        for rule in SELECTED_KNOWLEDGE_RULES
    ]
    lane_counts = {
        "response_wording": sum(1 for item in knowledge_items if item["lane"] == "response_wording"),
        "voice_delivery": sum(1 for item in knowledge_items if item["lane"] == "voice_delivery"),
    }
    return {
        "reviewed_slice_id": RAG_REVIEWED_FIRST_SLICE_ID,
        "inputs": {
            "rag006_packet_path": rel_path(rag006_path, root_path),
            "rag005_result_path": rel_path(rag005_path, root_path),
            "source_manifest_path": rel_path(manifest_path, root_path),
        },
        "summary": {
            "selected_chunk_count": len(SELECTED_CHUNK_IDS),
            "knowledge_item_count": len(knowledge_items),
            "lane_counts": lane_counts,
            "auto_promoted_chunk_count": 0,
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "source_excerpt_text_stored": False,
            "external_provider_calls_made": False,
            "notebooklm_api_used": False,
            "private_customer_data_used": False,
            "source_metadata_final": False,
        },
        "knowledge_items": knowledge_items,
        "excluded_categories": [
            "scarcity_loss_aversion",
            "decoy_effect_choice_architecture",
            "sunk_cost_reframing",
            "reciprocity_pressure",
            "authority_borrowing",
            "sensitive_demographic_personalization",
        ],
        "boundaries": {
            "runtime_retrieval_enabled": False,
            "chunk_import_enabled": False,
            "auto_promote_allowed": False,
            "source_excerpt_text_stored": False,
            "provider_calls_allowed": False,
            "private_customer_data_allowed": False,
            "reads_data_private": False,
            "retrieval_policy_required_before_runtime_use": True,
        },
    }


def render_reviewed_first_slice_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RAG-007 Reviewed First Slice",
        "",
        "RAG-007 creates a manually reviewed, paraphrased first knowledge slice. Runtime retrieval remains disabled.",
        "",
        "## Summary",
        "",
        f"- Selected chunks: `{summary['selected_chunk_count']}`",
        f"- Knowledge items: `{summary['knowledge_item_count']}`",
        f"- Response wording items: `{summary['lane_counts']['response_wording']}`",
        f"- Voice delivery items: `{summary['lane_counts']['voice_delivery']}`",
        f"- Auto-promoted chunks: `{summary['auto_promoted_chunk_count']}`",
        f"- Runtime retrieval enabled: `{summary['runtime_retrieval_enabled']}`",
        f"- Chunk import enabled: `{summary['chunk_import_enabled']}`",
        f"- Source excerpt text stored: `{summary['source_excerpt_text_stored']}`",
        f"- Source metadata final: `{summary['source_metadata_final']}`",
        "",
        "## Response wording",
        "",
        "| Knowledge ID | Source Chunk | Rule |",
        "| --- | --- | --- |",
    ]
    for item in payload["knowledge_items"]:
        if item["lane"] != "response_wording":
            continue
        rule = item["project_rule"].replace("|", "/")
        lines.append(f"| `{item['knowledge_id']}` | `{item['source_chunk_ids'][0]}` | {rule} |")
    lines.extend(["", "## Voice delivery", "", "| Knowledge ID | Source Chunk | Rule |", "| --- | --- | --- |"])
    for item in payload["knowledge_items"]:
        if item["lane"] != "voice_delivery":
            continue
        rule = item["project_rule"].replace("|", "/")
        lines.append(f"| `{item['knowledge_id']}` | `{item['source_chunk_ids'][0]}` | {rule} |")
    lines.extend(
        [
            "",
            "## Review Rules",
            "",
            "- All items are project-owned paraphrases.",
            "- Quote-dependent source text is not copied forward.",
            "- Campaign guardrails, customer refusal, compliance text, and human escalation override every item.",
            "- Tone mismatch is treated as uncertainty that can justify a gentle clarification, not as emotion certainty.",
            "",
            "## Boundaries",
            "",
            "- Runtime retrieval remains disabled.",
            "- Chunk import remains disabled.",
            "- No provider or NotebookLM API calls are made.",
            "- No private customer data or `data/private` path is used.",
            "",
        ]
    )
    return "\n".join(lines)
```

- [ ] **Step 5: Run validator to verify module RED advances to runner/doc failures**

Run:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
```

Expected:

```text
AssertionError: RAG-007 reviewed first slice runner is missing.
```

- [ ] **Step 6: Commit module**

Run:

```powershell
git add scripts\rag_reviewed_first_slice.py
git commit -m "feat: add RAG-007 reviewed slice builder"
```

### Task 3: Runner, Case Metadata, And Product Doc Stub

**Files:**
- Create: `scripts/run_rag_007_reviewed_first_slice.py`
- Create: `research/experiments/cases/rag-007-reviewed-first-slice.json`
- Create: `docs/product/RAG_007_REVIEWED_FIRST_SLICE.md`

- [ ] **Step 1: Add runner**

Create `scripts/run_rag_007_reviewed_first_slice.py`:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag_reviewed_first_slice import build_reviewed_first_slice, render_reviewed_first_slice_report


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAG006_PACKET = ROOT / "research" / "experiments" / "generated" / "RAG-006-chunk-review-packet" / "result.json"
DEFAULT_RAG005_RESULT = ROOT / "research" / "experiments" / "generated" / "RAG-005-chunk-normalization" / "result.json"
DEFAULT_SOURCE_MANIFEST = ROOT / "research" / "experiments" / "generated" / "RAG-004-source-manifest-normalization" / "result.json"
DEFAULT_OUTPUT_DIR = ROOT / "research" / "experiments" / "generated" / "RAG-007-reviewed-first-slice"
DEFAULT_RESULT = DEFAULT_OUTPUT_DIR / "result.json"
DEFAULT_REPORT = DEFAULT_OUTPUT_DIR / "report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the RAG-007 manually reviewed first knowledge slice.")
    parser.add_argument("--rag006-packet", default=str(DEFAULT_RAG006_PACKET), help="RAG-006 review packet JSON path.")
    parser.add_argument("--rag005-result", default=str(DEFAULT_RAG005_RESULT), help="RAG-005 chunk-normalization result JSON path.")
    parser.add_argument("--source-manifest", default=str(DEFAULT_SOURCE_MANIFEST), help="RAG-004 source manifest JSON path.")
    parser.add_argument("--out", default=str(DEFAULT_RESULT), help="Output JSON reviewed slice path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Output Markdown reviewed slice report path.")
    return parser.parse_args()


def resolve_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    args = parse_args()
    rag006_packet = resolve_path(args.rag006_packet)
    rag005_result = resolve_path(args.rag005_result)
    source_manifest = resolve_path(args.source_manifest)
    out_path = resolve_path(args.out)
    report_path = resolve_path(args.report_out)
    payload = build_reviewed_first_slice(rag006_packet, rag005_result, source_manifest, root=ROOT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_reviewed_first_slice_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add case metadata**

Create `research/experiments/cases/rag-007-reviewed-first-slice.json`:

```json
{
  "rag_review_id": "RAG-007-reviewed-first-slice",
  "title": "Reviewed first RAG knowledge slice",
  "description": "Promotes a small paraphrased, source-tracked response-wording and voice-delivery slice for review artifacts only, without runtime retrieval.",
  "default_rag006_packet": "research/experiments/generated/RAG-006-chunk-review-packet/result.json",
  "default_rag005_result": "research/experiments/generated/RAG-005-chunk-normalization/result.json",
  "default_source_manifest": "research/experiments/generated/RAG-004-source-manifest-normalization/result.json",
  "runtime_retrieval_enabled": false,
  "chunk_import_enabled": false,
  "auto_promotion_enabled": false,
  "metadata_only": true,
  "selected_lanes": [
    "response_wording",
    "voice_delivery"
  ],
  "selected_chunk_ids": [
    "rag005-chunk-017",
    "rag005-chunk-020",
    "rag005-chunk-022",
    "rag005-chunk-024",
    "rag005-chunk-025",
    "rag005-chunk-091",
    "rag005-chunk-098",
    "rag005-chunk-099",
    "rag005-chunk-101"
  ],
  "notes": [
    "This checkpoint resolves quote-dependent candidates by storing project-owned paraphrases.",
    "It rejects pressure tactics and sensitive demographic personalization from the first slice.",
    "It does not import chunks into runtime memory or enable retrieval.",
    "A guarded retrieval policy is required before runtime use."
  ]
}
```

- [ ] **Step 3: Add product doc stub**

Create `docs/product/RAG_007_REVIEWED_FIRST_SLICE.md`:

````markdown
# RAG-007 Reviewed First Slice

## Purpose

RAG-007 creates the first manually reviewed RAG knowledge slice from the RAG-006 review packet.

It is a promotion gate for reviewed artifacts, not a runtime retrieval checkpoint.

## Selected Slice

Response wording:

- Yes-And objection framing
- short declarative statements
- empathy echo
- PREP structure
- 3-2-1 answer structure

Voice delivery:

- Yes-And delivery posture
- tone mismatch as uncertainty and clarification
- trustworthiness over forced friendliness
- bounded vocal toolbox guidance

## Commands

Run the reviewed-first-slice builder:

```powershell
python scripts\run_rag_007_reviewed_first_slice.py
```

Validate the RAG-007 reviewed-slice contract:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
```

## Default Output

```text
research\experiments\generated\RAG-007-reviewed-first-slice\
```

The output contains:

- `result.json`
- `report.md`

## Product Boundary

RAG-007 keeps the architecture unchanged:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + reviewed sales knowledge layer
  + explicit guardrails and human escalation paths
```

Runtime retrieval remains disabled. Chunk import remains disabled. No source excerpt text, private customer data, provider call, NotebookLM API call, API key, or `data/private` read is used.
````

- [ ] **Step 4: Run validator to verify GREEN**

Run:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
```

Expected:

```text
RAG-007 reviewed first slice validation passed.
```

- [ ] **Step 5: Commit runner, case, and doc stub**

Run:

```powershell
git add scripts\run_rag_007_reviewed_first_slice.py research\experiments\cases\rag-007-reviewed-first-slice.json docs\product\RAG_007_REVIEWED_FIRST_SLICE.md
git commit -m "feat: add RAG-007 reviewed slice runner"
```

### Task 4: Generate Official RAG-007 Artifacts

**Files:**
- Generated: `research/experiments/generated/RAG-007-reviewed-first-slice/result.json`
- Generated: `research/experiments/generated/RAG-007-reviewed-first-slice/report.md`

- [ ] **Step 1: Run RAG-007 with real project inputs**

Run:

```powershell
python scripts\run_rag_007_reviewed_first_slice.py
```

Expected summary:

```json
{
  "selected_chunk_count": 9,
  "knowledge_item_count": 9,
  "lane_counts": {
    "response_wording": 5,
    "voice_delivery": 4
  },
  "auto_promoted_chunk_count": 0,
  "runtime_retrieval_enabled": false,
  "chunk_import_enabled": false,
  "source_excerpt_text_stored": false,
  "external_provider_calls_made": false,
  "notebooklm_api_used": false,
  "private_customer_data_used": false,
  "source_metadata_final": false
}
```

- [ ] **Step 2: Validate generated artifacts**

Run:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
```

Expected:

```text
RAG-007 reviewed first slice validation passed.
```

- [ ] **Step 3: Inspect output for forbidden text markers**

Run:

```powershell
rg -n '"source_excerpt_text":|quote_review_required|runtime_retrieval_enabled.: true|retrieval_eligible_now.: true|runtime_eligible_now.: true|reads_data_private.: true' research\experiments\generated\RAG-007-reviewed-first-slice docs\product\RAG_007_REVIEWED_FIRST_SLICE.md
```

Expected: no matches.

- [ ] **Step 4: Commit generated artifacts**

Run:

```powershell
git add research\experiments\generated\RAG-007-reviewed-first-slice\result.json research\experiments\generated\RAG-007-reviewed-first-slice\report.md
git commit -m "data: generate RAG-007 reviewed first slice"
```

### Task 5: Documentation, Setup, And Thesis Wiring

**Files:**
- Modify: `docs/product/RAG_007_REVIEWED_FIRST_SLICE.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `scripts/check_setup.py`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`

- [ ] **Step 1: Expand product doc with run counts**

In `docs/product/RAG_007_REVIEWED_FIRST_SLICE.md`, add this section after `Default Output`:

```markdown
## Current Reviewed Slice Run

The 2026-05-06 run against the refreshed RAG-006 packet produced:

- `9` reviewed knowledge items
- `5` response-wording items
- `4` voice-delivery items
- `0` auto-promoted chunks
- source excerpt text stored: `false`
- runtime retrieval disabled
- chunk import disabled
- provider and NotebookLM calls made: `false`
- private customer data used: `false`

The slice is vertical-agnostic and campaign-guardrail-compatible. It prepares reviewed knowledge for a later retrieval-policy checkpoint but does not make the runtime sales agent use RAG.
```

- [ ] **Step 2: Add RAG-007 commands**

In `docs/product/COMMANDS.md`, insert after the RAG-006 validation command:

````markdown

Run RAG-007 reviewed first-slice promotion after RAG-006 creates review queues:

```powershell
python scripts\run_rag_007_reviewed_first_slice.py
```

Default RAG-007 output folder:

```text
research\experiments\generated\RAG-007-reviewed-first-slice\
```

Validate RAG-007 reviewed paraphrases, selected chunk IDs, pressure-tactic exclusions, no-source-excerpt storage, and no-runtime-retrieval boundary:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
```
````

- [ ] **Step 3: Register RAG-007 in setup**

In `scripts/check_setup.py`, add required-file entries next to the RAG-006 entries:

```python
    ("file.docs_product_rag_007_reviewed_first_slice", "docs/product/RAG_007_REVIEWED_FIRST_SLICE.md", "RAG reviewed first slice"),
```

```python
    ("file.scripts_rag_reviewed_first_slice", "scripts/rag_reviewed_first_slice.py", "RAG reviewed first slice module"),
    ("file.scripts_run_rag_007_reviewed_first_slice", "scripts/run_rag_007_reviewed_first_slice.py", "RAG reviewed first slice runner"),
    ("file.scripts_validate_rag_007_reviewed_first_slice", "scripts/validate_rag_007_reviewed_first_slice.py", "RAG reviewed first slice validator"),
```

In the required case-file block, add:

```python
    ("file.research_case_rag_007_reviewed_first_slice", "research/experiments/cases/rag-007-reviewed-first-slice.json", "RAG reviewed first slice case file"),
```

- [ ] **Step 4: Update roadmap checkpoint board**

In `docs/thesis/ROADMAP.md`, change the current RAG checkpoint to the next guarded retrieval-policy design and add RAG-007 to completed checkpoints:

```markdown
- [ ] Current: design the guarded RAG retrieval policy that can query only reviewed knowledge slices, keep campaign guardrails authoritative, and keep runtime retrieval disabled until validation proves filtering, citation, and refusal behavior.
```

```markdown
- [x] `RAG-007` reviewed first slice, which promoted `9` manually reviewed, project-owned paraphrased knowledge items from RAG-006/RAG-005 into a review artifact only: `5` response-wording items and `4` voice-delivery items. It excluded pressure tactics and sensitive demographic personalization, rewrote tone-mismatch guidance as uncertainty plus clarification rather than emotion certainty, stored no source excerpt text, made no provider or NotebookLM calls, used no private customer data, and kept runtime retrieval plus chunk import disabled.
```

- [ ] **Step 5: Update methodology log**

Add a new top entry to `docs/thesis/METHODOLOGY_LOG.md`:

```markdown
### 2026-05-06 - RAG-007 reviewed first slice

- Objective: move from RAG-006 review queues to one manually reviewed, source-tracked first knowledge slice without enabling runtime retrieval.
- Action taken: added a failing RAG-007 validator first, implemented `scripts/rag_reviewed_first_slice.py`, added `scripts/run_rag_007_reviewed_first_slice.py`, generated the reviewed-slice JSON/Markdown artifact, documented the checkpoint, and added it to setup gates.
- Data used: the RAG-006 review packet, the RAG-005 chunk-normalization result, and the RAG-004 source manifest under `research/experiments/generated`. No NotebookLM API call, LLM call, TTS/ASR provider call, private customer data, raw call-center audio, API key, raw source text import, chunk import, or runtime retrieval was used.
- Output created: `docs/product/RAG_007_REVIEWED_FIRST_SLICE.md`, `research/experiments/cases/rag-007-reviewed-first-slice.json`, `research/experiments/generated/RAG-007-reviewed-first-slice/result.json`, `research/experiments/generated/RAG-007-reviewed-first-slice/report.md`, `scripts/rag_reviewed_first_slice.py`, `scripts/run_rag_007_reviewed_first_slice.py`, and `scripts/validate_rag_007_reviewed_first_slice.py`.
- What was learned: the first safe slice should combine response-wording guidance and voice-delivery guidance, but voice/prosody rules must stay non-diagnostic. Tone mismatch is only a weak uncertainty signal that can trigger a gentle clarification; it cannot override explicit customer intent, compliance, campaign scripts, refusal handling, or human escalation.
- Open questions: what retrieval policy should query these reviewed items, how retrieved items should be cited in decision traces, and which campaign guardrails must block or override retrieval before any runtime use.
```

- [ ] **Step 6: Run docs/setup validation**

Run:

```powershell
python scripts\validate_rag_007_reviewed_first_slice.py
python scripts\check_setup.py --json
git diff --check
```

Expected:

```text
RAG-007 reviewed first slice validation passed.
```

`check_setup.py --json` should report no missing RAG-007 assets.

- [ ] **Step 7: Commit docs and setup wiring**

Run:

```powershell
git add docs\product\RAG_007_REVIEWED_FIRST_SLICE.md docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md
git commit -m "docs: document RAG-007 reviewed first slice"
```

### Task 6: Final Verification

**Files:**
- Verify only

- [ ] **Step 1: Run RAG validation chain**

Run:

```powershell
python scripts\validate_rag_004_source_manifest_normalization.py
python scripts\validate_rag_005_chunk_normalization.py
python scripts\validate_rag_006_chunk_review_packet.py
python scripts\validate_rag_007_reviewed_first_slice.py
```

Expected:

```text
RAG-004 source manifest normalization validation passed.
RAG-005 chunk normalization validation passed.
RAG-006 chunk review packet validation passed.
RAG-007 reviewed first slice validation passed.
```

- [ ] **Step 2: Run setup and diff checks**

Run:

```powershell
python scripts\check_setup.py --json
git diff --check
```

Expected: setup passes and `git diff --check` prints no whitespace errors.

- [ ] **Step 3: Confirm RAG-007 did not enable retrieval**

Run:

```powershell
rg -n "\"runtime_retrieval_enabled\": true|\"chunk_import_enabled\": true|\"retrieval_eligible_now\": true|\"runtime_eligible_now\": true" scripts docs\product research\experiments\cases research\experiments\generated\RAG-007-reviewed-first-slice
```

Expected: no matches.

- [ ] **Step 4: Confirm no private-data boundary is referenced**

Run:

```powershell
rg -n "data/private|private customer data used.: true|reads_data_private.: true" scripts\rag_reviewed_first_slice.py scripts\run_rag_007_reviewed_first_slice.py scripts\validate_rag_007_reviewed_first_slice.py docs\product\RAG_007_REVIEWED_FIRST_SLICE.md research\experiments\generated\RAG-007-reviewed-first-slice
```

Expected: no matches except allowed prose that states private data is not used.

- [ ] **Step 5: Commit final verification note only if files changed**

If final verification requires a small correction, commit only the corrected RAG-007 files:

```powershell
git add scripts\rag_reviewed_first_slice.py scripts\run_rag_007_reviewed_first_slice.py scripts\validate_rag_007_reviewed_first_slice.py docs\product\RAG_007_REVIEWED_FIRST_SLICE.md docs\product\COMMANDS.md scripts\check_setup.py docs\thesis\ROADMAP.md docs\thesis\METHODOLOGY_LOG.md research\experiments\cases\rag-007-reviewed-first-slice.json research\experiments\generated\RAG-007-reviewed-first-slice\result.json research\experiments\generated\RAG-007-reviewed-first-slice\report.md
git commit -m "fix: tighten RAG-007 reviewed slice validation"
```

If no files changed, do not create an empty commit.
