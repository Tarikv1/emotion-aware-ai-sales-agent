# 4M0 ElevenLabs Dashboard Setup Checklist

Purpose: configure a manual ElevenLabs Agent prototype for public ChatGPT plan-fit guidance without enabling provider calls, tools, payment, account changes, email, calendar, or CRM side effects from this repo.

## Pre-upload gates

- Confirm this package is from `PHASE-4M0-ELEVENLABS-DOCS-COMPATIBLE-UPLOAD-PACKAGE-001`.
- Use the current 4L5 source bundle as truth; do not refresh OpenAI plan facts in this phase.
- Confirm no OpenAI API, ElevenLabs API, model, TTS, CRM, email, calendar, payment, or account call was made to create the package.
- Confirm the package contains no raw private transcript, private audio, provider secret, token, API key, customer account data, or raw evidence dump.
- Keep every future tool disabled during 4M0 setup.

## Agent configuration

- Paste `01_agent_system_prompt.md` into the ElevenLabs Agent system prompt field.
- Keep the agent identity as a public-data plan-fit guide, not an official OpenAI representative.
- Configure the first workflow branch from `02_workflow_branch_spec.md` manually if using the workflow builder.
- Do not configure custom LLM in 4M0.
- Do not configure tools in 4M0 unless a later reviewed phase explicitly enables a read-only tool.

## Knowledge base upload

- Upload concise KB Markdown files `03` through `11` as document files.
- Use Prompt mode only for short guardrail-critical material if dashboard limits allow it.
- Use Auto/RAG mode for plan facts, allowed claims, sales playbooks, objections, persuasion, buyer state, repair, and side-effect safety.
- Do not upload `12_tool_contracts_read_only.md` unless tools are being configured in a later phase.
- Do not upload `13_manual_eval_script.md`; use it for human testing only.
- Do not upload `15_elevenlabs_documentation_alignment.md`; keep it as reference.

## Conversation analysis setup

- Track manual ratings for spoken naturalness, sales usefulness, source safety, and side-effect safety.
- Add analysis tags for plan fit, claim boundary, side-effect refusal, repeated-question repair, buyer state, and self-serve/contact-sales route.
- Do not export raw private audio or raw private transcript into public evidence.

## Manual launch gate

- A pass means the package is ready for manual ElevenLabs dashboard upload and testing only.
- A pass is not live readiness.
- A pass does not enable selector control, response replacement, provider calls, tools, payment, CRM, email, calendar, or account changes.
