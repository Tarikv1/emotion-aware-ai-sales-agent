# Brain Folder

This folder is the home for the sales-agent brain: the runtime decision architecture, state packet contract, and dialogue-policy evidence.

Start here:

- `BRAIN_001_PROJECT_BRAIN_ARCHITECTURE.md`: what belongs inside the brain and what stays outside it.
- `BRAIN_002_RUNTIME_STATE_SCHEMA.md`: the per-turn state packet contract.
- `PROD_011_DIALOGUE_POLICY_HARDENING.md`: the first hardened policy-action layer over long-call objection evidence.

Related implementation files stay in their existing project locations so validators and command docs remain stable:

- `scripts/brain_runtime_state_schema.py`
- `scripts/dialogue_policy_hardening.py`
- `research/experiments/cases/brain-002-runtime-state-schema.json`
- `research/experiments/cases/prod-011-dialogue-policy-hardening.json`
- `research/experiments/generated/BRAIN-002-runtime-state-schema/`
- `research/experiments/generated/PROD-011-dialogue-policy-hardening/`

Boundary: this folder is not long-term customer memory, raw transcript storage, private audio storage, or a prompt dump. Runtime retrieval remains disabled by default unless a separate RAG gate promotes it.
