# RAG-003 Report Import Readiness

## Purpose

RAG-003 audits the real NotebookLM report files that were exported or pasted into the RAG-002 imports folder.

It answers a narrow question: are the report artifacts complete and structured enough to enter manual RAG normalization later?

## What It Checks

- expected topic coverage across the ten active RAG topics
- `END: COMPLETE` versus `NEED_CONTINUATION`
- source coverage section presence
- RAG-ready appendix or chunk-candidate presence
- pasted continuation or gap-check output after the first report body
- stable source-ID mapping readiness
- quote-review markers and secret-like strings

## What It Does Not Do

- it does not call NotebookLM
- it does not call an LLM, TTS provider, ASR provider, or external API
- it does not import chunks into runtime memory
- it does not enable retrieval
- it does not decide that the agent should use any extracted tactic yet

## Commands

Run the audit against the default imports folder:

```powershell
python scripts\run_rag_003_report_import_readiness.py
```

Validate the RAG-003 scanner and runner contract:

```powershell
python scripts\validate_rag_003_report_import_readiness.py
```

## Default Output

```text
research\experiments\generated\RAG-003-report-import-readiness\
```

The output contains:

- `result.json`
- `report.md`

## Current Import Audit

The 2026-05-06 audit of Tarik's imported NotebookLM reports found:

- `10 / 10` active RAG topics covered
- `11` report files scanned, including the Vinh Giang communication and human voice behavior report
- all reports contained `END: COMPLETE`
- no reports contained `NEED_CONTINUATION`
- no secret-like strings were detected
- runtime retrieval stayed disabled
- import readiness was `review_required`

After Tarik added the voice/prosody source-coverage addendum and later imported the Vinh Giang communication report, every report has source coverage. The review-required status is intentional. The reports are useful research intake, but they still need source-title-to-stable-source-ID mapping, pasted continuation/gap-check normalization, and quote review before chunk import.

## Readiness Meaning

`ready_for_manual_chunk_normalization` means the reports are structurally present, complete, and mapped well enough for a later reviewed chunk-normalization step.

`review_required` means the reports are useful but still need cleanup, source-ID mapping, quote review, or appendix normalization.

`blocked` means a topic is missing, a report still needs continuation, or a secret-like string was detected.

Even when the status is not blocked, runtime retrieval remains disabled. Source-tracked chunks must be normalized and reviewed in a later checkpoint before the sales agent can use them.

## Product Boundary

RAG-003 keeps the product architecture unchanged:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + reviewed sales knowledge layer
  + explicit guardrails and human escalation paths
```

The extracted reports are research intake, not product behavior.
