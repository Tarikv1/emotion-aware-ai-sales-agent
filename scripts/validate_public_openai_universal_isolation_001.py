#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PUBLIC-OPENAI-UNIVERSAL-ISOLATION-001"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID
RESULT_PATH = OUT_DIR / "result.json"
REPORT_PATH = OUT_DIR / "report.md"

UNIVERSAL_FILES = [
    ROOT / "runtime" / "core" / "universal_conversation_policy_runtime.py",
    ROOT / "runtime" / "core" / "universal_sales_conversation_knowledge.py",
    ROOT / "runtime" / "core" / "contextual_buyer_semantics.py",
    ROOT / "runtime" / "core" / "dialogue_manager.py",
    ROOT / "runtime" / "core" / "live_voice_session_policy.py",
]

FORBIDDEN_PATTERNS = {
    "OpenAI": re.compile(r"OpenAI"),
    "ChatGPT": re.compile(r"ChatGPT"),
    "GPT-5.5": re.compile(r"GPT-5\.5"),
    "GPT-5.3": re.compile(r"GPT-5\.3"),
    "Plus": re.compile(r"\bPlus\b"),
    "Pro": re.compile(r"\bPro\b"),
    "Enterprise": re.compile(r"\bEnterprise\b"),
    "Business ChatGPT": re.compile(r"Business ChatGPT"),
    "Codex pricing": re.compile(r"Codex pricing"),
    "Deep Research": re.compile(r"Deep Research"),
    "Custom GPTs": re.compile(r"Custom GPTs"),
    "plan fit check for ChatGPT": re.compile(r"plan fit check for ChatGPT"),
    "API usage is separate": re.compile(r"API usage is separate"),
}


def write_evidence(result: dict, report: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    failures: list[str] = []
    matches: list[dict[str, object]] = []
    for path in UNIVERSAL_FILES:
        if not path.is_file():
            failures.append(f"missing universal file: {path.relative_to(ROOT)}")
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for label, pattern in FORBIDDEN_PATTERNS.items():
                if pattern.search(line):
                    matches.append(
                        {
                            "file": str(path.relative_to(ROOT)),
                            "line": line_number,
                            "pattern": label,
                            "text": line.strip(),
                        }
                    )
    if matches:
        failures.append(f"OpenAI-specific facts leaked into universal files: {matches[:10]}")

    result = {
        "status": "pass" if not failures else "fail",
        "checkpoint_id": CHECKPOINT_ID,
        "files_checked": [str(path.relative_to(ROOT)) for path in UNIVERSAL_FILES],
        "match_count": len(matches),
        "matches": matches,
        "provider_calls_made": False,
        "local_llm_calls_made": False,
        "sends_email": False,
        "creates_calendar_event": False,
        "writes_crm": False,
        "opens_prod_102": False,
        "failures": failures,
    }
    report = "\n".join(
        [
            f"# {CHECKPOINT_ID}",
            "",
            f"- Status: `{result['status']}`",
            f"- Files checked: `{len(UNIVERSAL_FILES)}`",
            f"- Forbidden matches: `{len(matches)}`",
            f"- Failures: `{len(failures)}`",
            "",
        ]
    )
    write_evidence(result, report)
    if failures:
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.exit(1)
    print(json.dumps({"status": "pass", "checkpoint_id": CHECKPOINT_ID, "files_checked": len(UNIVERSAL_FILES)}, indent=2))


if __name__ == "__main__":
    main()
