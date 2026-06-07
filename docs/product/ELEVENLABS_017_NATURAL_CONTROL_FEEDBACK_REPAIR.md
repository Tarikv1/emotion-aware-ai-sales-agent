# ELEVENLABS-017 Natural Control Feedback Repair

Package ID: `ELEVENLABS-017-natural-control-feedback-repair`

## Decision

The latest human-reviewed cross-vertical screenshots show that the hosted Atlas
Web Studio agent is closer, but not green:

- some conversations end after the buyer accepts the mockup before the agent
  captures an email or approved send path; these are premature send-path endings
- some final buyer clarifications remain unanswered
- delivery-timing questions can trigger a repeated send-path sentence instead
  of a short repair
- busy callback/email choices are overexplained
- the name-capture rule is too weak and can be skipped
- trust and growth objections need shorter non-guarantee language plus simple
  sensemaking, not long legal-sounding disclaimers
- the universal sales layer needs a compact problem-solution-gain-curiosity
  sequence so the agent creates demand by making the buyer's possible problem
  visible without pretending the problem is proven

This checkpoint repairs those defects in the prompt, the three-layer KB, and the
cross-vertical simulation criteria. It does not approve patient-growth,
more-customer, more-job, call-volume, ranking, SEO, revenue, or booking
guarantees.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_017_natural_control_feedback_repair.py
```

Build the dry-run agent patch and revised simulation-test create requests:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_natural_control_feedback_repair.package.json `
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
  --agent-patch-version-scope "ELEVENLABS-017 natural control feedback repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-017-natural-control-feedback-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-017-natural-control-feedback-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-017-natural-control-feedback-repair\agent_patch_requests.json
```

## Boundary

- No private customer data is included.
- No API key value is stored in tracked files.
- The validator makes no live provider call.
- The old cross-vertical live test folder contains stale criteria until the
  revised V2 test pack is created live.
- The phrase `ethical manipulation` is intentionally not encoded as an agent
  operating rule. The approved behavior is truthful relevance, concise
  perspective-taking, and reversible next steps.
- A fresh live rerun and human review are required before any green or
  production-readiness claim.

## Live Application

Applied live on 2026-06-07 after explicit user request.

- live agent version: `agtvrsn_6701kthngpabe6etedq4rr4a3dpa`
- attached KB document IDs:
  - `7pyke4f9n9casIzeA25x` (`universal_sales_core.md`)
  - `K6xBUXcBoo8cPDvrmCzL` (`atlas_web_studio_web_design_campaign_overlay.md`)
  - `9pv9mi6v2EdWIOUsAzoH` (`atlas_web_studio_web_design_campaign_profile.md`)
- revised V2 simulation folder: `tfld_6201kth9njh3f18rxe63zqd34cgm`
  (`Atlas Web Studio - Cross-Vertical Local Business Simulation V2`)
- revised tests created: 6
- simulation run made: no
- production-green claimed: no
