# LIQUID-AUDIO-LATENCY-AUDIT-001

- status: pass
- processor_load_time_seconds: 1.14
- full_model_load_time_seconds: 2.436
- tts_p50_generation_seconds: 12.896955
- tts_p90_generation_seconds: 21.416825
- first_audio_p50_seconds: 0.313958
- first_audio_p90_seconds: 0.558489
- rtf_average: 1.743069
- current_smoke_live_usable: false
- streaming_interleaved_could_improve_perceived_latency: true
- streaming_requires_verifier_gating_before_playback: true
- live_wiring_allowed: false
- sales_brain_replacement_allowed: false

## Interpretation

First-audio latency is promising, but full generation latency and RTF are too slow for live voice. Liquid remains plausible for offline demos, batch audio, or architecture inspiration pending listening review and prompt/mode fixes.
