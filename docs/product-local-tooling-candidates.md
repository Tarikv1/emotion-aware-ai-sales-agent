# Product-Local Tooling Candidates

## Purpose

This document tracks which workflows should eventually live inside the Emotion Aware AI Sales Agent repo as product-local tooling.

The rule is simple: if a workflow is needed to run, demo, deploy, support, verify, or hand off this product without Tarik's `D:\Codex` workspace, it should live here. If it only helps Codex/Tarik navigate the broader workspace, it should stay in Codex HQ or `D:\Codex\shared`.

External repositories can inspire these workflows, but the promoted product-local version must be minimal, attributed when appropriate, and free of hidden runtime dependencies. See `docs/third-party-inspirations.md`.

## Current Repo Shape

Current product-local executable work is mostly in `scripts/`.

The `apps/`, `services/`, and `packages/shared/` folders are still mostly placeholders. That means the near-term product-local tooling path is probably not a new app yet. It is a small set of stable commands, docs, and validation checks promoted from the existing research/product scripts once they become part of customer or developer setup.

## Candidate List

| Candidate | Current source | Use | Move now? | Recommendation |
| --- | --- | --- | --- | --- |
| Product setup verifier | `scripts/check_setup.py`, `scripts/validate_check_setup.py` | Check Python version, required folders, expected product files, safe write-path signals, and optional provider env vars without printing secrets. | Already product-local. | Keep. Default setup verification must remain offline and no-secret. |
| Product command index | `docs/product/COMMANDS.md` | Give one reliable place to see safe commands for simulation, validation, voice dry-runs, and guarded local servers. | Already product-local. | Keep updated whenever stable product-local scripts are added. |
| Relevant file reader | `scripts/read_relevant.py`, `scripts/validate_read_relevant.py`; workspace-wide sibling in Codex HQ/shared | Read only a line range, query context, outline, or Markdown section from large local files. | Already product-local. | Keep. This is developer support, not runtime logic, but it helps future maintainers work without `D:\Codex\shared`. |
| Local server guard launcher | `scripts/start_guarded_local_server.py`, `docs/product/LOCAL_SERVER_AUTOSTART_GUARDRAILS.md` | Start local demos without hanging Codex or a developer terminal. | Already product-local. | Keep. This belongs in the product repo. |
| Realtime turn CLI | `scripts/realtime_turn_cli.py`, `runtime/entrypoints/REALTIME_TURN_CLI.md` | Exercise the latency-critical sales-agent core one turn at a time. | Already product-local. | Keep and eventually make it the official smoke test for the live core. |
| Product output contract validator | `scripts/product_agent_output_contract.py`, `scripts/validate_product_agent_output_contract.py` | Prevent inconsistent runtime outputs before speaking/logging. | Already product-local. | Keep. This is product logic, not workspace helper tooling. |
| Simulation runners and validators | `scripts/run_product_simulation.py`, `scripts/run_rule_baseline.py`, related `validate_prod_*` scripts | Regress campaign behavior, call-control decisions, and guardrail outcomes. | Already product-local. | Keep. Later wrap the stable subset in one product command. |
| LLM product-agent runner | `scripts/run_llm_product_agent.py` | Test model-backed responses against the same simulation contract. | Already product-local, but gated by API key. | Keep as an explicit opt-in tool. It should never be part of default setup verification. |
| Voice provider readiness gate | `scripts/evaluate_voice_provider_readiness.py`, `docs/product/VOICE_007_PROVIDER_READINESS_GATE.md` | Block unsafe ASR/TTS integration until key, consent, retention, latency, and fallback rules are declared. | Already product-local. | Keep. This is a product safety gate. |
| Voice dry-run/local smoke tools | `VOICE-001` through `VOICE-008` scripts/docs | Validate no-key speech/TTS flows, browser/local paths, latency, and interruption behavior. | Already product-local. | Keep as research-to-product tooling. Mark which commands are no-key and safe-by-default. |
| Live provider smoke tests | `scripts/run_voice_010_cartesia_tts_smoke.py` | Test a real provider only when explicitly allowed. | Already product-local, but live network capable. | Keep, but document as opt-in only. Default validation should use dry-run/fallback mode. |
| Network and secret audit | Codex HQ `audit network` / `audit secrets`; scattered validators already check secret leakage | Detect accidental egress, hardcoded keys, unsafe logging, or customer data upload paths. | Partly. | Create a product-local lightweight audit before any client deployment. Until then, use Codex HQ as internal support. |
| Data/source manifest checker | `docs/data/*`, `data/*`, experiment source labels | Confirm public/private/mixed-source labels and private-data exclusion rules. | Soon. | Medium-high priority. This matters for thesis honesty and client trust. |
| Customer/demo readiness report | Not yet centralized | Generate a human-readable status report for what can be demoed safely. | Not yet. | Medium priority. Useful before sales demos or client review. |
| Deployment preflight | Not yet present | Check production env, provider gates, logging policy, retention policy, DB path, and integration readiness. | Not yet. | Defer until there is a real deploy target. Make it product-local before the first client deployment. |
| Customer onboarding checklist | Not yet present | List installation, env setup, consent, data import, campaign config, and handoff requirements. | Not yet. | Defer until MVP workflow is firmer, then make product-local. |
| RAG/agent diagnostics | Codex HQ `diagnose rag` / `diagnose agent`; product docs mention background modules | Troubleshoot retrieval, memory, tool, or agent failures. | Not yet. | Defer until the product actually uses RAG, memory, or multi-agent runtime modules. |
| Skill improvement workflow | Codex HQ/shared skill logs and proposals | Improve Codex skills after review. | No. | Keep internal. It is not product operation. |
| Workspace memory index/classifier | Codex HQ memory/classify commands | Help Codex navigate Tarik's project universe. | No. | Keep internal. Do not make customer setup depend on it. |

## Product-Local Promotion Rule

Promote a workflow into this repo when at least one of these is true:

- A customer, teammate, or future developer must run it without access to `D:\Codex\active\codex-workspace-dashboard`.
- It verifies product safety, product privacy, or production readiness.
- It is needed for CI, deployment, demo readiness, onboarding, or support.
- It protects runtime behavior, campaign guardrails, provider usage, consent, data usage, or output consistency.
- It produces artifacts that belong to this product's research, thesis, or customer evidence trail.

Keep a workflow outside this repo when:

- It only helps Codex search memory, classify notes, or improve skills.
- It spans multiple unrelated projects.
- It is a temporary internal planning helper.
- It would introduce broad dependencies or workspace assumptions into customer setup.

## Near-Term Recommendation

Do not copy Codex HQ wholesale into this product.

These product-local additions are now present:

1. `scripts/check_setup.py` for safe local setup verification.
2. `docs/product/COMMANDS.md` as the concise product command map.
3. `scripts/read_relevant.py` for safe, bounded local file reading.

The next useful product-local additions are:

1. A lightweight product-local audit that checks for hardcoded secrets, unsafe provider calls, and accidental private-data paths.
2. A data/source manifest checker before larger thesis or client-facing claims.

Those should be implemented only when they become the next active work item. For now, this document is the candidate map.
