# ELEVENLABS-011 Web Design Remaining Simulation Repair

Package ID: `ELEVENLABS-011-web-design-remaining-simulation-repair`

## Decision

The next useful step is not another random rerun. The previous evidence says
V22c remains `7/9`, and V22d was patch-only for gatekeeper callback wording.
This checkpoint repairs the two remaining V22 failure modes in repo-owned source
files and keeps the live provider update as an explicit later action.

This checkpoint does not make a live provider call, does not create new
simulation tests, and does not claim production-green status.

## What This Changes

- `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md`
  adds a remaining V22 repair section for plain-language abstract wording,
  send-path acknowledgment closing, and social-objection value rotation.
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign.md`
  updates the package marker and adds concrete repair examples for normal-word
  answers and Instagram/Google Maps value rotation.
- `runtime/providers/elevenlabs_agents/variables/mikes_kitchen_dynamic_variable_defaults.json`
  removes direction-heavy default phrasing from interpolated campaign values.
- `runtime/providers/elevenlabs_agents/manifests/web_design_remaining_simulation_repair.package.json`
  defines the offline repair package for a future ElevenLabs KB upload and agent
  patch.
- `scripts/validate_elevenlabs_011_web_design_remaining_simulation_repair.py`
  validates the offline package and dry-run patch bundle without provider calls.

## Repair Targets

The source failures from `ELEVENLABS-010` were:

- `sim_plain_language_confused_buyer`: plain-language abstract wording such as
  potential direction, plus a late send-path closing miss.
- `sim_social_presence_objection`: social-objection value rotation collapsed back
  into practical-detail repetition and missed a final send/reply closing.

The repair deliberately avoids adding broader sales features. It only tightens
the instructions that map to those two failures.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_011_web_design_remaining_simulation_repair.py
```

Build the dry-run agent patch:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_remaining_simulation_repair.package.json `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <universal_sales_core_document_id> `
  --kb-document-name universal_sales_core.md `
  --kb-document-id <atlas_web_studio_campaign_document_id> `
  --kb-document-name atlas_web_studio_web_design_campaign.md `
  --agent-prompt-file runtime\providers\elevenlabs_agents\prompts\web_design_atlas_sales_prompt.md `
  --first-message-file runtime\providers\elevenlabs_agents\prompts\web_design_first_message.txt `
  --dynamic-variable-defaults runtime\providers\elevenlabs_agents\variables\mikes_kitchen_dynamic_variable_defaults.json `
  --agent-temperature 0.25 `
  --agent-patch-version-scope "ELEVENLABS-011 web design remaining simulation repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-011-web-design-remaining-simulation-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-011-web-design-remaining-simulation-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-011-web-design-remaining-simulation-repair\agent_patch_requests.json
```

## Boundary

- No private customer data is included.
- No API key value is stored in tracked files.
- No live provider write happened in this checkpoint.
- No old ElevenLabs KB document is deleted.
- The existing V22 simulation pack remains the evaluation target.
- Passing the offline validator is not proof that the live dashboard agent is
  fixed.

## Live Result

No live result yet.

The latest recorded live evidence is still:

- previous suite: `Atlas Web Studio - Mike's Kitchen Simulation Repair V22`
- previous suite ID: `suite_9101ktd8q9r1fc1rc7tecszbyj0h`
- previous result: `7/9` simulation tests passed
- production-green: `false`
- latest live patch before this checkpoint: V22d gatekeeper wording only

The next live gate is to upload the current repo-owned KB docs, patch the live
`web design` agent with the 011 prompt, and rerun the V22-or-later simulation
suite. Until that happens, this checkpoint is only an offline repair package.
