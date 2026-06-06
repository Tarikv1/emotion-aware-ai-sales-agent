# ELEVENLABS-010 Web Design Sales Control Repair

Package ID: `ELEVENLABS-010-web-design-sales-control-repair`

## Decision

The first simulation-test pass was not enough. Human review found four defects:

- the agent kept pitching after an immediate `not interested`
- the agent repeated the same review/send/quick-look close too many times
- website value was too thin because campaign-specific selling points were not separated from universal method
- direct cost questions, especially hosting, were sometimes dodged until the buyer asked repeatedly
- terminal turns often lacked a natural closing line
- unapproved bracketed delivery tags and content-like tags can clutter text transcripts
- gatekeeper simulations could pass even when the agent asked the staff member
  what the caller should tell the owner, which is a role-flipped conversation

This checkpoint is a human-reviewed simulation repair. It keeps ElevenLabs as
the voice host and dashboard runtime, while keeping the repo as the source of
truth.

## What This Changes

- `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core.md`
  now has stricter refusal, sales rhythm, campaign-value-use, and upsell discipline.
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign.md`
  adds Atlas Web Studio website-specific value points and keeps them out of the
  universal core: owner control, menu scanability, staff-time reduction, one
  shareable link, first-time visitor clarity, optional future scope, pricing,
  and hosting boundaries.
- `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md`
  now blocks repeated closes, immediate-refusal pitching, internal self-talk,
  hosting-cost dodging, evasive future-pitch answers, missing terminal closings,
  unapproved bracketed delivery tags, and gatekeeper role-flip questions.
- `runtime/providers/elevenlabs_agents/automation.py` now uses same-name KB replacement
  when attaching newly uploaded docs, so stale same-name attached docs are not
  kept beside the current version.
- `runtime/providers/elevenlabs_agents/tests/web_design_mikes_kitchen_simulation_tests.json`
  now includes stricter success criteria and an optional booking future-scope
  scenario.

## RAG Diagnosis

The live agent was attached to one `universal_sales_core.md` document, but the
workspace knowledge-base inventory contained multiple historical uploads with
the same name. The dashboard source panel can also show multiple chunks from
one attached document. That means duplicate names in the workspace are real, but
the immediate behavior fix is to attach the current repo-owned documents and
avoid stale same-name attachments.

Deleting old ElevenLabs knowledge-base documents is intentionally not part of
this checkpoint because it is destructive and may affect other dashboard
experiments.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_010_web_design_sales_control_repair.py
```

Build the dry-run agent patch:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_sales_control_repair.package.json `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <universal_sales_core_document_id> `
  --kb-document-name universal_sales_core.md `
  --kb-document-id <atlas_web_studio_campaign_document_id> `
  --kb-document-name atlas_web_studio_web_design_campaign.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-temperature 0.25 `
  --agent-patch-version-scope "ELEVENLABS-010 web design sales control repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-010-web-design-sales-control-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-010-web-design-sales-control-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-010-web-design-sales-control-repair\agent_patch_requests.json
```

## Boundary

- No private customer data is included.
- No API key value is stored in tracked files.
- No old ElevenLabs KB document is deleted.
- Audio tags remain a separate voice-delivery experiment. This checkpoint does
  not make approved delivery tags the main sales-quality pass/fail criterion,
  but it still blocks unapproved bracketed delivery tags, tag spam, content-like
  tags, and fake reactions in conversation text.
- Passing simulations is still not proof of production outbound quality.

## Live Result

Patched and rerun on 2026-06-06:

- live universal KB: `BcBNsi1ixg9pOsY4pRPE`
- live Atlas campaign KB: `sIrXtflwhwf3WdOg7Blg`
- repaired simulation folder: `Atlas Web Studio - Mike's Kitchen Simulation Repair V22`
- previous clean simulation folder: `Atlas Web Studio - Mike's Kitchen Simulation Repair V17`
- repaired simulation folder ID: `tfld_2101ktd8d310f1basthjk2tqjcm7`
- repaired simulation suite: `suite_9101ktd8q9r1fc1rc7tecszbyj0h`
- result: `7/9` simulation tests passed; not production-green
- latest live prompt patch: `agent_patch_v22d_plan.json`, a narrow gatekeeper wording patch that changes the remaining `try after three` language to direct call-back wording
- remaining failures: plain-language abstract wording and social-objection value-rotation/send-closing instability
- sanitized summary: `research/experiments/generated/ELEVENLABS-010-web-design-sales-control-repair/sales_control_repair_results_summary.json`

Intermediate repair runs were not hidden. They exposed repeated-close failures
on skeptical-owner and social-presence objections, a gatekeeper note that was
too detailed, one unreachable late do-not-call simulation artifact, and a
persistent social-channel objection loop where the agent kept repeating the
same product checklist. V17 was a clean run under an older evaluator. V22 is
stricter and better aligned with human review, but the current V22c run still
has two failures and must not be treated as production-ready. V22d was a
patch-only live agent update after that run; it did not rerun the simulation
suite and does not change the 7/9 evidence.
