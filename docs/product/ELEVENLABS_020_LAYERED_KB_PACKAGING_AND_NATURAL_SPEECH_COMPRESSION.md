# ELEVENLABS-020 Layered KB Packaging And Natural Speech Compression

## Why The Universal KB Was Split

The full universal sales core is useful source material, but it is too broad for active ElevenLabs retrieval. Broad retrieval increases the chance that the agent pulls generic frameworks, old repair wording, or internal labels instead of the most relevant sales move.

ELEVENLABS-020 keeps the reusable method but splits it into focused universal category files. The full 21-file category set remains source/reference material. The active Atlas Web Studio voice agent uses the compact universal summary, 14 selected tactical category files, the campaign overlay, and the campaign profile.

## Active Agent Package

Recommended active KB package:

1. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core_summary.md`
2. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/buyer_moves.md`
3. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/buyer_journey_jobs.md`
4. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/buyer_enablement_and_sensemaking.md`
5. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/discovery_question_design.md`
6. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/value_and_roi_framing.md`
7. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/objection_status_quo_and_competition.md`
8. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/trust_and_risk_repair.md`
9. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/proof_and_evidence_handling.md`
10. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/conversation_repair.md`
11. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/next_step_policy.md`
12. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/disqualification_policy.md`
13. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/ethical_persuasion_boundaries.md`
14. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/motion_specific_playbooks.md`
15. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_categories/call_quality_rubrics.md`
16. `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md`
17. `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md`

The full `universal_sales_core.md` remains available as source material, but it is not recommended for active Atlas upload unless explicitly needed.

Reference-only category files not in the active upload are `stakeholder_mapping.md`, `qualification_evidence.md`, `decision_and_paper_process.md`, `negotiation_and_concession_policy.md`, `vertical_general_playbooks.md`, `post_sale_handoff.md`, and `success_failure_patterns.md`.

## Campaign Profile Owns Facts

The campaign profile owns exact offer, approved prices, assurance facts, demand-capture mechanism, vertical mechanisms, send/callback facts, next steps, and forbidden claims.

This matters because universal sales guidance can improve how the agent sells, but it cannot create Atlas facts, prices, guarantees, proof, contact details, or operational capabilities.

## Prompt Compression

The prior prompt had accumulated patch-style repairs. ELEVENLABS-020 compresses it into a voice-agent system prompt with role, mission, layer precedence, spoken style, sales spine, send-state control, hard boundaries, and dynamic variable guidance.

The goal is lower retrieval and prompt noise while preserving the dominant sales spine: no guarantee, existing attention, where attention leaks, buyer action, and the free mockup as the proof step.

## Natural Spoken Style

Natural speech is enforced in the prompt by requiring short turns, one idea at a time, one question at a time, direct answer first, and contractions by default in buyer-facing replies.

The prompt also bans internal words such as RAG, demand capture, system prompt, validator, and acceptance criteria from normal buyer-facing output. Buyer-facing replacements point to plain actions: what to do next, a page people can check before calling, a cleaner way to call or request a quote, and a free mockup to judge first.

## Provider And Readiness Boundary

No ElevenLabs API calls were made.
No OpenAI API calls were made.
No live outbound calls were enabled.
No CRM, email, calendar, payment, account, scraping, or lead tooling was enabled.
No private customer data or private transcripts were used.
Production readiness is not claimed.
