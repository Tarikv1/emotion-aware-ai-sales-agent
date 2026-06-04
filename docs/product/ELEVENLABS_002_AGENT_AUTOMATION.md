# ELEVENLABS-002 Agent Automation

Package ID: `ELEVENLABS-002-agent-automation`

## Decision

Default mode is dry-run.

This checkpoint adds the first repo-owned automation lane for ElevenLabs Agents.
It turns the repo package from `ELEVENLABS-001-universal-sales-core` into an
operator plan and API request bundle for:

- knowledge base file upload
- baseline LLM response test creation
- run-tests request drafting

Live provider writes require `--live` and `--confirm-provider-write`.

This checkpoint does not attach KB documents to an agent automatically.

That is deliberate. The update-agent endpoint supports patching agent settings,
but the safe attach step needs the current copied dashboard JSON config so the
repo can modify the exact agent schema without guessing.

## Commands

Build the dry-run automation plan:

```powershell
python scripts\run_elevenlabs_agent_automation.py --agent-id agent_7801kt0g32zxf4f8x5zkykj7syty
```

Validate the automation lane:

```powershell
python scripts\validate_elevenlabs_002_agent_automation.py
```

Live upload of knowledge base files is gated:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --operation upload-kb `
  --live `
  --confirm-provider-write
```

Live test creation is also gated:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --operation create-tests `
  --live `
  --confirm-provider-write
```

Both live commands require `ELEVENLABS_API_KEY` in the process environment.

## Outputs

- `research/experiments/generated/ELEVENLABS-002-agent-automation/automation_plan.json`
- `research/experiments/generated/ELEVENLABS-002-agent-automation/api_requests.json`

The outputs must not contain API key values, private customer emails, private
transcripts, private audio paths, response-only dashboard metadata, or raw live
provider responses. Live result evidence is reduced to status codes and safe
IDs/summaries.

## Boundary

- Repo remains source of truth.
- ElevenLabs remains managed runtime and dashboard surface.
- Provider calls are default-off.
- API key values are environment-only.
- Customer-specific campaign material needs a separate campaign package and
  privacy review before upload.
- Agent config patching waits for a copied dashboard JSON config snapshot.
