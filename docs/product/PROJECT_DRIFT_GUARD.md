# Project Drift Guard

## Purpose

`GUARD-001` keeps the Emotion Aware AI Sales Agent repo portable and safe as the project grows.

It is a detection layer, not an auto-editor. The guard reports issues and exits with a failure when it finds risky drift, but it does not rewrite files, delete artifacts, rotate keys, or move dependencies by itself.

## What It Checks

- required project-local docs and scripts exist
- Git conflict markers are not left in text files
- secret-like values are not committed into project files
- generated voice/audio artifacts are ignored unless explicitly curated
- product files do not silently depend on another local workspace project
- `data/private/` exists for raw private call-center audio and is ignored/skipped so private files are not scanned or surfaced in reports

## Self-Containment Rule

Emotion Aware can use external repos, Codex HQ, and shared workspace material as inspiration during development.

If a workflow becomes required to run, demo, verify, deploy, support, or hand off Emotion Aware, the useful part must be adapted into this repo.

Allowed provenance or internal-tool notes can live in:

- `AGENTS.md`
- `docs/third-party-inspirations.md`
- `docs/internal-development-tools.md`
- `docs/product-local-tooling-candidates.md`
- `docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md`
- `docs/product/COMMANDS.md`
- `docs/product-review-gates.md`
- thesis logs and roadmap notes

Runtime scripts, validators, campaign logic, provider clients, customer demos, and product setup steps should not depend on files outside this repo.

## Commands

Run the guard:

```powershell
python scripts\check_project_drift.py
```

Run the machine-readable guard:

```powershell
python scripts\check_project_drift.py --json
```

Write a Markdown report:

```powershell
python scripts\check_project_drift.py --report-out research\experiments\generated\GUARD-001-project-drift-report.md
```

Validate the guard behavior:

```powershell
python scripts\validate_project_drift_guard.py
```

## Expected Behavior

- Clean repo: exits `0`.
- Drift detected: exits nonzero and lists exact file paths plus line numbers when available.
- Secrets: reports only the location and rule, not the secret value.
- External workspace paths: fail outside approved provenance docs.
- Generated audio: fail when provider outputs could be accidentally committed.
- Auto-fixes: always `false` for this checkpoint.

## Future Upgrade Path

The next useful version can add optional remediation suggestions, CI wiring, and a stricter deployment preflight.

Automatic fixing should stay off until the fix rules are boring, deterministic, and reviewed. This avoids the guard becoming the exact thing it is supposed to protect us from: a silent source of unexpected project changes.
