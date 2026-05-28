# LOCAL-AUDIO-S2S-ARCHITECTURE-PLAN-001

Status: pass

Phase 4I0 added `runtime/audio_backends/speech_to_speech_architecture_plan.json`.

## Source Links

- Liquid Audio repo: https://github.com/Liquid4All/liquid-audio
- Liquid LFM2.5-Audio model card: https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B
- Liquid audio model docs: https://docs.liquid.ai/lfm/models/audio-models

## Pipelines

Pipeline 1, current modular path:

`ASR -> transcript normalization -> conversation brain -> response text -> prosody planner -> TTS`

Pipeline 2, Liquid-inspired future path:

`audio input -> speech-to-speech/audio model -> transcript + candidate audio -> deterministic sales/memory/verifier -> controlled response audio`

## Boundary

Liquid is a future audio interface candidate, not the sales/conversation brain. Campaign facts, source grounding, memory ledger, and safety verifier stay project-owned. Candidate audio must not play live before verifier gating is designed and tested.

## Side Effects

- model_downloads_performed: false
- provider_calls_made: false
- live_tts_calls_made: false
- local_model_generation_made: false
- runtime_behavior_changed: false
- response_text_changed: false
