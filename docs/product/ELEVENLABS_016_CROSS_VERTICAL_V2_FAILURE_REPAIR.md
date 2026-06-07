# ELEVENLABS-016 Cross-Vertical V2 Failure Repair

Package ID: `ELEVENLABS-016-cross-vertical-v2-failure-repair`

## Decision

The live V2 cross-vertical suite after `ELEVENLABS-015` was not green:
`4/6` passed and `2/6` failed.

The failures are narrow enough to repair directly:

- verbal email send-path confirmation: after the buyer gave a clear spoken
  email, the agent did not confirm the send/reply path or close.
- gatekeeper callback-window repair: when a staff member asked when to say the
  owner should call back, the agent deflected to email and invented an
  unapproved found-online email path.

This checkpoint repairs those two defects. It does not broaden the campaign
authority, does not approve found-online email sending, and does not claim
production-green status.

Live V3 evidence then exposed one extra send-path edge: when the buyer asks
whether the link is being sent right now, the agent must answer the timing
directly. The repair now requires present-action wording such as `I'm sending
it now to [email]` before any closing line.

Live V5 evidence showed two evaluator-contract issues rather than new value
argument defects: HVAC must allow a busy buyer to choose an email-send path
instead of a callback, and a hair-salon run should not fail after a complete
present-action send confirmation just because the simulated user asks a
post-close repeat question and then ends before the agent receives another
turn.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_016_cross_vertical_v2_failure_repair.py
```

Build the dry-run agent patch:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_cross_vertical_v2_failure_repair.package.json `
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
  --agent-patch-version-scope "ELEVENLABS-016 cross-vertical V2 failure repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-016-cross-vertical-v2-failure-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-016-cross-vertical-v2-failure-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-016-cross-vertical-v2-failure-repair\agent_patch_requests.json
```

## Boundary

- No private customer data is included.
- No API key value is stored in tracked files.
- The validator makes no live provider call.
- The live V2 suite remains failed evidence, not production-green evidence.
- The first live V3 rerun remained failed evidence (`4/6`) and is stored under
  `research/experiments/generated/ELEVENLABS-016-cross-vertical-v2-failure-repair`.
- Live V4 and V5 also remained `4/6`; they are failed evidence, not green
  evidence.
- Live V6 improved to `5/6` in suite `suite_4001kthb1m7qfjbsb6k1zytzy65r`.
  The remaining failed case is the auto-repair spoken-email terminal turn:
  the simulated user gave `mike at northsideauto dot com` and the harness ended
  before an agent confirmation turn was observed.
- A fresh rerun and human review are required before any green or production
  readiness claim.
