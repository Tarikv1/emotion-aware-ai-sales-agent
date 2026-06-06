# ELEVENLABS-012 Web Design Feedback Quality Repair

Package ID: `ELEVENLABS-012-web-design-feedback-quality-repair`

## Decision

This checkpoint converts human feedback from the latest simulation screenshots
into a repo-owned offline repair package. It does not make a live provider call,
does not create new simulation tests, and does not claim production-green
status.

The strongest failure was not that the agent was too formal. The real failure
was that it repeated the same value idea across several turns, gave indirect
assurance when the buyer asked direct trust questions, and used too many words
when the buyer was busy.

One part of the feedback should not be copied literally: adding `haha` or a
scripted chuckle into the text would make the hosted agent sound fake and can
interact badly with voice rendering. The repair therefore encodes no literal
fake laughter. It allows brief human reassurance only when it directly answers
the buyer's concern.

## What This Changes

- `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md`
  adds first-sentence pressure matching, busy-pressure brevity, no literal fake laughter,
  and value-angle exclusivity rules.
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md`
  adds campaign-specific assurance-first wording and a named value-angle
  rotation for Atlas Web Studio.
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md`
  records the approved assurance facts: the mockup is free to review, no
  obligation, no sign-up, and no paid project starts from receiving the link.
- `runtime/providers/elevenlabs_agents/manifests/web_design_feedback_quality_repair.package.json`
  defines the dry-run ElevenLabs package using the current three-layer RAG-022
  document order.
- `scripts/validate_elevenlabs_012_web_design_feedback_quality_repair.py`
  validates the package and dry-run patch bundle without provider calls.

## Repair Targets

- First-sentence pressure matching: when the buyer asks whether there is a
  catch, whether it is really free, whether there are strings attached, or
  whether they are being signed up, the first sentence answers that pressure
  directly.
- Value-angle exclusivity: the agent must not treat organized details, clear
  path, key information, faster first impression, and one place as separate
  sales points when a buyer hears them as the same claim.
- Busy-pressure brevity: when the buyer says they are slammed or asks whether
  the call can wait, the agent moves to callback timing instead of restating
  the value case.
- Assurance without over-talking: the agent can say the mockup is completely
  free to review, no obligation, and no sign-up, then stop or move to the next
  necessary step.

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_012_web_design_feedback_quality_repair.py
```

Build the dry-run agent patch:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --package-manifest runtime\providers\elevenlabs_agents\manifests\web_design_feedback_quality_repair.package.json `
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
  --agent-patch-version-scope "ELEVENLABS-012 web design feedback quality repair" `
  --agent-patch-out research\experiments\generated\ELEVENLABS-012-web-design-feedback-quality-repair\agent_patch_payload.json `
  --out research\experiments\generated\ELEVENLABS-012-web-design-feedback-quality-repair\agent_patch_plan.json `
  --api-requests-out research\experiments\generated\ELEVENLABS-012-web-design-feedback-quality-repair\agent_patch_requests.json
```

## Boundary

- No private customer data is included.
- No API key value is stored in tracked files.
- No live ElevenLabs upload or patch happened in this checkpoint.
- No old ElevenLabs KB document is deleted by this checkpoint.
- The existing V22-or-later simulation surface remains the live evaluation
  target.
- Passing this offline validator is not proof that the hosted agent is fixed.

## Live Result

No live result yet.

The next live gate is explicit upload and patch approval, then a fresh
V22-or-later simulation rerun and human review. Until then this is only an
offline repair package.
