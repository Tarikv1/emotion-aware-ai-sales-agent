# RAG-022 Universal Sales Layer Contract

Package ID: `RAG-022-universal-sales-layer-contract`

## Decision

Use a three-layer sales knowledge architecture:

1. Universal Sales RAG
2. Campaign Sales Overlay
3. Campaign Profile And Facts

Universal Sales RAG teaches how to sell. Campaign Sales Overlay teaches how this
campaign should sell. Campaign Profile And Facts owns what is actually true.

The package validator does not make a live provider call. The package is still
dry-run-first by default.

After the offline package was validated, Tarik explicitly requested live upload
and patching on 2026-06-07. That live application uploaded the three layered KB
documents and patched the existing ElevenLabs `web design` agent. It does not
claim simulation-green status.

## Why This Exists

ElevenLabs RAG retrieves relevant chunks from attached documents. It should not
be treated as a deterministic cross-document import system. A campaign profile
can mention universal sales principles, but that is not a reliable instruction
router by itself.

The repo therefore owns the layer contract and compiles a provider package where
the precedence rule is explicit:

```text
Campaign Profile And Facts > Campaign Sales Overlay > Universal Sales RAG
```

## What This Changes

- Adds `runtime/sales_knowledge/universal_sales_rag/layer_contract.json`.
- Adds `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md`.
- Adds `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md`.
- Adds `runtime/providers/elevenlabs_agents/manifests/web_design_layered_sales_package.package.json`.
- Updates `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md` with the three-layer contract and category map.
- Updates `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md` with layer precedence.
- Adds `scripts/validate_rag_022_universal_sales_layer_contract.py`.

## Universal Sales RAG Categories

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

## ElevenLabs Packaging Rule

The layered ElevenLabs package attaches:

- `universal_sales_core.md` as reusable sales method.
- `atlas_web_studio_web_design_campaign_overlay.md` as campaign-specific sales adaptation.
- `atlas_web_studio_web_design_campaign_profile.md` as the highest-authority fact source.

Do not rely on one uploaded document importing another by reference. If a rule is
critical, put the precedence rule in the prompt and package manifest.

## Live Application

Applied on 2026-06-07 after explicit user request.

Uploaded KB documents:

- `universal_sales_core.md`: `p1CtFfTBnhfuewhLn0jP`
- `atlas_web_studio_web_design_campaign_overlay.md`: `npbVIw1kdC32W0UmceM8`
- `atlas_web_studio_web_design_campaign_profile.md`: `SDnLQPveXasZJEqOQA4o`

Patched agent:

- agent: `web design`
- agent ID: `agent_7801kt0g32zxf4f8x5zkykj7syty`
- version ID: `agtvrsn_6601ktfhhm1ge029y9gmv1d2mwp1`
- branch ID: `agtbrch_6501kt0g34dvffgr95mvrh70cr2d`
- RAG enabled: `true`

Live evidence:

- `research/experiments/generated/RAG-022-universal-sales-layer-contract/live_upload_plan.json`
- `research/experiments/generated/RAG-022-universal-sales-layer-contract/live_patch_plan.json`

This live application is provider-write evidence only. It is not proof that the
agent is production-green. A fresh V22-or-later simulation rerun and human review
are still required.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_rag_022_universal_sales_layer_contract.py
```

Build the dry-run agent patch:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_layered_sales_package.package.json `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <universal_sales_core_document_id> `
  --kb-document-name universal_sales_core.md `
  --kb-document-id <campaign_overlay_document_id> `
  --kb-document-name atlas_web_studio_web_design_campaign_overlay.md `
  --kb-document-id <campaign_profile_document_id> `
  --kb-document-name atlas_web_studio_web_design_campaign_profile.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-temperature 0.25 `
  --agent-patch-version-scope "RAG-022 universal sales layer contract" `
  --agent-patch-out research\experiments\generated\RAG-022-universal-sales-layer-contract\agent_patch_payload.json `
  --out research\experiments\generated\RAG-022-universal-sales-layer-contract\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\RAG-022-universal-sales-layer-contract\agent_patch_requests.json
```

## Boundary

- The validator makes no live ElevenLabs API call.
- The 2026-06-07 live application did upload three KB files and patch the
  existing `web design` agent after explicit user request.
- No private customer data is included.
- No API key value is stored in tracked files.
- No customer audio or private transcript is uploaded.
- No old ElevenLabs KB document is deleted.
- Existing V22 simulation evidence remains not production-green until a fresh
  live simulation run proves otherwise.
