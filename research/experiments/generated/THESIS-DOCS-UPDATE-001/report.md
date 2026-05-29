# THESIS-DOCS-UPDATE-001

## Baseline Verification

- Verified latest thesis-doc baseline commit: `10117b6df799b869783b4a840503947bf67a1734`
- Commit message: `docs(thesis): update project documentation from latest evidence`
- Commit date: `2026-05-29T00:52:29+02:00`
- Known checkpoint checked: `09228e0c23548ae799ca7baf7ede9ced7aea83ad`, `2026-05-25T01:29:50+02:00`
- Finding: the known 2026-05-25 checkpoint is not the latest thesis-doc update. The update range for this phase is `10117b6df799b869783b4a840503947bf67a1734..HEAD` before these docs edits.

## Thesis Files Discovered

- `docs/thesis/AI_USAGE_NOTE.md`
- `docs/thesis/BASELINE_SPEC.md`
- `docs/thesis/COLLABORATION_NOTE.md`
- `docs/thesis/DECISION_LOG.md`
- `docs/thesis/EVALUATION_RUBRIC.md`
- `docs/thesis/FIRST_EXPERIMENT_PLAN.md`
- `docs/thesis/METHODOLOGY_LOG.md`
- `docs/thesis/PROJECT_BRIEF.md`
- `docs/thesis/PROMPT_EVAL_WORKFLOW.md`
- `docs/thesis/ROADMAP.md`
- `docs/thesis/SPEECH_REALISM_REFERENCES.md`
- `docs/thesis/THESIS_OUTLINE.md`
- `docs/thesis/THESIS_REFERENCE_REGISTRY.md`
- `docs/thesis/THESIS_WRITING_GUIDE.md`

## Files Updated

- `docs/thesis/DECISION_LOG.md`: added Ultravox hosted-interface and cleaned prosody/mapping decisions.
- `docs/thesis/METHODOLOGY_LOG.md`: added Ultravox and prosody cleanup entries, and corrected the thesis baseline to `10117b6d`.
- `docs/thesis/ROADMAP.md`: moved near-term work from prosody cleanup to thesis consolidation, sales-dialogue quality work, and non-LLM/action-selector research; marked Ultravox latency testing stopped for now.
- `docs/thesis/THESIS_REFERENCE_REGISTRY.md`: updated Ultravox references/evidence and Fish/prosody status.
- `docs/thesis/SPEECH_REALISM_REFERENCES.md`: added Ultravox hosted speech-interface source notes and current boundaries.
- `docs/thesis/EVALUATION_RUBRIC.md`: added tool-boundary, warm-turn latency, voice naturalness, and manual listening-review dimensions.
- `docs/thesis/BASELINE_SPEC.md`, `PROJECT_BRIEF.md`, `PROMPT_EVAL_WORKFLOW.md`, `AI_USAGE_NOTE.md`, `COLLABORATION_NOTE.md`, `THESIS_WRITING_GUIDE.md`, and `THESIS_OUTLINE.md`: updated current architecture/methodology framing.
- `research/experiments/generated/THESIS-DOCS-UPDATE-001/result.json` and this report: corrected the baseline and recorded the new evidence range.

## Files Intentionally Not Updated

- `docs/thesis/FIRST_EXPERIMENT_PLAN.md`: historical phase-1 plan; the post-baseline Ultravox/prosody conclusions do not belong in the first experiment definition.
- `runtime/**`: this phase is documentation/evidence only.
- `runtime/campaigns/**`: campaign behavior and response text were out of scope.
- `scripts/**`: no checker or runtime script change was needed.
- `local_artifacts/**`: no model weights, generated audio, or local artifacts were copied.

## Evidence Reviewed

Post-baseline evidence after `10117b6d`:

- Prosody cleanup and mapping: `PROSODY-TAXONOMY-CLEANUP-001`, `ELEVENLABS-PROSODY-MAPPING-PROTOTYPE-001`, `ELEVENLABS-PROSODY-MAPPING-QUALITY-AUDIT-001`, `ELEVENLABS-PROSODY-MAPPING-DECISION-001`
- Ultravox tool and hosted sandbox: `ULTRAVOX-TOOL-BOUNDARY-MOCK-001`, `ULTRAVOX-LOCAL-TOOL-ENDPOINT-001`, `ULTRAVOX-TUNNEL-SANDBOX-001`, `ULTRAVOX-WEBSOCKET-TEXT-SANDBOX-001`, `ULTRAVOX-WEBSOCKET-AUDIO-SANDBOX-001`
- Ultravox review and latency: `ULTRAVOX-AUDIO-LISTENING-REVIEW-MANUAL-001`, `ULTRAVOX-WARM-SESSION-LATENCY-001`, `ULTRAVOX-WARM-SESSION-LATENCY-AUDIT-001`, `ULTRAVOX-LATENCY-OPTIMIZATION-BENCHMARK-001`, `ULTRAVOX-LATENCY-OPTIMIZATION-AUDIT-001`, `ULTRAVOX-AUDIO-SANDBOX-REVIEW-DECISION-001`

## Major Decisions Reflected

- Ultravox is a promising hosted speech-native interface candidate with a working sandbox tool boundary, not the current runtime path and not the final ElevenLabs replacement.
- Project runtime remains owner of campaign truth, sales-brain decisions, canonical memory, source/fact boundaries, verifier logic, and side-effect safety.
- Ultravox audio quality is promising in manual review, but warm-turn latency is not live-ready.
- Stop Ultravox provider latency testing for now.
- Prosody cleanup preserved 267 labels, 24 categories, and 46 composition rules; mappings were cleaned from 138 to 92; duplicate mapping signatures, vague labels, backend hint boilerplate, mapping warnings, and mapping failures were reduced to 0.
- The ElevenLabs prosody mapping prototype produced 62 examples with 62 pass, 0 warning, and 0 fail, without provider calls, response text changes, raw Fish tag leakage, or live wiring.

## References Added Or Updated

- Ultravox docs: overview, docs root, how Ultravox works, tools overview, HTTP versus client tools, authentication, durable versus temporary tools, WebSocket, data messages, call stages, making-calls, prompting, SDK, voices, hosted voice join-host validator pattern, pricing, repository, and model cards.
- Fish Audio S2 / fish-speech / s2-pro / speech.fish.audio status updated with cleaned taxonomy and mapping counts.
- Speech realism references updated with Ultravox hosted speech-interface boundaries and latency caveat.

## Side Effects

- Provider/model/audio calls made by this docs update: false
- OpenAI API calls made by this docs update: false
- Local LLM/Ollama generation made by this docs update: false
- Liquid/Fish/Kokoro inference made by this docs update: false
- ElevenLabs/live TTS calls made by this docs update: false
- Model downloads/training made by this docs update: false
- Audio generation made by this docs update: false
- Raw private transcript/audio copied: false
- Runtime behavior changed: false
- Response text changed: false
- Live runtime wiring changed: false

## Validation

- `python scripts\validate_thesis_reference_registry.py`: pass. Initial run exposed missing Ultravox URL coverage; registry was updated with the exact source/docs and validator host-pattern references, then the validator passed.
- `python scripts\validate_thesis_update_gate.py`: pass.
- `python scripts\validate_runtime_manifest.py`: pass; reported `runtime_behavior_changed: false` and `response_text_changed: false`.
- `python scripts\validate_project_drift_guard.py`: pass.
- `git diff --check`: pass. Git printed line-ending warnings only; no whitespace errors.
