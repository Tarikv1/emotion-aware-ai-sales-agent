# Private Call Learning Pipeline

## Purpose

Define how future private call-center recordings can improve the sales agent without turning customer identities or sensitive personal facts into training data.

This is a scaffold only. It does not ingest, transcribe, upload, or read real private recordings.

## Core Rule

Raw private audio never leaves `data/private/`.

Private identifiers are not training signal.

Pattern-mining first, fine-tuning later.

## Why This Exists

Human sales agents are trained from examples, coaching, repeated objections, and successful call patterns. The AI sales agent should eventually learn from the same kind of evidence, but only from the reusable sales behavior inside the calls.

Useful signal:

- how successful human agents open, listen, respond, and close
- how customers express objections, uncertainty, confusion, resistance, or interest
- which response patterns recover difficult calls
- which response patterns create distrust, pressure, confusion, or compliance risk
- when handoff, callback, transfer, or call ending is the right move

Not useful signal:

- names
- phone numbers
- addresses
- emails
- dates of birth
- account, policy, payment, or contract identifiers
- exact health facts
- exact financial facts
- exact locations
- any detail whose main value is identifying or profiling a person

## Pipeline

1. Ingest raw audio locally under `data/private/raw-audio`.
2. Transcribe locally by default into `data/private/transcripts-raw`.
3. Segment speakers into customer and human sales-agent turns under `data/private/speaker-segments`.
4. Redact or mask identifiers and sensitive details into `data/private/transcripts-redacted`.
5. Label outcomes under `data/private/outcome-labels`.
6. Mine patterns under `data/private/pattern-notes`.
7. Human-review extracted patterns before reuse.
8. Export only minimized, non-identifying sales-learning notes to safe project locations.
9. Delete raw source files when they are no longer needed and keep deletion manifests under `data/private/deletion-manifests`.

No safe export before redaction and human review.

## Positive And Negative Learning

Good calls are useful because they show what to do.

Bad calls are useful as negative constraints because they show what the agent should avoid.

Positive patterns may include:

- successful openings
- objection recovery sequences
- useful empathy moves
- strong timing for qualification questions
- smooth transition into scheduling or handoff

Negative patterns may include:

- pressure that increases resistance
- answers that ignore emotion
- confusing product explanations
- premature close attempts
- missed handoff or compliance-stop opportunities
- robotic or over-scripted phrasing that lowers trust

## RAG Boundary

Raw private data must not be loaded into RAG.

RAG can use only reviewed, minimized, non-identifying pattern notes. Those notes must carry a restricted source label so thesis and product claims do not pretend the result is public-only.

## Fine-Tuning Boundary

Fine-tuning is disabled by default.

A later fine-tuning checkpoint must separately prove:

- client scope allows it
- data-processing roles and retention rules are documented
- raw private audio is not uploaded
- identifiers and sensitive details are removed or masked
- examples are minimized to sales behavior
- bad examples are labeled as avoid patterns, not target behavior
- training examples are reviewed for quality and safety

## Local Workspace Structure

The ignored private workspace can be created with:

```powershell
python scripts\init_private_call_learning_workspace.py
```

Preview it without creating folders:

```powershell
python scripts\init_private_call_learning_workspace.py --dry-run
```

Required ignored subfolders:

- `data/private/raw-audio`
- `data/private/transcripts-raw`
- `data/private/speaker-segments`
- `data/private/transcripts-redacted`
- `data/private/outcome-labels`
- `data/private/pattern-notes`
- `data/private/quarantine`
- `data/private/deletion-manifests`

## Validation

Check the scaffold without scanning private file contents:

```powershell
python scripts\check_private_call_learning_pipeline.py
```

Validate the checker and policy:

```powershell
python scripts\validate_private_call_learning_pipeline.py
```

The checker must report:

- network calls made: false
- raw private content read: false
- secret values logged: false
- provider upload allowed: false
- raw audio Git tracking allowed: false
- customer identifier learning allowed: false
- fine-tuning enabled by default: false

## Thesis Note

This pipeline should be described as restricted private-data learning, not as a reproducible public dataset experiment. If future agent quality improves because of private call-center patterns, the thesis should disclose that restricted local evidence informed the product behavior while the raw data remains undistributed.
