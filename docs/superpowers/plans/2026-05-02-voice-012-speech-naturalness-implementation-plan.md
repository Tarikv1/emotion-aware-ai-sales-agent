# VOICE-012 Speech Naturalness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a campaign-configurable, segment-aware speech naturalness layer that can insert rare mid-utterance fillers without altering scripted questions or compliance-sensitive text.

**Architecture:** Keep the realtime policy and guarded response layers authoritative. VOICE-012 receives already-approved speech segments, protects scripted/company/compliance segments, and only adds deterministic lightweight fillers to eligible freeform segments before TTS.

**Tech Stack:** Python standard library, JSON case files, Markdown experiment reports.

---

### Task 1: Naturalness Module

**Files:**
- Create: `scripts/speech_naturalness.py`

- [ ] Define protected segment types such as `campaign_qualification_question`, `company_script`, `required_disclosure`, `compliance_statement`, `legal_or_medical_boundary`, `coverage_or_claim_boundary`, `do_not_call`, `hangup`, `appointment_confirmation`, and `sensitive_escalation`.
- [ ] Define eligible freeform segment types such as `freeform_empathy`, `freeform_objection_handling`, `freeform_transition`, `freeform_explanation`, and `freeform_clarification`.
- [ ] Add English and German filler inventories.
- [ ] Implement deterministic filler insertion with a campaign profile containing `enabled`, `filler_frequency`, `max_fillers_per_response`, `allow_casual_fillers`, and `allow_hesitation_sounds`.
- [ ] Return metadata proving which segments were protected, which fillers were inserted, and whether protected segments stayed unchanged.

### Task 2: VOICE-012 Runner

**Files:**
- Create: `scripts/run_voice_012_speech_naturalness.py`
- Create: `research/experiments/cases/voice-012-speech-naturalness.json`

- [ ] Add bilingual campaign profiles with different naturalness settings.
- [ ] Add cases for English/German freeform speech, mixed freeform plus campaign questions, compliance/disclosure protection, do-not-call/hangup protection, and disabled naturalness.
- [ ] Generate JSON and Markdown outputs under `research/experiments/generated/`.

### Task 3: Validator

**Files:**
- Create: `scripts/validate_voice_012_speech_naturalness.py`

- [ ] Run the VOICE-012 runner.
- [ ] Assert fillers appear only in eligible freeform segments.
- [ ] Assert protected campaign questions, disclosures, appointment confirmations, and hang-up lines remain byte-for-byte unchanged.
- [ ] Assert language-specific fillers are used only in matching language cases.
- [ ] Assert disabled profiles produce zero fillers.
- [ ] Assert no API key, provider call, or customer audio path exists in VOICE-012 outputs.

### Task 4: Documentation

**Files:**
- Create: `docs/product/VOICE_012_SPEECH_NATURALNESS_LAYER.md`
- Create: `research/experiments/VOICE-012-speech-naturalness.md`
- Modify: `docs/product/COMMANDS.md`
- Modify: `docs/product/REALTIME_AGENT_ARCHITECTURE.md`
- Modify: `docs/product/BILINGUAL_REALTIME_CORE.md`
- Modify: `docs/thesis/METHODOLOGY_LOG.md`
- Modify: `docs/thesis/ROADMAP.md`

- [ ] Document the segment model and campaign configurability.
- [ ] Explain why filler words are blocked in company-provided questions and compliance text.
- [ ] Record the thesis-methodology lesson: more human speech must be constrained by source-of-truth and compliance boundaries.

### Task 5: Verification

**Commands:**

```powershell
python scripts\validate_voice_012_speech_naturalness.py
python scripts\validate_resp_001_guarded_response_generation.py
python scripts\validate_lang_001_bilingual_realtime_core.py
python scripts\validate_voice_011_cartesia_websocket_smoke.py
python scripts\check_setup.py --json
```

- [ ] Confirm all commands exit `0`.
- [ ] Run a local secret-pattern scan before summarizing the change.
