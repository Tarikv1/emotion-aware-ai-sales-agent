# Architecture Overview

## Purpose

4O0 defines a reusable sales-agent architecture for campaign-adaptive voice agents. The goal is to stop patching campaign-specific prompts one case at a time and instead define a stable separation between universal sales behavior, campaign facts, validated adapter data, and rendered agent packages.

## Layers

### 1. Universal Sales Operating System

The universal sales operating system is the reusable sales intelligence layer. It defines how the agent sells across campaigns without knowing a specific company, offer, price, proof point, close path, or tool.

It owns:

- truthful identity
- cold-call opening logic
- qualification
- discovery
- buyer-state detection
- emotion-aware adaptation
- pain-to-value bridge
- consultative persuasion
- objection handling
- disqualification
- micro-close strategy
- pricing behavior
- capability boundaries
- side-effect boundaries
- stop-request handling
- repeated-question repair
- trust repair
- call control
- no fake guarantees
- no fake authority
- no pressure after refusal
- no bracketed/internal labels

### 2. Campaign Intake Layer

The intake layer is the human-authored source of campaign facts. It asks the campaign owner for the company, offer, buyer, pains, safe outcomes, pricing policy, proof, objections, close paths, allowed commitments, forbidden claims, tool permissions, unavailable actions, compliance boundaries, privacy constraints, and stop-request policy.

### 3. Campaign Adapter Schema

The adapter is not raw intake. It is the normalized, validated, sales-ready campaign representation used by renderers and tests.

It owns:

- normalized product facts
- approved claims
- forbidden claims
- buyer personas
- pain-to-value mappings
- objection playbooks
- qualification logic
- disqualification logic
- pricing behavior
- close paths
- tool/capability boundaries
- campaign-specific test cases
- uploadable KB files
- rendered system prompt fields

### 4. Rendered Agent Package

The renderer combines universal rules, campaign adapter facts, capability boundaries, and campaign-specific knowledge into a prompt, KB files, test cases, an upload manifest, and EASID logging fields for a provider shell.

The rendered package must not include private data, internal test language in buyer-facing prompts, fake actions, unrelated campaign knowledge, or any side effect that is not explicitly enabled.

## Minimum Workflow

1. Campaign owner fills in the campaign intake.
2. Validator checks completeness, safety, claims, pricing policy, stop-request policy, and side-effect risk.
3. Normalizer converts raw intake into a campaign adapter.
4. Renderer produces a provider-shell package from universal rules plus adapter facts.
5. Universal and campaign-specific tests verify behavior before any manual upload or runtime use.

## Architecture Decision

The strong architecture is not a bigger prompt. It is a small universal core plus structured campaign facts and explicit boundaries. The first thing likely to break in a prompt-only approach is campaign contamination: the agent will borrow facts, promises, pricing, or close paths from a previous campaign. The adapter boundary makes that failure visible and testable.
