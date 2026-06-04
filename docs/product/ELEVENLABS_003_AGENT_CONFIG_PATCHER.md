# ELEVENLABS-003 Agent Config Patcher

Package ID: `ELEVENLABS-003-agent-config-patcher`

## Decision

Copied ElevenLabs dashboard JSON is now used as the schema source for safe patch
drafting.

The raw copied config must not be committed when it contains account identity,
access-info, customer data, transcripts, API keys, phone numbers, WhatsApp
accounts, or shareable tokens. The tracked fixture is sanitized.

## What This Adds

The automation runner can now accept:

- a copied/sanitized ElevenLabs agent config
- returned knowledge base document IDs from a prior KB upload
- knowledge base document names

It emits a PATCH payload that:

- preserves the existing first message
- preserves the existing system prompt
- preserves model, voice, turn, ASR, and workflow settings
- attaches the repo-owned KB document under
  `conversation_config.agent.prompt.knowledge_base`
- enables `conversation_config.agent.prompt.rag.enabled`
- omits response-only and identity fields such as `access_info`,
  `creator_email`, phone numbers, WhatsApp accounts, and shareable tokens

## Commands

Validate the patcher without provider calls:

```powershell
python scripts\validate_elevenlabs_003_agent_config_patcher.py
```

Generate a dry-run PATCH payload after a KB upload has returned a document ID:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <returned_knowledge_base_document_id> `
  --kb-document-name universal_sales_core.md `
  --agent-patch-out research\experiments\generated\ELEVENLABS-002-agent-automation\agent_patch_payload.json
```

Live PATCH remains gated:

```powershell
python scripts\run_elevenlabs_agent_automation.py `
  --operation patch-agent `
  --agent-config runtime\providers\elevenlabs_agents\fixtures\web_design_agent_config.sanitized.json `
  --kb-document-id <returned_knowledge_base_document_id> `
  --kb-document-name universal_sales_core.md `
  --live `
  --confirm-provider-write
```

Live PATCH requires `ELEVENLABS_API_KEY` in the process environment.

## Boundary

- The patcher does not invent a new agent.
- The patcher does not overwrite prompt or first-message content.
- The patcher does not upload customer information.
- The patcher does not attach tests automatically; test creation and run-tests
  are separate automation steps.
- The patcher should be rerun with a fresh copied dashboard config after manual
  dashboard edits.
