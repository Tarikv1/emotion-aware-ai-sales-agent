# LOCAL-AUDIO-BACKEND-REGISTRY-001

Status: pass

Phase 4I0 created a repo-local, source-grounded audio backend registry at `runtime/audio_backends/audio_backend_candidates.json`. The registry is data/config only. It does not install packages, download model weights, load models, generate audio, call providers, or wire anything into live runtime.

## Source Links

- Liquid Audio: https://github.com/Liquid4All/liquid-audio
- Liquid model card: https://huggingface.co/LiquidAI/LFM2.5-Audio-1.5B
- Liquid license docs: https://docs.liquid.ai/lfm/help/model-license
- Liquid repo license: https://github.com/Liquid4All/liquid-audio/blob/main/LICENSE
- Fish S2: https://fish.audio/s2/
- Fish GitHub org: https://github.com/fishaudio
- Fish Speech repo: https://github.com/fishaudio/fish-speech
- Fish S2 model card: https://huggingface.co/fishaudio/s2-pro
- Fish docs: https://speech.fish.audio/
- Fish license: https://github.com/fishaudio/fish-speech/blob/main/LICENSE
- Kokoro repo: https://github.com/hexgrad/kokoro
- Kokoro model card: https://huggingface.co/hexgrad/Kokoro-82M
- Kokoro license: https://github.com/hexgrad/kokoro/blob/main/LICENSE

## Findings

- Liquid Audio is classified as a high-priority feasibility candidate for speech-to-speech, ASR, and TTS. It is not the sales brain.
- Fish Audio S2 is classified as prosody/emotion-control inspiration and research-only for now. The 24GB VRAM requirement and separate commercial license are blockers for direct local/product use.
- Kokoro-82M is classified as a local/offline TTS benchmark candidate. It is not a replacement for ElevenLabs without later latency and listening evidence.
- ElevenLabs remains the current provider TTS path. This phase does not change it.

## Side Effects

- model_downloads_performed: false
- provider_calls_made: false
- live_tts_calls_made: false
- local_model_generation_made: false
- runtime_behavior_changed: false
- response_text_changed: false
- raw_private_transcripts_included: false
