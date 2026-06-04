# ELEVENLABS-006 Web Design Naturalness Patch

Package ID: `ELEVENLABS-006-web-design-naturalness-patch`

## Decision

The scenario failures were not only test-definition issues.

The live ElevenLabs agent prompt had drifted to `You are a helpful assistant.`,
so the model was relying on chat history and RAG instead of a real Atlas Web
Studio sales-agent instruction.

## Critique From Test Results

- `visual representation of a potential homepage` sounds like brochure copy.
- `potential improvement to your online presence` is generic and less useful
  than naming menu, hours, location, and reservation calls.
- `how customers interact with your website` is wrong when the prospect has no
  full website known.
- `customer action path` is internally useful but customer-facing jargon; say
  menu, hours, location, and reservation phone path instead.
- The failed mockup-content answer did not ask whether reviewing the mockup
  would be useful.
- The failed callback answer said `share the mockup idea`, which is too vague;
  it should name the review purpose.

## What This Adds

- `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md`
- `runtime/providers/elevenlabs_agents/prompts/web_design_first_message.txt`
- `runtime/providers/elevenlabs_agents/variables/mikes_kitchen_dynamic_variable_defaults.json`
- automation support for `--agent-prompt-file`, `--first-message-file`, and
  `--dynamic-variable-defaults`
- `scripts/validate_elevenlabs_006_web_design_naturalness_patch.py`

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_006_web_design_naturalness_patch.py
```

Draft the prompt PATCH payload:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id OyjSKNJnQTc84pyk1Yu0 `
  --kb-document-name universal_sales_core.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-patch-out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\api_requests.json
```

Live PATCH remains gated:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --operation patch-agent `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id OyjSKNJnQTc84pyk1Yu0 `
  --kb-document-name universal_sales_core.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-patch-out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\automation_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-006-web-design-naturalness-patch\api_requests.json `
  --live `
  --confirm-provider-write
```

## Boundary

- No new KB document is uploaded.
- No customer private data is used.
- The patch changes prompt, first message, dynamic variable placeholders, and
  preserves the existing KB attachment.
- Test output and provider responses must remain safe summaries only.

## Live Result

Run date: 2026-06-04

- Live agent PATCH applied to `agent_7801kt0g32zxf4f8x5zkykj7syty`.
- Read-back confirmed prompt length `3412`, first message override, Mike's
  Kitchen dynamic placeholders, KB document `OyjSKNJnQTc84pyk1Yu0`, and RAG
  enabled.
- Scenario rerun suite `suite_6901kt9w3km8eera53zy0ykagjee` passed all six
  `ELEVENLABS-005` Mike's Kitchen scenario tests.
