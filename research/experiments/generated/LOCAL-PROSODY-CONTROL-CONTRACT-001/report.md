# LOCAL-PROSODY-CONTROL-CONTRACT-001

Status: pass

Phase 4I0 added a backend-neutral prosody object and mapping policy:

- `runtime/audio_backends/prosody_control_contract.py`
- `runtime/audio_backends/prosody_style_policy.json`

The policy records `voice_intent`, `buyer_emotion`, `sales_move`, `pace`, `warmth`, `confidence`, `energy`, `pause_policy`, `emphasis_terms`, `avoid`, and `backend_hints`.

## Backend Rules

- ElevenLabs: future mapping only. Do not insert Fish-style inline tags into ElevenLabs text.
- Kokoro: future benchmark mapping only. Speed/voice/punctuation mapping must be proven in an isolated benchmark.
- Fish-inspired: inspiration only. Inline examples such as `[pause]`, `[emphasis]`, `[calm]`, `[whispering]`, and `[reassuring]` are internal design vocabulary, not active runtime text.
- Liquid: future speech-to-speech style hints only. Sales brain, verifier, campaign facts, and memory stay project-owned.

## Side Effects

- provider_calls_made: false
- live_tts_calls_made: false
- fish_tags_wired_into_live_runtime: false
- runtime_behavior_changed: false
- response_text_changed: false
