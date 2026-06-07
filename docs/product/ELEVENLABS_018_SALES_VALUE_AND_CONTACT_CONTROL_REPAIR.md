# ELEVENLABS-018 Sales Value And Contact Control Repair

Package ID: `ELEVENLABS-018-sales-value-and-contact-control-repair`

## Decision

The latest human-reviewed cross-vertical screenshots show that `ELEVENLABS-017`
did not fully fix the real failure:

- website value answers still leaned on weak phrases like "clearer page",
  "something to judge", or long non-guarantee disclaimers
- the agent still skipped name capture in normal owner/manager calls
- some conversations still ended after a buyer accepted the mockup or gave an
  email before the send/reply path was confirmed
- a buyer-instructed public Facebook lookup was hard-refused even though this
  campaign can treat it as a post-call handoff

This checkpoint makes the campaign value sharper without making unsafe claims.
The approved shape is: short no, then a supported mechanism. Example:
`No, I can't promise that. What it can do is support local visibility with an
owned, indexable page people can check from Google or social before deciding who
to call.`

It still does not approve more-customer, more-patient, more-job, call-volume,
ranking, SEO, revenue, booking, or treatment-result guarantees.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_018_sales_value_and_contact_control_repair.py
```

Build the dry-run agent patch and revised V3 simulation-test create requests:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_sales_value_and_contact_control_repair.package.json `
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
  --agent-patch-version-scope "ELEVENLABS-018 sales value and contact control repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-018-sales-value-and-contact-control-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-018-sales-value-and-contact-control-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-018-sales-value-and-contact-control-repair\agent_patch_requests.json
```

## Boundary

- No private customer data is included.
- No API key value is stored in tracked files.
- The validator makes no live provider call.
- Public-profile contact lookup is only a buyer-instructed public business
  source handoff. It is not permission to claim an email was found or sent.
- `ethical manipulation` is not encoded as an agent rule. The approved control
  style is truthful relevance, sharper value mechanism, concise name capture,
  and reversible next steps.
- A fresh live rerun and human review are required before any green or
  production-readiness claim.

## Live Application

Applied live on 2026-06-07 after explicit user request.

- live agent version: `agtvrsn_8901kthty7p4e69v6pk3ybnve233`
- attached KB document IDs:
  - `JF3WSPRZOcPS1rki03ot` (`universal_sales_core.md`)
  - `nDldYVCnhKzj4mKW4X4O` (`atlas_web_studio_web_design_campaign_overlay.md`)
  - `sxG793M1gBKfJxzgUWIO` (`atlas_web_studio_web_design_campaign_profile.md`)
- revised V3 simulation folder: `tfld_3501ktha7vdsekeshx4m9wajkhhv`
  (`Atlas Web Studio - Cross-Vertical Local Business Simulation V3`)
- revised tests created: 6
- simulation run made: no
- production-green claimed: no
