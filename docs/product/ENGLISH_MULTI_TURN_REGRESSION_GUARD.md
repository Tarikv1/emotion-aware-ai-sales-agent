# English Multi-Turn Regression Guard

This is the stable guard command for English deterministic multi-turn runtime behavior.

Run it before editing or promoting English spoken-response behavior, English follow-up routing, callback scheduling behavior, terminal call-control behavior, or broader deterministic English runtime readiness:

```powershell
python scripts\validate_english_multi_turn_regression_guard.py
```

## Scope

The guard wraps `PROD-056-english-post-patch-multi-turn-regression`.

It checks:

- `26` promoted English runtime surfaces
- `10` runtime second-turn follow-up cases
- `1` callback scheduling flow
- `15` terminal-boundary cases
- zero blocking findings
- no provider, LLM, private-data, retrieval, German, voice, payment, contract, or production-promotion boundary drift

## What It Does Not Prove

Passing this guard does not approve:

- native German wording
- voice playback or audio quality
- retrieval defaults
- public demo use
- real customer use
- payment collection
- contract signing
- legal compliance readiness
- provider use or private-data use

Those remain separate review gates.
