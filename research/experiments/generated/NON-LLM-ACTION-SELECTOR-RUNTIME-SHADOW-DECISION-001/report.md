# NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-DECISION-001

- Status: pass
- Recommendation: add_runtime_action_metadata_extraction_before_real_runtime_comparison
- Detail: Offline replay is safety-clean, but runtime action IDs are still unavailable; add runtime action metadata extraction before claiming real runtime agreement.
- Replay cases: 147
- Runtime action ID available count: 0
- Agreement/compatible with expected: 141/144
- Possible improvement/regression: 0/1
- Safety blockers: 0
- Latency p50/p90/p99 ms: 1.8480/2.0955/2.6821
- Live wiring allowed: false
- Response text changed: false
- Runtime behavior changed: false
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false
