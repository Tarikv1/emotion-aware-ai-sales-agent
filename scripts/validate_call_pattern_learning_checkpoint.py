#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "call_pattern_learning_checkpoint.py"
TMP = ROOT / ".tmp" / "call-pattern-learning" / f"validation-{os.getpid()}"
NOTES = TMP / "notes"
OUT = TMP / "checkpoint.json"


def assert_condition(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def write_note(index: int) -> None:
    NOTES.mkdir(parents=True, exist_ok=True)
    payload = {
        "note_id": f"note-{index:03d}",
        "source_label": "redacted-local-call-note",
        "call_outcome": "successful" if index % 2 == 0 else "neutral",
        "event_outcomes": [{"event_type": "objection_handling", "event_outcome": "successful"}],
        "contains_raw_transcript": False,
        "contains_customer_identifier": False,
        "runtime_promotion_allowed": False,
    }
    (NOTES / f"note-{index:03d}.json").write_text(json.dumps(payload), encoding="utf-8")


def main() -> None:
    for index in range(199):
        write_note(index)
    below = subprocess.run(
        [sys.executable, str(SCRIPT), "--notes-dir", str(NOTES), "--out", str(OUT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(below.returncode == 0, below.stderr)
    below_payload = json.loads(OUT.read_text(encoding="utf-8"))
    assert_condition(below_payload["eligible_note_count"] == 199, below_payload)
    assert_condition(below_payload["threshold_met"] is False, below_payload)
    assert_condition(below_payload["runtime_promotion_allowed"] is False, below_payload)

    write_note(199)
    reached = subprocess.run(
        [sys.executable, str(SCRIPT), "--notes-dir", str(NOTES), "--out", str(OUT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert_condition(reached.returncode == 0, reached.stderr)
    reached_payload = json.loads(OUT.read_text(encoding="utf-8"))
    assert_condition(reached_payload["eligible_note_count"] == 200, reached_payload)
    assert_condition(reached_payload["threshold_met"] is True, reached_payload)
    assert_condition(reached_payload["notify_tarik"] is True, reached_payload)
    assert_condition(reached_payload["automatic_pattern_mining_started"] is False, reached_payload)
    assert_condition(reached_payload["runtime_promotion_allowed"] is False, reached_payload)
    serialized = json.dumps(reached_payload).replace("\\", "/").lower()
    assert_condition("raw-audio" not in serialized, reached_payload)
    assert_condition("transcripts-raw" not in serialized, reached_payload)
    print("Call pattern learning checkpoint validation passed.")


if __name__ == "__main__":
    main()
