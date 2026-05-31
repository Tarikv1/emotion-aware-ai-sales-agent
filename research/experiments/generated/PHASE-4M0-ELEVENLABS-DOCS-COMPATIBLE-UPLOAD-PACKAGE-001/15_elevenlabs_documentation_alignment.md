# ElevenLabs Documentation Alignment

This file records how 4M0 follows the ElevenLabs constraints supplied in the phase spec. No web browsing, ElevenLabs API call, OpenAI API call, model call, TTS call, or provider call was made in 4M0.

## Knowledge Base support

The package is formatted for KB addition as files. The phase constraints say files, URLs, or text can be added, and supported file formats include PDF, TXT, DOCX, HTML, and EPUB. This package uses Markdown files because they are easy to inspect locally and can be copied into TXT-style upload flows or converted later if the dashboard requires a different file extension.

## KB size and character constraints

The package treats non-enterprise limits conservatively as 20MB or 300k characters. KB content is split into focused files:

- Plan taxonomy.
- Allowed claims.
- Claim boundaries.
- Sales playbook.
- Objection handling.
- Persuasion strategy.
- Emotion/buyer state.
- Conversation repair.
- Side-effect safety.

The validator checks total KB character count and largest KB file character count.

## RAG usage

RAG retrieves relevant chunks rather than loading every document into prompt context. KB files use clear headings, topic labels, short sections, and "Allowed" / "Do not say" boundaries to make retrieval high-signal and lower latency.

## Document usage modes

- System prompt: `01_agent_system_prompt.md`.
- Prompt or Auto/RAG only for short guardrail material when dashboard limits allow it.
- Auto/RAG for plan facts, allowed claims, sales playbook, objections, persuasion, emotion/buyer state, repair, and safety.
- Reference-only for tool contracts, manual evaluation, and this alignment file.

## Tool types

ElevenLabs tools can be client tools, server tools, MCP tools, or system tools. This phase defines future read-only contracts only. All tools have `configure_now: false`.

## Server tool requirements

Future server tools are described as HTTP/API-style contracts with clear names, descriptions, parameter schemas, output schemas, when-to-call rules, when-not-to-call rules, safe fallback behavior, and side-effect policies.

## MCP tool planning

MCP is listed only as a future option for source-claim checking or state summarization. No MCP tool is configured in 4M0.

## Custom LLM future note

Custom LLM is not implemented or connected in 4M0. If a later phase uses one, it must be OpenAI-compatible through `/v1/chat/completions` or `/v1/responses` and support Server-Sent Events streaming with `text/event-stream`. That future work requires a separate provider/security review.

## Why custom LLM is not configured in 4M0

The goal is a manual ElevenLabs dashboard upload package, not a runtime repair or provider integration phase. Adding a custom LLM server now would increase risk, change runtime scope, and create a false readiness signal.

## Why all tools are disabled by default

Tool use can create side effects or false action claims if configured too early. 4M0 keeps tools disabled so the agent can be evaluated for spoken plan-fit quality, source safety, and side-effect refusal before any read-only tool is added.
