# Internal Development Tools

## Purpose

This project can use tools from Codex HQ and `D:\Codex\shared` during development, but those tools are not product runtime dependencies.

Customer setup for Emotion Aware AI Sales Agent should not require Tarik's broader `D:\Codex` workspace, Codex HQ, shared skills, shared templates, or workspace memory files.

Some product-local developer-tooling patterns were inspired by external agent-tooling projects such as `1jehuang/jcode`. Track those sources in `docs/third-party-inspirations.md`; do not make them hidden runtime or customer setup dependencies.

## Boundary

Use internal tools for:

- finding project context across `D:\Codex`
- auditing local files before risky changes
- drafting or reviewing reusable skills
- diagnosing research or agent workflows
- deciding whether a workflow should become product-local

Do not use internal tools as:

- required customer install steps
- production runtime services
- hidden dependencies for demos
- the only way to validate a product release
- a place to store product secrets, private customer data, or client-specific sensitive details

If a workflow becomes required for product operation, rebuild the minimal useful version inside this repo.

## Useful Internal Commands

Run these from `D:\Codex\active\codex-workspace-dashboard`, or from any project with:

```powershell
node D:\Codex\active\codex-workspace-dashboard\cli.mjs <command>
```

Useful commands while developing Emotion Aware:

```powershell
npm run cli -- memory search "emotion aware"
npm run cli -- docs search "voice provider"
npm run cli -- audit network
npm run cli -- audit secrets
npm run cli -- classify file --path active/emotion-aware-ai-sales-agent/docs/product/PRODUCT_BRIEF.md
npm run cli -- diagnose agent
npm run cli -- diagnose rag
npm run cli -- skills observations add --skill "emotion-aware-product-workflow" --note "<sanitized observation>"
npm run cli -- skills proposals create --skill "emotion-aware-product-workflow" --title "<title>" --summary "<summary>"
```

## How To Use Them Safely

- Treat Codex HQ findings as internal review support, not final product evidence.
- Do not paste secrets, API keys, private customer data, raw transcripts, or private application details into shared memory or skill logs.
- Use `audit secrets` to find secret-like files and paths, but do not copy secret contents into documentation.
- Use `audit network` to find possible internet-capable code paths, then inspect the product-local scripts before enabling live provider calls.
- Keep skill improvement proposals review-gated. Do not automatically change Codex skills after a single observation.
- Prefer product-local docs and scripts for any workflow a customer, teammate, or deployment environment will need.

## Product Repo Handoff Rule

Before a workflow is considered product-ready, ask:

1. Can a new developer understand and run it from this repo alone?
2. Does it avoid reading or logging secrets?
3. Does it default to no external network calls unless explicitly enabled?
4. Does it document provider, consent, retention, and data-source assumptions?
5. Does it produce outputs inside this repo's expected `research/`, `docs/`, `data/`, or future app/service folders?

If the answer is no, the workflow can still be useful internally, but it should not be part of customer setup yet.
