# Metric Computation Status

| Dataset/artifact | Metric type | Computed? | Evidence path | Notes |
| --- | --- | --- | --- | --- |
| MELD | MELD row/label statistics | yes | `docs/data/MELD_LABEL_MAPPING.md` | Train rows inspected as 9,989; emotion and sentiment labels listed. |
| Persuasion for Good | Persuasion strategy extraction | inspected/pattern-grounded | `docs/data/DATASETS.md`, `research/experiments/EXP-002-dataset-derived-case-pack.md` | Used for persuasion strategy grounding and success/failure pattern analysis; not commercial sales proof. |
| IEMOCAP | Official audio emotion metrics | no - not computed | `docs/data/DATASETS.md`, `docs/thesis/THESIS_REFERENCE_REGISTRY.md` | Partial/unverified local export; official full corpus use not proven. |
| EASID | EASID feature coverage | no - not computed | `research/experiments/generated/PHASE-4N4-THESIS-EASID-ALIGNMENT-001/` | Schema and synthetic/sanitized examples exist; no actual EASID dataset coverage run. |
| Thesis emotion model | emotion detection accuracy/F1 | no - not computed | none found in inspected files | Do not claim accuracy or F1. |
| LOCAL-QWEN-SFT-DATASET-001 | Qwen SFT row/split counts | yes | `research/experiments/generated/LOCAL-QWEN-SFT-DATASET-001/result.json` | 80 rows; train 60, validation 10, test 10. |
| LOCAL-QWEN-BALANCED-SFT-DATASET-001 | Balanced dataset row/split counts | yes | `research/experiments/generated/LOCAL-QWEN-BALANCED-SFT-DATASET-001/result.json` | 445 rows; train 304, validation 65, test 66, OOD test 10; 10 semantic groups. |
| NON-LLM-ACTION-SELECTOR-DATASET-001 | Non-LLM action-selector dataset stats | yes | `research/experiments/generated/NON-LLM-ACTION-SELECTOR-DATASET-001/result.json` | 451 rows; train 304, validation 65, test 82; 23 labels; no audio data used. |
| NON-LLM-ACTION-SELECTOR-DATA-SOURCES-001 | Usable row/source-role count | yes | `research/experiments/generated/NON-LLM-ACTION-SELECTOR-DATA-SOURCES-001/result.json` | 455 usable training/eval rows; roles include committed sanitized/synthetic rows, benchmark rows, and reference artifacts. |
| PHASE-4N3-WEBSITE-SALES-AGENT-EVALUATION-PROTOCOL-001 | Evaluation protocol counts | yes | `research/experiments/generated/PHASE-4N3-WEBSITE-SALES-AGENT-EVALUATION-PROTOCOL-001/result.json` | 36 cases, 3 variants, 10 scoring dimensions, 11 hard failure flags. |
| ElevenLabs website-sales manual runs | ElevenLabs manual sales effectiveness | no - not computed | none found in inspected 4N3/4N4 files | Protocol exists; scored manual results not present. |
| Website-sales human evaluation | human-likeness scores | no - not computed | `research/experiments/generated/PHASE-4N4-THESIS-EASID-ALIGNMENT-001/11_placeholder_result_tables.md` | Human-likeness table is template only. |
| Website-sales hosted voice package | latency | no - not computed | `research/experiments/generated/PHASE-4N4-THESIS-EASID-ALIGNMENT-001/10_latency_and_real_time_constraints_plan.md` | No provider/model/TTS calls in 4N4, no website-sales latency result. |
| Local Qwen live-action benchmark | local action-selection latency | yes, separate product context | `research/experiments/generated/LOCAL-QWEN-LIVE-ACTION-LATENCY-BENCHMARK-001/result.json` | Local model benchmark was run and target was not met; not website-sales ElevenLabs latency. |
| Local Ollama small-model benchmark | local action-selection latency | yes, separate product context | `research/experiments/generated/LOCAL-OLLAMA-SMALL-LIVE-ACTION-MODEL-BENCHMARK-001/result.json` | Localhost-only benchmark; not provider or hosted website-sales evaluation. |

## Metric Boundary

Rows, splits, labels, and local benchmark timings can be reported only for their own artifacts. They do not imply emotion accuracy/F1, human-likeness, or Atlas website-sales effectiveness.
