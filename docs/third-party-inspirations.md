# Third-Party Inspirations

## Purpose

This document tracks external repositories, provider documentation, and tool ideas that affected the Emotion Aware AI Sales Agent product/thesis project.

Entries here do not make any source a product runtime dependency. The product architecture remains:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + explicit guardrails, consent, provider gates, and human escalation paths
```

## 1jehuang/jcode

- Source: https://github.com/1jehuang/jcode
- License observed: MIT.
- Checked: 2026-05-02. Security audit source notes: `D:\Codex\shared\docs\jcode-security-audit.md`.
- Reuse label: adapted pattern.
- What we learned/adapted:
  - The useful idea was bounded context reading: outline a large file, read only a line range, find a query with nearby context, or extract a Markdown section.
  - We also kept the broader lesson that high-performance agent tools can be useful as references without becoming trusted runtime dependencies.
- Directly copied material: none. No Jcode code, installer, telemetry, provider, OAuth, update, MCP, browser, or notification code was copied.
- Where it affected the Emotion Aware project:
  - `scripts/read_relevant.py`
  - `scripts/validate_read_relevant.py`
  - `docs/product/COMMANDS.md`
  - `docs/product-local-tooling-candidates.md`
- Product/runtime boundary:
  - Developer support only.
  - Not part of the sales-agent runtime.
  - Not required by customers unless they are developing inside this repo.
- Security/privacy notes:
  - The local reader is offline and read-only.
  - It blocks `.git`, `.tmp`, `private-restricted`, env files, token/credential/key-like paths, and certificate-like files.
  - Jcode itself remains reference/sandbox only for this workspace.
- Follow-up:
  - Keep the local reader small.
  - Do not import Jcode runtime features without a separate security review.

## karpathy/autoresearch

- Source: https://github.com/karpathy/autoresearch
- License observed: MIT.
- Checked: 2026-05-02. Workspace source notes: `D:\Codex\shared\docs\autoresearch-patterns.md`.
- Reuse label: adapted pattern.
- What we learned/adapted:
  - Baseline first.
  - One narrow hypothesis.
  - One editable surface.
  - Fixed evaluation budget.
  - Results log.
  - Keep, revise, or discard based on evidence.
  - Penalize complexity unless the gain is meaningful.
- Directly copied material: none.
- Where it affected the Emotion Aware project:
  - `program.md`
  - `research/experiments/EXPERIMENT_TEMPLATE.md`
  - product/thesis experiment style across `research/experiments/`
  - repeatable simulation and validation workflow in `scripts/`
- Product/runtime boundary:
  - Process discipline only.
  - No unattended autonomous research loop was added.
  - No product runtime self-modification was added.
- Security/privacy notes:
  - Experiments stay bounded and reviewable.
  - Private data still follows `docs/data/DATA_USAGE_POLICY.md`.
- Follow-up:
  - Keep using this as methodology inspiration for sales-agent evaluations.
  - Do not add autonomous self-improvement loops without explicit review and rollback design.

## Shubhamsaboo/awesome-llm-apps

- Source: https://github.com/Shubhamsaboo/awesome-llm-apps
- License observed: Apache-2.0.
- Checked: 2026-05-02. Local checkout license observed at `D:\Codex\shared\repo-research\awesome-llm-apps\LICENSE`.
- Reuse label: adapted pattern.
- What we learned/adapted:
  - The sales intelligence agent team pattern was rewritten into a proof-backed battle-card workflow.
  - Useful pieces: competitor research, feature analysis, positioning analysis, SWOT, objection handling, source-backed responses, and a do-not-claim list.
- Directly copied material: none. The Emotion Aware blueprint was rewritten in this project style.
- Where it affected the Emotion Aware project:
  - `docs/battle-card-agent-blueprint.md`
  - `docs/open-source-agent-inspiration.md`
- Product/runtime boundary:
  - Documentation/blueprint only.
  - No `awesome-llm-apps` template, dependency, agent runtime, or API integration was imported.
  - Battle cards must support the reusable sales-agent core and active SalesCampaign facts rather than create a separate autonomous sales agent.
- Security/privacy notes:
  - Battle-card outputs require source URLs next to claims.
  - Human review is required before external use.
  - No scraping, login automation, CRM access, or customer data ingestion was added from this source.
- Follow-up:
  - If battle-card generation becomes executable, keep it local, source-cited, and review-gated.

## safishamsi/graphify

- Source: https://github.com/safishamsi/graphify
- License observed: MIT.
- Checked: 2026-05-02.
- Reuse label: inspiration only.
- What we learned/adapted:
  - Graph-style project memory can separate extracted facts, inferred relationships, confidence, and source paths.
  - This is useful for making lead, objection, campaign, and emotional-signal reasoning explainable.
- Directly copied material: none.
- Where it affected the Emotion Aware project:
  - `docs/open-source-agent-inspiration.md`
  - long-range thinking about explainable project memory and source-linked reasoning.
- Product/runtime boundary:
  - Not installed in the Emotion Aware repo.
  - Not a customer dependency.
  - Not part of the live sales-agent core.
- Security/privacy notes:
  - Future graph runs must not ingest secrets, raw private transcripts, customer exports, or restricted local data.
  - Any graph tool that uses an LLM/API must be reviewed for what leaves the machine.
- Follow-up:
  - Revisit only after the project has enough product docs, campaign configs, and safe synthetic data to make a graph useful.

## jamiepine/voicebox

- Source: https://github.com/jamiepine/voicebox
- License observed: MIT.
- Checked: 2026-05-02.
- Reuse label: inspiration only.
- What we learned/adapted:
  - Voice workflows should track profiles, provenance, versions, effects, queueing, and local-first privacy boundaries.
  - Voice cloning and generated speech require explicit consent and clear ownership.
- Directly copied material: none.
- Where it affected the Emotion Aware project:
  - `docs/open-source-agent-inspiration.md`
  - voice consent and provenance caution in the VOICE milestone direction.
- Product/runtime boundary:
  - Not installed.
  - Not a voice runtime dependency.
  - The current product voice path remains adapter-based around the reusable sales-agent core.
- Security/privacy notes:
  - Do not clone real customer, employee, or third-party voices.
  - Do not store raw private audio in the repo.
  - Generated audio must remain clearly separated from source audio.
- Follow-up:
  - If local voice synthesis becomes relevant, define consent, retention, profile ownership, and disclosure rules before any implementation.

## microsoft/VibeVoice

- Source: https://github.com/microsoft/VibeVoice
- License observed: MIT.
- Checked: 2026-05-02. Workspace source notes: `D:\Codex\shared\docs\vibevoice-opportunity-notes.md`.
- Reuse label: avoid until reviewed.
- What we learned/adapted:
  - VibeVoice-ASR is a useful future ASR candidate for long-form, speaker-aware, timestamped transcripts and hotword/domain vocabulary support.
  - TTS and realtime voice claims are interesting but high-risk for a sales-agent product.
- Directly copied material: none.
- Where it affected the Emotion Aware project:
  - future voice-agent research notes
  - no-key-first voice milestone posture
  - caution around commercial/realtime voice use
- Product/runtime boundary:
  - Not installed.
  - Not used by the current voice scripts.
  - Not approved for production or customer deployment.
- Security/privacy notes:
  - Treat as research/dev-only until tested on non-sensitive audio.
  - Do not use for voice cloning, impersonation, or real customer audio without consent and retention review.
  - Generated or transformed audio must be disclosed when shared.
- Follow-up:
  - If evaluated later, start with a small local test on non-sensitive audio and compare against simpler ASR options.

## NousResearch/hermes-agent

- Source: https://github.com/NousResearch/hermes-agent
- License observed: MIT.
- Checked: 2026-05-02.
- Reuse label: inspiration only.
- What we learned/adapted:
  - Useful architecture vocabulary: skills, plugins, tools, context files, memory, scheduled work, and explicit safety boundaries.
  - Reinforced the need to separate platform/agent infrastructure from the product's live response path.
- Directly copied material: none.
- Where it affected the Emotion Aware project:
  - `docs/open-source-agent-inspiration.md`
  - product architecture caution around agent platforms and memory.
- Product/runtime boundary:
  - Not installed.
  - Not used as an agent runtime.
  - The Emotion Aware product still uses one fast sales-agent core plus optional background modules, not a large always-on agent platform.
- Security/privacy notes:
  - Do not add hidden memory or messaging integrations.
  - Do not add unattended scheduled actions that call, message, publish, or edit without review.
- Follow-up:
  - Keep as a reference for future internal developer tooling only.

## facebookresearch/tribev2

- Source: https://github.com/facebookresearch/tribev2
- License observed: CC-BY-NC-4.0.
- Checked: 2026-05-02.
- Reuse label: avoid until reviewed.
- What we learned/adapted:
  - Multimodal emotional or response signals can be time-aligned across language, audio, and visual context.
  - This is useful research framing for long-range multimodal emotion work.
- Directly copied material: none.
- Where it affected the Emotion Aware project:
  - `docs/open-source-agent-inspiration.md`
  - long-range framing for `docs/architecture/VOICE_FEATURE_MODULE.md`.
- Product/runtime boundary:
  - Not installed.
  - Not used as product code.
  - Not suitable for commercial product reuse without a separate license review because of the non-commercial license.
- Security/privacy notes:
  - Do not use TRIBE v2 code, weights, or data in a commercial product path unless licensing is resolved.
  - Treat it as research inspiration only.
- Follow-up:
  - Keep as background research vocabulary, not implementation material.

## Official TTS Provider Sources For VOICE-009

- Source:
  - Cartesia docs: https://docs.cartesia.ai/
  - Cartesia Sonic 3 docs: https://docs.cartesia.ai/build-with-cartesia/tts-models/sonic-3
  - Cartesia realtime TTS quickstart: https://docs.cartesia.ai/get-started/realtime-text-to-speech-quickstart
  - Cartesia WebSocket API: https://docs.cartesia.ai/api-reference/tts/websocket
  - Cartesia pricing: https://cartesia.ai/pricing
  - ElevenLabs docs/product pages, OpenAI audio/TTS docs, Azure Speech docs, Google Cloud TTS docs, AWS Polly docs, Deepgram docs, and Piper GitHub sources are listed in `research/experiments/cases/voice-009-tts-provider-research.json`.
- License observed: official/provider documentation and product terms; not treated as open-source code. Piper source licenses were not adopted into runtime code.
- Checked: 2026-05-02. Project source list retrieved on 2026-05-01 in `VOICE-009`.
- Reuse label: adapted pattern.
- What we learned/adapted:
  - Use a provider-readiness matrix before adding any SDK, API key, or live audio path.
  - Score providers for German/English support, streaming, latency, sales-voice controls, privacy/key safety, telephony readiness, and fallback behavior.
  - Select Cartesia Sonic 3 as the first guarded TTS smoke candidate, not as a launch-approved provider.
- Directly copied material: none. Provider facts were summarized into project-owned JSON/Markdown reports.
- Where it affected the Emotion Aware project:
  - `docs/product/VOICE_009_TTS_PROVIDER_RESEARCH.md`
  - `docs/product/VOICE_010_CARTESIA_TTS_SMOKE_TEST.md`
  - `docs/product/VOICE_011_CARTESIA_WEBSOCKET_SMOKE_TEST.md`
  - `scripts/evaluate_voice_009_tts_provider_research.py`
  - `scripts/run_voice_010_cartesia_tts_smoke.py`
  - `scripts/run_voice_011_cartesia_websocket_smoke.py`
  - `scripts/validate_voice_009_tts_provider_research.py`
  - `scripts/validate_voice_010_cartesia_tts_smoke.py`
  - `scripts/validate_voice_011_cartesia_websocket_smoke.py`
  - `research/experiments/cases/voice-009-tts-provider-research.json`
- Product/runtime boundary:
  - VOICE-009 made no API calls, uploaded no audio, and stored no API key.
  - VOICE-010 is dry-run/fallback by default.
  - Live Cartesia use requires explicit `--live`, `CARTESIA_API_KEY`, and `CARTESIA_VOICE_ID`.
  - TTS remains an adapter behind the reusable sales-agent core and active SalesCampaign language/guardrails.
- Security/privacy notes:
  - API keys are environment-only.
  - No customer audio is uploaded by these TTS checks.
  - Generated text sent to a provider requires retention and provider-terms review.
  - Cloned, custom, or customer-like voices remain blocked until consent/legal review.
- Follow-up:
  - Before production use, complete provider terms, text retention, latency, consent, and disclosure reviews.

## Workspace-Local Process Patterns Adapted Into This Repo

- Source:
  - `D:\Codex\shared\templates\voice-ai-consent-checklist.md`
  - `D:\Codex\active\youtube-channel\templates\generated-asset-log.md`
  - `D:\Codex\active\youtube-channel\automation\media-generation-workflow.md`
- Checked: 2026-05-02.
- Reuse label: adapted workspace pattern.
- What we learned/adapted:
  - Voice provider runs need explicit consent, provenance, provider boundary, generated asset logging, and review gates.
  - Provider workflows should document network use, upload use, API key location, cost risk, generated output path, and human review state.
  - Required workflow material should be local to the product repo, not dependent on another workspace project.
- Directly copied material: none. The Emotion Aware docs were rewritten locally for this product.
- Where it affected the Emotion Aware project:
  - `docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md`
  - `docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md`
  - `docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md`
  - `scripts/validate_self_contained_project_policy.py`
- Product/runtime boundary:
  - These docs are now project-local.
  - No runtime script imports from `D:\Codex\shared`, `active/youtube-channel`, or another workspace project.
  - Future client handoff should include the Emotion Aware repo only, not the wider `D:\Codex` workspace.
- Security/privacy notes:
  - API keys remain environment-only.
  - Customer audio upload remains blocked unless a separate consent and retention review exists.
  - Voice cloning remains blocked without explicit written permission for the exact voice and use.
- Follow-up:
  - RESP-003 live TTS should use these local docs as its provider-run and generated-audio logging boundary.

## Sources Needing Clarification Before Adding

- `source unclear`: local MELD, Persuasion for Good, and IEMOCAP dataset archives under `data/public/`.
  - These influenced label-mapping and experiment planning, but exact source URLs and license/access conditions were not identified from this chat history.
  - Do not add them as full inspiration/source entries until Tarik confirms the exact sources or we run a separate dataset provenance pass.
- `source unclear`: Apollo, Salesgenie, Proposify, and B2B Vic sales-objection materials referenced in `docs/product/SALES_DIFFICULTY_TAXONOMY.md`.
  - These were used as broad pattern grounding for sales-objection categories, but exact article/page URLs and usage terms were not captured in this chat history.
  - Do not add source-specific entries until Tarik confirms the exact pages or we run a separate source-provenance pass.

## Summary

- Sources added:
  - `1jehuang/jcode`
  - `karpathy/autoresearch`
  - `Shubhamsaboo/awesome-llm-apps`
  - `safishamsi/graphify`
  - `jamiepine/voicebox`
  - `microsoft/VibeVoice`
  - `NousResearch/hermes-agent`
  - `facebookresearch/tribev2`
  - official TTS provider sources for `VOICE-009`
  - workspace-local process patterns adapted into project-local voice/provider docs
- Sources needing license/source clarification:
  - local MELD, Persuasion for Good, and IEMOCAP dataset archives
  - Apollo, Salesgenie, Proposify, and B2B Vic sales-objection materials
- Copied material needing attribution or rewrite:
  - No direct code, prompts, docs, scripts, or configs were identified as copied into Emotion Aware from the listed repos.
  - The `awesome-llm-apps` battle-card influence is already attributed in `docs/battle-card-agent-blueprint.md`.
  - Provider facts are summarized; do not copy provider documentation text into product docs.
- Runtime, privacy, or security risk:
  - No listed open-source repo is currently a product runtime dependency.
  - Jcode, VibeVoice, Voicebox, Graphify, Hermes, and TRIBE v2 should not be installed into this product without a separate review.
  - Cartesia live TTS smoke testing is the only listed provider path with an explicit live-network mode; it remains opt-in and environment-key gated.
