# ELEVENLABS-020 Layered KB Packaging And Natural Speech Compression

## Why The Universal KB Was Split

The full universal sales core is useful source material, but it is too broad for active ElevenLabs retrieval. Broad retrieval increases the chance that the agent pulls generic frameworks, old repair wording, or internal labels instead of the most relevant sales move.

ELEVENLABS-020 keeps the reusable method but splits it into focused universal category files. Those files are source/reference material. The active Atlas Web Studio voice agent should use the compact universal summary plus campaign layers.

## Active Agent Package

Recommended active KB package:

1. `runtime/providers/elevenlabs_agents/knowledge_base/universal_sales_core_summary.md`
2. `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_overlay.md`
3. `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio_web_design_campaign_profile.md`

The full `universal_sales_core.md` remains available as source material, but it is not recommended for active Atlas upload unless explicitly needed.

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
