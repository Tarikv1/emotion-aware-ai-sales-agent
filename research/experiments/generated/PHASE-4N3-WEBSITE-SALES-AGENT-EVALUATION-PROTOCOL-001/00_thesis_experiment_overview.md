# Thesis Experiment Overview

## Purpose

This protocol tests whether a structured local-business website sales-agent package produces stronger sales behavior than a simple generic website-sales prompt under the same manual voice-agent evaluation cases.

## Core Hypothesis

A structured campaign package with vertical knowledge, buyer-state handling, objection handling, and explicit safety boundaries will improve micro-close success and sales quality without increasing hard safety failures.

## Real Goal

The goal is not to prove that a hosted voice-agent platform can run a prompt. The goal is to produce thesis-grade evidence about sales-agent design choices:

- whether structured sales knowledge improves relevance
- whether explicit buyer-state and objection handling improves progression
- whether safety boundaries can coexist with strong selling
- which failure modes remain when a hosted voice-agent platform mediates the conversation

## Experimental Design

Use the same evaluation cases for all agent variants. Each case is run manually in the hosted platform with the same buyer scenario, the same target success outcome, and the same scoring rubric.

The only intended variable between Variant A and Variant B is the agent package:

- Variant A uses a simple generic baseline prompt and no knowledge base.
- Variant B uses the Atlas 4N2 prompt and 4N2 knowledge base files.
- Variant C is reserved for a future iteration after Variant A and Variant B results are scored.

## Evidence Framework

Evidence consists of sanitized transcripts, manual scores, hard failure flags, outcome labels, evaluator notes, representative quotes, and an aggregate metrics table.

Do not store real customer transcripts. Do not run real outbound calls. Do not enable tools. Do not use live customer data. Do not treat the protocol as production readiness.

## Provider Boundary

The protocol allows a future manual ElevenLabs dashboard run only after human setup. It does not call ElevenLabs, OpenAI, model, TTS, CRM, email, calendar, payment, or account APIs.
