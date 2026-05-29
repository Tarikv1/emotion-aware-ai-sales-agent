# NON-LLM-ACTION-SELECTOR-EVAL-001

- Status: pass
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama calls: false
- Live runtime wiring allowed: false
- Runtime behavior changed: false
- Response text changed: false

## Baselines

### rule_based
- Validation accuracy: 0.9538
- Test accuracy: 0.9512
- Validation macro F1: 0.7802
- Test macro F1: 0.8268
- Latency ms p50/p90/p99/max: 0.2473/0.3565/0.4983/0.5429
- Test fallback rate: 0.0244

### sklearn_tfidf_logistic_regression
- Validation accuracy: 0.6308
- Test accuracy: 0.5610
- Validation macro F1: 0.3892
- Test macro F1: 0.3913
- Latency ms p50/p90/p99/max: 0.4152/0.5538/0.8119/0.8635
- Test fallback rate: 0.0000
