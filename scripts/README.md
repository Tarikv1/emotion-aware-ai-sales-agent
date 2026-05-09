# Scripts Folder

This folder contains local project automation. Default scripts should be safe to run offline unless their command docs explicitly require `--live` or provider credentials.

## Script Groups

| Group | Pattern | Purpose |
| --- | --- | --- |
| Setup and guards | `check_*`, `validate_check_setup.py`, `validate_project_drift_guard.py` | Local health, drift, thesis, and privacy checks. |
| Runners | `run_*` | Create checkpoint outputs under `research/experiments/generated/`. |
| Validators | `validate_*` | Check docs, cases, outputs, boundaries, and regression gates. |
| Brain modules | `brain_runtime_state_schema.py`, `dialogue_policy_hardening.py` | Runtime brain state and policy logic. |
| Product modules | `full_*`, `generated_full_call_packets.py`, `product_agent_output_contract.py` | Product decision-layer simulations and output contracts. |
| RAG modules | `rag_*` | Source intake, cleanup, guarded retrieval, and sales-knowledge expansion. |
| Voice/runtime modules | `voice_*`, `runtime_*`, `generate_runtime_*`, provider/prosody/speech modules | Voice delivery, TTS boundaries, listening packets, and runtime delivery previews. |

## Common Commands

```powershell
python scripts\check_setup.py --json
python scripts\check_project_drift.py --json
python scripts\check_thesis_reference_registry.py
python scripts\check_thesis_update_gate.py
```

For checkpoint-specific commands, use `docs/product/COMMANDS.md`.

## Moving Scripts

Many docs and validators reference exact script paths. Before moving a script, update:

- `docs/product/COMMANDS.md`
- `scripts/check_setup.py`
- `scripts/validate_check_setup.py`
- `scripts/check_project_drift.py`
- any checkpoint validator that imports or executes it
