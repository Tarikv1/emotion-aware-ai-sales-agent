# Emotion Aware AI Sales Agent Project Memory

This project is Tarik's product/thesis workspace for the emotion-aware AI sales-agent idea.

## New-Chat Bootstrap

- First orient from project-local files such as `README.md`, `docs/thesis/ROADMAP.md`, `docs/product/PRODUCT_BRIEF.md`, `docs/product/COMMANDS.md`, and recent Git history.
- If the wider `D:\Codex` workspace is available and extra orientation is useful, optionally run:

```powershell
cd D:\Codex\active\codex-workspace-dashboard
npm run cli -- memory refresh --project emotion-aware-ai-sales-agent
```

- Treat the refresh as local orientation only: no raw transcript capture, no network call, and no secret contents.
- Do not make this project depend on Codex HQ. If a workflow becomes required for Emotion Aware, adapt it into this repo.

## Durable Context

- Keep product-required docs, scripts, and workflows inside this repo when they are needed for product operation or customer/developer handoff.
- Workspace tools from `D:\Codex\shared` and Codex HQ may support development, but they are not product runtime dependencies.
- Preserve the architecture principle:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + explicit guardrails, consent, provider gates, and human escalation paths
```

- Use `docs/product-review-gates.md` before larger product/runtime changes, provider work, memory/transcript/customer-data flows, or customer setup changes.
- Track Emotion-Aware-relevant external inspirations in `docs/third-party-inspirations.md`.

## Privacy

- Do not store secrets, API keys, raw private customer data, raw restricted transcripts, or private audio here.
- Data under `data/private-restricted/` is sensitive by default.
- Live provider/network behavior must stay opt-in and documented.
