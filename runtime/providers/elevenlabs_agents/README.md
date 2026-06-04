# ElevenLabs Agent Packages

This directory holds repo-owned source packages intended for ElevenLabs Agents.

ElevenLabs is treated as the managed runtime and manual upload surface. This
repository remains the source of truth for uploadable knowledge-base documents,
baseline tests, package manifests, prompts, first messages, campaign facts,
policy boundaries, and drift checks.

Default rules:

- No live provider call is made by package generation or validation.
- No provider credential is stored in Markdown, JSON, logs, screenshots, or Git.
- No private customer data, raw customer email, raw transcript, or private audio
  belongs in these tracked package files.
- Universal sales knowledge is advisory and must stay subordinate to campaign
  facts, customer-specific policy, regulated-industry limits, and stop rules.
- Manual dashboard edits must be copied or snapshotted back into the repo before
  they are treated as accepted source material.

Current packages:

- `ELEVENLABS-001-universal-sales-core`: compact universal sales knowledge base
  and baseline test source for future ElevenLabs dashboard/API automation.

