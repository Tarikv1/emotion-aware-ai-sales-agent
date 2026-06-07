# ELEVENLABS-015 Cross-Vertical Feedback Repair

Package ID: `ELEVENLABS-015-cross-vertical-feedback-repair`

## Decision

The latest cross-vertical screenshots exposed two separate issues.

The narrow evaluator issue is that `menu` was treated as restaurant leakage even
when the agent meant a salon service menu or pricing menu. The broader agent
issue is more important: the agent still falls back to one repeated website
selling point instead of using a deeper local-business value library.

This checkpoint repairs both without approving unsafe claims. The agent may use
safe local visibility language, owned-page trust framing, service/pricing
clarity, one shareable link, proof-before-purchase, and controlled next-step
movement. It must not promise rankings, traffic, leads, bookings, revenue, or
more customers.

## Repair Scope

- service menu evaluator repair: service menu or pricing menu is not restaurant
  leakage; food menu, tables, reservations, and food ordering are.
- safe local visibility: a website can support local visibility through an
  owned, indexable page, but no ranking or customer-growth guarantee is approved.
- name capture: ask who the owner or manager is when it is natural, but do not
  interrupt busy, gatekeeper, refusal, or direct-objection turns.
- contractions: prefer spoken forms like `it's`, `I'll`, `don't`, `can't`, and
  short guarantee boundaries like `I can't promise that.`
- callback number gap: if no callback number is configured, do not invent one.
- ethical persuasion, not manipulation: answer the concern, bridge to one
  truthful value angle, and guide only to a valid next step.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_015_cross_vertical_feedback_repair.py
```

Build the dry-run agent patch:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_cross_vertical_feedback_repair.package.json `
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
  --agent-patch-version-scope "ELEVENLABS-015 cross-vertical feedback repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-015-cross-vertical-feedback-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-015-cross-vertical-feedback-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-015-cross-vertical-feedback-repair\agent_patch_requests.json
```

## Boundary

- No private customer data is included.
- No API key value is stored in tracked files.
- The validator makes no live provider call.
- This checkpoint does not claim production-green status.
- A live patch, fresh cross-vertical simulation rerun, and human transcript
  review are still required before treating the agent as improved in ElevenLabs.
