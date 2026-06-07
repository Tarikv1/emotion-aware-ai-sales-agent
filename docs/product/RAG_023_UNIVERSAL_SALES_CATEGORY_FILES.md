# RAG-023 Universal Sales Category Files

Package ID: `RAG-023-universal-sales-category-files`

## Decision

The universal sales RAG now has explicit category source files in the repo.
Those category files are the editable source. The uploadable
`runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md`
is the compiled universal layer, not the place to hand-edit long-term content.

This keeps the three-layer contract intact:

```text
Campaign Profile And Facts > Campaign Sales Overlay > Universal Sales RAG
```

Universal category files teach reusable sales method only. They do not own
campaign facts, prices, proof, guarantees, testimonials, or offer-specific
promises.

## What This Changes

- Adds `runtime/sales_knowledge/universal_sales_rag/category_index.json`.
- Adds 21 category files under `runtime/sales_knowledge/universal_sales_rag/categories/`.
- Adds `scripts/compile_universal_sales_rag.py`.
- Adds compiled output at `runtime/sales_knowledge/universal_sales_rag/compiled/universal_sales_core.md`.
- Updates the provider upload artifact at
  `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md`.
- Adds `scripts/validate_rag_023_universal_sales_category_files.py`.

## Categories

- buyer_moves
- buyer_journey_jobs
- buyer_enablement_and_sensemaking
- stakeholder_mapping
- discovery_question_design
- qualification_evidence
- value_and_roi_framing
- objection_status_quo_and_competition
- trust_and_risk_repair
- proof_and_evidence_handling
- conversation_repair
- next_step_policy
- decision_and_paper_process
- negotiation_and_concession_policy
- disqualification_policy
- ethical_persuasion_boundaries
- motion_specific_playbooks
- vertical_general_playbooks
- post_sale_handoff
- success_failure_patterns
- call_quality_rubrics

## Compile Rule

Edit category files first, then compile:

```powershell
python scripts\compile_universal_sales_rag.py
```

Validate:

```powershell
python scripts\validate_rag_023_universal_sales_category_files.py
```

The validator checks category order, required section markers, campaign-fact
leakage, compiled output freshness, provider KB freshness, and hash consistency.

## Live Application

Applied on 2026-06-07 after explicit user request.

Uploaded KB document:

- `universal_sales_core.md`: `4lXSg5OAicFL8XKtxvh9`

Reused existing campaign KB documents from the previous live package:

- `atlas_web_studio_web_design_campaign_overlay.md`: `0VU3KlSbvC0K3LjBQnk8`
- `atlas_web_studio_web_design_campaign_profile.md`: `6nG4gYzwn7YNdTtuwzKQ`

Patched agent:

- agent: `web design`
- agent ID: `agent_7801kt0g32zxf4f8x5zkykj7syty`
- version ID: `agtvrsn_3501ktfp1ne3f85va4z1y4fbzkhb`
- branch ID: `agtbrch_6501kt0g34dvffgr95mvrh70cr2d`
- RAG enabled: `true`
- included prompt repair: `ELEVENLABS-013-send-path-final-confirmation`

Live evidence:

- `research/experiments/generated/RAG-023-universal-sales-category-files/live_upload_plan.json`
- `research/experiments/generated/RAG-023-universal-sales-category-files/live_patch_plan.json`

This live application is provider-write evidence only. It is not proof that the
agent is production-green. A fresh V22-or-later simulation rerun and human review
are still required.

## Boundary

- No live provider call is made by the compiler or validator.
- The 2026-06-07 live application uploaded the compiled universal KB and patched
  the existing `web design` agent after explicit user request.
- No private customer data is included.
- No raw private transcripts or customer audio are included.
- This checkpoint does not claim production-green status.
- The compiled universal layer still stays subordinate to campaign overlay and
  campaign profile facts.
