# RESP-002 Runtime Voice Delivery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `RESP-002`, an offline runtime voice-delivery layer that applies existing prosody planning and provider rendering to guarded `RESP-001` output.

**Architecture:** Add a focused `runtime_voice_delivery.py` module and `generate_runtime_voice_delivery.py` CLI. The module consumes a `RESP-001` packet, wraps the final response into protected or eligible segments, applies VOICE-015 prosody, renders one VOICE-016 provider preview, and appends a `voice_delivery` object without changing `final_response`.

**Tech Stack:** Python standard library, existing `generate_guarded_response.py`, `prosody_naturalness.py`, `provider_prosody_rendering.py`, JSON and Markdown artifacts.

---

### Task 1: Validator First

**Files:**
- Create: `scripts/validate_resp_002_runtime_voice_delivery.py`

- [x] **Step 1: Write failing validator**

The validator expects a `RESP-002` runner, JSON/report output, unchanged guarded response, offline provider rendering, protected segment behavior, and secret-free artifacts.

- [x] **Step 2: Run validator to verify RED**

Run:

```powershell
python scripts\validate_resp_002_runtime_voice_delivery.py
```

Expected:

```text
AssertionError: RESP-002 runner script is missing.
```

### Task 2: Runtime Voice Delivery Module

**Files:**
- Create: `scripts/runtime_voice_delivery.py`
- Create: `scripts/generate_runtime_voice_delivery.py`

- [x] **Step 1: Implement segment classification**

Classify `RESP-001` final responses as freeform or protected based on decision fields such as `sales_difficulty`, `next_action`, `interest_state`, and `call_control`.

- [x] **Step 2: Implement provider rendering**

Apply `apply_prosody_naturalness` and `render_provider_variant` to the delivery segments. Default provider is ElevenLabs.

- [x] **Step 3: Implement CLI and report**

The CLI should mirror `generate_guarded_response.py` arguments and write `RESP-002-runtime-voice-delivery-result.json` plus a Markdown report.

- [x] **Step 4: Run validator to verify GREEN**

Run:

```powershell
python scripts\validate_resp_002_runtime_voice_delivery.py
```

Expected:

```text
RESP-002 runtime voice delivery validation passed.
```

### Task 3: Docs And Setup Wiring

**Files:**
- Create: `docs/product/RESP_002_RUNTIME_VOICE_DELIVERY.md`
- Create: `research/experiments/RESP-002-runtime-voice-delivery.md`
- Create: generated RESP-002 artifacts
- Modify: `docs/product/COMMANDS.md`
- Modify: `docs/product/REALTIME_AGENT_ARCHITECTURE.md`
- Modify: `docs/product/RESP_001_GUARDED_RESPONSE_GENERATION.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`
- Modify: `scripts/check_setup.py`

- [x] **Step 1: Generate official artifact**

Run:

```powershell
python scripts\generate_runtime_voice_delivery.py --campaign campaign-prod-005-b2c-telecom --stage relevance-check --transcript "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt." --out research\experiments\generated\RESP-002-runtime-voice-delivery-result.json --report-out research\experiments\generated\RESP-002-runtime-voice-delivery-report.md
```

- [x] **Step 2: Document the checkpoint**

Explain that `RESP-002` is offline, vertical-agnostic, and applies prosody only after guarded response generation.

- [x] **Step 3: Run final verification**

Run:

```powershell
python scripts\validate_resp_002_runtime_voice_delivery.py
python scripts\validate_resp_001_guarded_response_generation.py
python scripts\validate_voice_015_prosody_naturalness.py
python scripts\validate_voice_016_provider_prosody_rendering.py
python scripts\check_setup.py --json
git diff --check
```
