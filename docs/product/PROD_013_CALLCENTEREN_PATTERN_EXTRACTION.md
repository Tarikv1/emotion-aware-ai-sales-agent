# PROD-013 CallCenterEN Pattern Extraction

## Purpose

PROD-013 extracts a safe abstract pattern bank from local CallCenterEN / AIxBlock files.

It is the missing step between the real-world call-center dataset and the synthetic scenario tests: instead of hand-writing pattern abstractions, this checkpoint reads local dataset files transiently and emits structured labels for openings, intents, objections, emotion transitions, persuasion tactics, discovery questions, stages, close attempts, safety boundaries, timing behavior, domains, personas, and agent mistakes.

## Source Boundary

- Dataset: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- Dataset file tree: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english/tree/main
- Paper: https://arxiv.org/abs/2507.02958
- License observed: `cc-by-nc-4.0`
- Reuse label: `abstract_pattern_extraction_only`
- Commercial runtime use: `false`
- Commercial model training use: `false`

Default runs do not download the dataset. Place approved local ZIP/JSON/JSONL files under:

```text
data/external/callcenteren/raw/
```

That folder is ignored. The extractor writes only aggregate labels, counts, tactics, states, and scenario-template metadata.

## Dataset Shape Notes

The downloaded dataset ZIPs contain individual JSON files. Many files expose word-level text with start/end timestamps and no reliable speaker labels. PROD-013 handles this by grouping timestamped words into bounded pseudo-turns and using explicit speaker labels when present. When speaker labels are absent, role assignment is inferred from role-specific language signals plus file direction: agent signals include identity disclosure, company/call reason, permission checks, discovery questions, offer framing, empathy/repair, and handoff language; customer signals include price questions, busy/wrong-person boundaries, objections, cancellation, support issues, and callback/info requests. That inference is useful for pattern mining but is not ground-truth diarization.

## Extracted Pattern Groups

PROD-013 extracts:

- opening patterns: opening types, greeting styles, identity disclosures, company disclosures, reason for call, permission to continue, first question types, and customer initial response
- customer intent patterns: buying interest, information request, price request, complaint, cancellation, technical problem, billing issue, appointment request, not interested, wrong person, busy now, callback request, and hostile rejection
- objection patterns: objection text pattern, objection type, emotion signal, agent response tactic, response quality, resolved/not resolved, and next customer state
- emotion and tone transitions: neutral/interested/annoyed/confused/skeptical/hesitant/committed/angry transition labels
- persuasion strategy patterns: safe tactics and bad persuasion labels
- discovery question patterns: provider, problem, budget, usage, decision maker, timeline, priority, pain point, and eligibility questions
- turn-level stage patterns: opening through wrap-up labels
- close attempt patterns: close type, commitment level, customer response, safe close, close success, and follow-up required
- safety and compliance boundaries: stop, escalate, handoff, avoid unsupported claims, and avoid pressure
- timing and speech naturalness patterns: turn length, pause before agent response, interruptions, overlong monologues, rapid-fire questions, silence after offer, and silence after price
- domain-specific scenario patterns and agent mistake patterns

## Non-Extraction Rules

PROD-013 must not extract:

- exact scripts
- full call wording
- company-specific wording
- PII placeholders as features
- agent names or customer names
- long call summaries
- customer-service flows with no sales relevance, except as support, escalation, or stop-selling boundaries

## Commands

Run:

```powershell
python scripts\run_prod_013_callcenteren_pattern_extraction.py
```

Run with a smaller local sample:

```powershell
python scripts\run_prod_013_callcenteren_pattern_extraction.py --max-conversations 100
```

Run the full local dataset while keeping high-volume sample records bounded:

```powershell
python scripts\run_prod_013_callcenteren_pattern_extraction.py --max-conversations 0 --record-limit 5000
```

Validate:

```powershell
python scripts\validate_prod_013_callcenteren_pattern_extraction.py
```

Default output:

```text
research/experiments/generated/PROD-013-callcenteren-pattern-extraction/pattern-bank.json
research/experiments/generated/PROD-013-callcenteren-pattern-extraction/report.md
research/experiments/generated/PROD-013-callcenteren-pattern-extraction/download-manifest.json
```

## Runtime Decision

PROD-013 is not a runtime promotion. It creates the pattern bank that later scenario-generation checkpoints can use to build more realistic conversation flow. Any runtime use still requires separate leakage checks, non-sale correctness checks, safe-close checks, and retrieval/default-runtime gates.
