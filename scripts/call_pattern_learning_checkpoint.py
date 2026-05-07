#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTES_DIR = ROOT / "data" / "private" / "pattern-notes"
DEFAULT_OUT = ROOT / ".tmp" / "call-pattern-learning" / "checkpoint.json"
THRESHOLD = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether enough redacted call notes exist for pattern-mining review.")
    parser.add_argument("--notes-dir", default=str(DEFAULT_NOTES_DIR))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    return parser.parse_args()


def load_note(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def eligible_note(note: dict) -> bool:
    return (
        note.get("source_label") == "redacted-local-call-note"
        and note.get("contains_raw_transcript") is False
        and note.get("contains_customer_identifier") is False
        and note.get("runtime_promotion_allowed") is False
    )


def build_checkpoint(notes_dir: Path) -> dict:
    notes = [load_note(path) for path in sorted(notes_dir.glob("*.json"))] if notes_dir.exists() else []
    eligible_notes = [note for note in notes if eligible_note(note)]
    threshold_met = len(eligible_notes) >= THRESHOLD
    return {
        "checkpoint_id": "CALL-PATTERN-LEARNING-200-NOTE-CHECKPOINT",
        "notes_dir": str(notes_dir),
        "threshold": THRESHOLD,
        "eligible_note_count": len(eligible_notes),
        "threshold_met": threshold_met,
        "notify_tarik": threshold_met,
        "automatic_pattern_mining_started": False,
        "runtime_promotion_allowed": False,
        "next_decision": (
            "Ask Tarik whether to run pattern mining, split by campaign/language, change threshold, or continue collecting."
            if threshold_met
            else "Continue collecting redacted local call notes."
        ),
    }


def main() -> None:
    args = parse_args()
    notes_dir = Path(args.notes_dir)
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    payload = build_checkpoint(notes_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
