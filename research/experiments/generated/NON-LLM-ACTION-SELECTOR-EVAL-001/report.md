# NON-LLM-ACTION-SELECTOR-EVAL-001

- Status: pass
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false
- Live runtime wiring allowed: false
- Runtime behavior changed: false
- Response text changed: false

## Baselines

### rule_based
- Validation accuracy: 0.9538
- Test accuracy: 0.9634
- Validation macro F1: 0.7802
- Test macro F1: 0.8485
- Latency ms p50/p90/p99/max: 0.2717/0.3519/0.4602/0.6099
- Test fallback rate: 0.0122

### sklearn_tfidf_logistic_regression
- Validation accuracy: 0.6308
- Test accuracy: 0.5610
- Validation macro F1: 0.3892
- Test macro F1: 0.3913
- Latency ms p50/p90/p99/max: 0.4204/0.4800/0.5303/0.6735
- Test fallback rate: 0.0000
