# VOICE-001 TTS Response Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a provider-safe text-to-speech prototype that turns an existing realtime sales-agent `agent_response` into a traceable neutral synthetic voice packet.

**Architecture:** The voice layer calls the existing realtime turn CLI path, extracts the approved `agent_response`, and wraps it in TTS metadata. Dry-run mode is deterministic and required for validation; optional Windows SAPI audio generation can be used locally without cloud keys.

**Tech Stack:** Python standard library, existing realtime turn modules, optional Windows PowerShell `System.Speech.Synthesis`, Markdown docs, JSON generated artifacts.

---

## File Structure

- Create: `scripts/validate_voice_001_tts.py`
  - Validates dry-run behavior, packet shape, source decision reuse, and secret-safe generated artifacts.
- Create: `scripts/generate_voice_response.py`
  - Calls the realtime turn engine, builds a voice packet, supports dry-run, and optionally writes local Windows SAPI WAV output.
- Create: `docs/product/VOICE_001_TTS_PROTOTYPE.md`
  - Documents how VOICE-001 fits around the reusable sales-agent core.
- Create: `research/experiments/VOICE-001-tts-response-prototype.md`
  - Summarizes the experiment and its result.
- Generate: `research/experiments/generated/VOICE-001-tts-packet.json`
  - Stores a deterministic dry-run sample packet.

## Task 1: Add Failing Validator

**Files:**
- Create: `scripts/validate_voice_001_tts.py`

- [ ] **Step 1: Write the validator before implementation**

```python
#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "generate_voice_response.py"


def run_voice_script(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def main() -> None:
    assert SCRIPT_PATH.exists(), "VOICE-001 generator script is missing"
    packet = run_voice_script(
        "--campaign",
        "campaign-prod-005-b2c-telecom",
        "--stage",
        "relevance-check",
        "--transcript",
        "Nur wenn Sie garantieren koennen, dass es stabil ist.",
        "--dry-run",
    )
    assert packet["voice_run_id"] == "VOICE-001-dry-run"
    assert packet["provider"] == "dry-run"
    assert packet["voice"]["style"] == "neutral-synthetic-test"
    assert packet["decision"]["sales_difficulty"] == "claim-boundary"
    assert packet["tts_text"] == packet["decision"]["agent_response"]
    assert packet["audio_output_path"] is None
    serialized = json.dumps(packet)
    assert "sk-" not in serialized
    assert "OPENAI_API_KEY" not in serialized
    assert "Authorization: Bearer" not in serialized


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run validator to verify it fails**

Run:

```powershell
python scripts\validate_voice_001_tts.py
```

Expected: fail with `VOICE-001 generator script is missing`.

## Task 2: Implement VOICE-001 Generator

**Files:**
- Create: `scripts/generate_voice_response.py`

- [ ] **Step 1: Implement dry-run packet generation**

Use the existing realtime turn functions:

```python
from realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from run_realtime_turn_simulation import load_realtime_cases
```

The script should:

- parse `--campaign`, `--stage`, `--transcript`, `--input-type`, `--silence-count`, `--cases`, `--provider`, `--voice-name`, `--out-json`, `--out-audio`, and `--dry-run`
- call `run_turn_decision`
- extract `decision["agent_response"]`
- create a packet with campaign metadata, voice metadata, realtime decision, `tts_text`, latency contract, and audio output path
- print JSON to stdout
- write JSON to `--out-json` when provided
- never require or print an API key

- [ ] **Step 2: Add optional Windows SAPI audio generation**

When `--provider windows-sapi` is used without `--dry-run`, call PowerShell with environment variables for text, output path, and optional voice name. The script should fail with a clear message if `--out-audio` is missing.

- [ ] **Step 3: Run validator to verify it passes**

Run:

```powershell
python scripts\validate_voice_001_tts.py
```

Expected: exit code `0`.

## Task 3: Add Documentation And Generated Evidence

**Files:**
- Create: `docs/product/VOICE_001_TTS_PROTOTYPE.md`
- Create: `research/experiments/VOICE-001-tts-response-prototype.md`
- Generate: `research/experiments/generated/VOICE-001-tts-packet.json`

- [ ] **Step 1: Generate deterministic dry-run packet**

Run:

```powershell
python scripts\generate_voice_response.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Nur wenn Sie garantieren koennen, dass es stabil ist." `
  --dry-run `
  --out-json research\experiments\generated\VOICE-001-tts-packet.json
```

Expected: JSON packet is printed and written to the generated artifact path.

- [ ] **Step 2: Document the product role**

Explain that VOICE-001 is a transport/interface layer around the vertical-agnostic realtime agent, not a separate sales brain.

- [ ] **Step 3: Document the experiment**

Record the sample campaign, transcript, provider mode, decision reuse, and safety boundary.

## Task 4: Verify, Commit, And Push

**Files:**
- Verify all created files and generated artifacts.

- [ ] **Step 1: Run validators**

Run:

```powershell
python scripts\validate_voice_001_tts.py
python scripts\validate_realtime_turn_cli.py
```

Expected: both commands exit `0`.

- [ ] **Step 2: Run secret scan for changed files**

Run a PowerShell `Select-String` scan for:

```text
sk-[A-Za-z0-9_-]{20,}|OPENAI_API_KEY\s*=|Authorization:\s*Bearer\s+[A-Za-z0-9]
```

Expected: no matches.

- [ ] **Step 3: Commit and push**

Commit message:

```text
Add VOICE-001 TTS response prototype
```

Push `main` to `origin/main`.

