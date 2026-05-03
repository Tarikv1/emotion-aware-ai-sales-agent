# Context Reading Policy

## Purpose

This policy makes the project-local relevant reader the default first step for large documentation and thesis files.

The goal is not to hide context. The goal is to avoid wasting time and context window on 200- to 1,000-line files when only a section, heading map, or nearby match is needed.

## Automatic Rule

Use `scripts/read_relevant.py` before full-file reads when working with:

- large Markdown docs
- thesis logs
- roadmaps
- product command maps
- generated reports
- policy or review-gate files

Start with the smallest useful read:

```powershell
python scripts\read_relevant.py outline --path docs\product\COMMANDS.md
```

Then use one of:

```powershell
python scripts\read_relevant.py section --path docs\product\COMMANDS.md --heading "Setup"
```

```powershell
python scripts\read_relevant.py find --path docs\product\COMMANDS.md --query "ElevenLabs" --context 2
```

```powershell
python scripts\read_relevant.py slice --path docs\product\COMMANDS.md --start 55 --end 88
```

## When Full Reads Are Still Correct

Full-file reads are still appropriate when:

- the file is short
- editing code where imports, helper functions, and contracts may matter
- changing a schema, validator, runner, or runtime module where hidden coupling is likely
- verifying a whole document for consistency before committing
- the relevant-reader output shows that more surrounding context is needed

## Safety Boundaries

The reader is project-local, offline, and no-key.

It should not read private restricted data, secret files, generated audio, provider keys, or files outside this repo.

## Validation

Run:

```powershell
python scripts\validate_context_reading_policy.py
```

This confirms that:

- `AGENTS.md` carries the automatic rule for future project work
- this policy exists
- `docs/product/COMMANDS.md` documents the reader and validator
- the project-local reader and validator still exist
