# LOCAL-AUDIO-BENCHMARK-PLANS-001

Status: pass

Phase 4I0 added future benchmark plans only:

- `runtime/audio_backends/benchmark_plans/liquid_audio_feasibility_plan.json`
- `runtime/audio_backends/benchmark_plans/kokoro_tts_benchmark_plan.json`
- `runtime/audio_backends/benchmark_plans/fish_inspired_prosody_policy_plan.json`

## Source Links

- Liquid Audio: https://github.com/Liquid4All/liquid-audio
- Liquid model card: https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B
- Kokoro repo: https://github.com/hexgrad/kokoro
- Kokoro model card: https://huggingface.co/hexgrad/Kokoro-82M
- Fish S2: https://fish.audio/s2/
- Fish Speech repo: https://github.com/fishaudio/fish-speech
- Fish S2 model card: https://huggingface.co/fishaudio/s2-pro
- Fish docs: https://speech.fish.audio/

## Plans

- Liquid: install probe only, no model download unless gated, check package/model metadata, ASR on sanitized phrases, TTS on 20 short sales responses, optional interleaved S2S smoke, no live wiring.
- Kokoro: isolated audio venv, install probe, 20 short sales utterances, cold/warm latency, real-time factor, ignored local audio artifacts only, subjective quality review.
- Fish-inspired: no model install, internal prosody tag taxonomy, buyer emotion plus sales move mapping, validate no unsupported tag leakage, no live wiring.

## Side Effects

- model_downloads_performed: false
- model_weights_committed: false
- audio_files_committed: false
- provider_calls_made: false
- live_tts_calls_made: false
- local_model_generation_made: false
- runtime_behavior_changed: false
- response_text_changed: false
