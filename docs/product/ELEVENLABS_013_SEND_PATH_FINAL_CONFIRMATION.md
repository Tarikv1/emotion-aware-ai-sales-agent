# ELEVENLABS-013 Send-Path Final Confirmation

Package ID: `ELEVENLABS-013-send-path-final-confirmation`

## Decision

This is a narrow repair for the latest failed simulation screenshot. After the
agent confirmed the send path and closed, the buyer asked a final send-path
clarification: whether they would get an email with the sample-page link. The
agent should answer that yes/no clarification once, close, and stop.

This checkpoint does not add a broader conversation loop. The correct behavior
is a one-line terminal answer, not a new pitch.

## Repair Target

This repair is for final send-path clarification only.

Final send-path clarification after the send path is already known:

```text
Buyer: Ok so I'll get an email with a link to the sample page, yeah?
Agent: Yes, I'll send the email with the mockup link. Have a good one.
```

The agent must not reopen website value, ask another question, or repeat the
full send-path explanation.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_013_send_path_final_confirmation.py
```

Build the dry-run agent patch:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_send_path_final_confirmation.package.json `
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
  --agent-patch-version-scope "ELEVENLABS-013 send-path final confirmation" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-013-send-path-final-confirmation\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-013-send-path-final-confirmation\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-013-send-path-final-confirmation\agent_patch_requests.json
```

## Boundary

- No private customer data is included.
- No API key value is stored in tracked files.
- The initial validator makes no live provider call.
- The prompt repair was applied live on 2026-06-07 together with
  `RAG-023-universal-sales-category-files`.
- Live patched agent version: `agtvrsn_3501ktfp1ne3f85va4z1y4fbzkhb`.
- This repair does not claim production-green status.
- A fresh V22-or-later simulation rerun and human review are still required.
