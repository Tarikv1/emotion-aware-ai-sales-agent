# Product Review Gates

These are internal development gates for the Emotion Aware AI Sales Agent. They are not customer runtime dependencies.

The gates are intentionally project-local so the repo remains portable. Workspace-level templates can inspire future improvements, but they are not required to use this file.

## Default Gates

Before larger changes, write a short local review note using the relevant gates below.

Product framing:

- What customer/client workflow changes?
- Does this preserve one reusable sales-agent core plus configurable SalesCampaign profiles?
- Does this make the product more vertical-agnostic or accidentally narrower?
- What claim, handoff, scheduling, or compliance behavior changes?

Engineering blast radius:

- Which scripts, docs, schemas, generated artifacts, and validators are touched?
- Which existing checkpoints could regress?
- Does default setup remain offline and no-key-safe?
- Does the change need a new validator or setup check?
- Does `python scripts\check_project_drift.py` pass with no hidden dependency, secret, conflict-marker, or generated-audio drift?

Security/privacy:

- Could any API key, voice ID, transcript, customer data, or private audio be logged or committed?
- Does the change add provider/network behavior?
- Does it upload customer audio or use voice cloning?
- Are live calls opt-in with bounded timeout and clear fallback?

QA-only review before edits:

- What is the observed issue?
- What command or artifact proves it?
- What is the smallest safe change?
- What verification will prove the fix?

## Product Architecture Rule

Every reviewed change must preserve:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + explicit guardrails, consent, provider gates, and human escalation paths
```

## When To Use

- Before changing the reusable sales-agent core.
- Before adding provider/API/network behavior.
- Before adding memory, transcript, voice, or customer-data flows.
- Before turning a thesis experiment into product behavior.
- Before adding a customer setup requirement.

## Optional Workspace Impact Helper

If the wider `D:\Codex` workspace is available, this optional helper can support development review:

```powershell
npm run cli -- impact file --project emotion-aware-ai-sales-agent --path <path-inside-project>
```

Do not treat this as a required product or customer setup command. If impact analysis becomes required for product operation, rebuild a product-local script inside this repo.

## Boundary

- These gates support development only.
- They must not become required customer install steps.
- Required gates must stay readable inside this file or another project-local file.
