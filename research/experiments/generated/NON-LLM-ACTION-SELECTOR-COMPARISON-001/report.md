# NON-LLM-ACTION-SELECTOR-COMPARISON-001

- Status: pass
- Non-LLM baseline: rule_based
- Non-LLM p50/p90/p99 ms: 0.2717/0.3519/0.4602
- Small-model p50/p90/p99 ms: 2411.0/2427.0/2435.0
- P50 speedup vs small model: 8873.8x
- Non-LLM test accuracy: 0.9634
- Small-model verifier pass rate: 1.0000
- Reran Ollama: false
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false
- Live runtime wiring allowed: false

## Framing

- Non-LLM selector is not a full conversation brain.
- Non-LLM selector may become a fast proposal layer.
- Response renderer and verifier remain separate.
