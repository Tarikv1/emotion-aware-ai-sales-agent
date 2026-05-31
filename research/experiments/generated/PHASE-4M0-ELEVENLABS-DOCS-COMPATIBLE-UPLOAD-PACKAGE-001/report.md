# PHASE-4M0-ELEVENLABS-DOCS-COMPATIBLE-UPLOAD-PACKAGE-001

## Recommendation

Use this package for manual ElevenLabs Agent setup and manual evaluation. Do not treat it as live readiness. Do not enable tools, provider/model/TTS calls, CRM, email, calendar, payment, account actions, selector control, or response replacement in 4M0.

## What ElevenLabs owns

- Hosted voice session.
- Agent prompt field.
- Knowledge Base storage and RAG retrieval.
- Workflow builder branch configuration.
- Conversation analysis fields and manual dashboard configuration.

## What the repo still owns

- Source bundle truth and claim precision policy.
- Evaluation scripts and safety validators.
- Sales playbook source material.
- Future read-only tool contracts.
- Guardrails for no side effects, no affiliation claim, and no unsupported current-term claims.

## Files created

- result.json: Machine-readable checkpoint outcome and safety flags.
- report.md: Human-readable checkpoint report.
- 00_dashboard_setup_checklist.md: Manual dashboard setup and safety checklist.
- 01_agent_system_prompt.md: System prompt for the ElevenLabs Agent.
- 02_workflow_branch_spec.md: Workflow branch planning reference.
- 03_kb_openai_plan_taxonomy.md: KB plan taxonomy and routing.
- 04_kb_openai_allowed_claims.md: KB source-grounded allowed claims.
- 05_kb_openai_claim_boundaries_do_not_say.md: KB claim boundaries and forbidden claims.
- 06_kb_openai_sales_playbook.md: KB discovery, recommendation, disqualification, and close logic.
- 07_kb_objection_handling_playbook.md: KB objection handling responses.
- 08_kb_persuasion_strategy_playbook.md: KB ethical persuasion strategies.
- 09_kb_emotion_buyer_state_playbook.md: KB buyer-state adaptation.
- 10_kb_conversation_repair_loop_handling.md: KB conversation repair rules.
- 11_kb_side_effect_tool_safety.md: KB side-effect refusal and safe alternatives.
- 12_tool_contracts_read_only.md: Future disabled read-only tool contract reference.
- 13_manual_eval_script.md: Manual evaluation script.
- 14_upload_manifest.json: Upload manifest and usage-mode map.
- 15_elevenlabs_documentation_alignment.md: ElevenLabs documentation alignment reference.

## KB summary

- KB file count: 9
- Total KB character count: 41618
- Largest KB file character count: 12619
- Conservative non-enterprise KB limit safe: true

## RAG/upload strategy

Upload `03` through `11` as focused KB documents. Use Auto/RAG for most documents. Use Prompt mode only for short guardrail-critical material if dashboard limits allow it. Keep tool contracts, manual eval, and documentation alignment as reference-only.

## Workflow summary

The workflow spec defines 16 manual branches: source boundary, individual fit, individual comparison, Business/Enterprise, privacy/security/procurement, pricing/current terms, API/subscription boundary, competitor/current tool, objections, no-fit, self-serve close, contact-sales route, repeated-question repair, side-effect refusal, confusion simplification, and buyer emotion/frustration handling.

## Tool contract summary

Four future read-only tools are described and disabled: `plan_fit_verifier`, `source_claim_checker`, `side_effect_guard`, and `conversation_state_summarizer`. All have `configure_now: false` and read-only side-effect policies.

## Evaluation summary

Manual eval case count: 46. Coverage includes 4L2 single-turn cases, 4L3 multi-turn cases, 4L4 Go-specific cases, 4L5 claim-conflict cases, side-effect refusal cases, contamination checks, and spoken quality rating fields.

## ElevenLabs docs alignment summary

The package follows the supplied KB, RAG, document usage mode, tool type, server tool, MCP planning, and custom LLM constraints. Custom LLM is not configured in 4M0. Tools are disabled by default.

## Risks

- ElevenLabs dashboard limits or UI labels may differ from this local reference and need manual adjustment.
- RAG chunking can retrieve too much or too little; manual tests must check latency and source safety.
- Current OpenAI pricing, terms, models, features, and limits can change after the 4L5 source bundle.
- Go feature exactness remains source-conflict/ambiguous and must stay conservative.
- Manual upload readiness is not live production readiness.

## Manual test plan

1. Paste the system prompt.
2. Upload KB files `03` through `11`.
3. Configure workflow branches manually only if needed.
4. Keep all tools disabled.
5. Run the manual eval script.
6. Record spoken naturalness, sales usefulness, source safety, and side-effect safety.

## Success criteria for deciding whether to pivot

Continue with ElevenLabs-hosted prototype only if:

- no OpenAI affiliation claim appears.
- no unrelated legacy campaign contamination appears in uploadable files or buyer-facing responses.
- no fake email/calendar/CRM/payment/account action appears.
- no unsupported plan claims appear.
- Go is handled conservatively.
- buyer context is preserved across turns.
- repeated-question repair works.
- spoken sales behavior is strong.
- average human rating is >= 4/5 for intelligibility and sales usefulness.
- no critical safety/source failures occur.

Pivot back to repo-side runtime work if manual ElevenLabs tests show poor RAG retrieval, recurring source overclaims, poor multi-turn memory, or side-effect refusal failures.

## Safety confirmations

- Provider calls made: false.
- Model calls made: false.
- OpenAI API calls made: false.
- ElevenLabs calls made: false.
- TTS calls made: false.
- CRM/email/calendar/payment/account side effects made: false.
- Selector control enabled: false.
- Response replacement enabled: false.
- Live readiness claimed: false.
