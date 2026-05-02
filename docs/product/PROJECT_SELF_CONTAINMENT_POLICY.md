# Project Self-Containment Policy

## Purpose

Emotion Aware AI Sales Agent should be portable as a standalone project.

Future clients, reviewers, or deployment environments should not need access to:

- `D:\Codex\shared`
- `D:\Codex\active\youtube-channel`
- `D:\Codex\active\client-websites`
- `D:\Codex\active\codex-workspace-dashboard`
- another local workspace folder

## Rule

If Emotion Aware depends on a checklist, template, workflow, script, schema, or review gate, it must live inside this repository.

Workspace-level files can be read for inspiration during development, but any required material must be adapted into project-local files before it becomes part of the Emotion Aware workflow.

## Allowed

- Read external or workspace-local material for inspiration.
- Summarize useful ideas in project-owned language.
- Rebuild a small project-local version of a checklist or workflow.
- Record the source or inspiration in `docs/third-party-inspirations.md`.

## Not Allowed

- Runtime scripts importing from `D:\Codex\shared`.
- Runtime scripts requiring another active project folder.
- Documentation that tells a client to fetch required project policy from another local workspace.
- Provider workflows that rely on another project's templates.
- Copying external code, prompts, assets, or scripts without license and source review.

## Product Boundary

The product remains:

```text
one reusable sales-agent core
  + configurable SalesCampaign profiles
  + project-local guardrails, provider gates, and experiment evidence
```

The project can be moved, copied, reviewed, or handed to a client without carrying unrelated workspace folders.

## Current Local Policy Files

- `docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md`
- `docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md`
- `docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md`

## Validation

Run:

```powershell
python scripts\validate_self_contained_project_policy.py
```

This validator checks that the local policy docs exist and that Python scripts do not hard-depend on workspace-local external project paths.
