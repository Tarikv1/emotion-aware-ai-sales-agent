#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_NAME = "emotion-aware-ai-sales-agent"
ROOT = Path(__file__).resolve().parents[1]

THESIS_TRACKING_FILES = {
    "docs/thesis/METHODOLOGY_LOG.md",
    "docs/thesis/ROADMAP.md",
    "docs/thesis/DECISION_LOG.md",
    "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
    "docs/thesis/SPEECH_REALISM_REFERENCES.md",
    "docs/thesis/THESIS_OUTLINE.md",
    "docs/thesis/THESIS_WRITING_GUIDE.md",
    "docs/thesis/AI_USAGE_NOTE.md",
    "docs/thesis/COLLABORATION_NOTE.md",
}

THESIS_TRIGGER_PREFIXES = (
    "apps/",
    "db/",
    "docs/data/",
    "docs/product/",
    "packages/",
    "research/experiments/",
    "scripts/",
)

THESIS_TRIGGER_FILES = {
    "AGENTS.md",
    "README.md",
    "program.md",
    "docs/product-review-gates.md",
    "docs/third-party-inspirations.md",
}

IGNORE_PREFIXES = (
    ".tmp/",
    "data/private/",
    "data/private-restricted/",
    "config/local/",
)


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    path: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }


def normalize_path(path: str) -> str:
    normalized = path.strip().strip('"').replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def parse_git_status_line(line: str) -> str | None:
    if not line.strip():
        return None
    if line.startswith("?? "):
        return normalize_path(line[3:])
    if len(line) < 4:
        return None
    path = line[3:]
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return normalize_path(path)


def get_git_changed_files(root: Path) -> tuple[list[str], list[Issue]]:
    completed = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        return [], [
            Issue(
                code="git_status_unavailable",
                severity="fail",
                path=".",
                message=f"Could not read git status: {completed.stderr.strip() or completed.stdout.strip()}",
            )
        ]
    changed_files = [parsed for line in completed.stdout.splitlines() if (parsed := parse_git_status_line(line))]
    return sorted(set(changed_files)), []


def should_ignore_changed_file(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in IGNORE_PREFIXES)


def is_thesis_tracking_file(path: str) -> bool:
    return path in THESIS_TRACKING_FILES


def is_thesis_trigger(path: str) -> bool:
    if should_ignore_changed_file(path):
        return False
    if path in THESIS_TRACKING_FILES:
        return False
    if path in THESIS_TRIGGER_FILES:
        return True
    return any(path.startswith(prefix) for prefix in THESIS_TRIGGER_PREFIXES)


def recommended_docs_for(paths: list[str]) -> list[str]:
    recommendations = {"docs/thesis/METHODOLOGY_LOG.md", "docs/thesis/ROADMAP.md"}
    if any(path.startswith("docs/product/") or path.startswith("scripts/") or path.startswith("packages/") for path in paths):
        recommendations.add("docs/thesis/DECISION_LOG.md")
    if any(path.startswith("research/experiments/") for path in paths):
        recommendations.add("docs/thesis/METHODOLOGY_LOG.md")
    if any(path.startswith("docs/data/") for path in paths):
        recommendations.add("docs/thesis/THESIS_WRITING_GUIDE.md")
    if any(path.startswith("docs/") for path in paths):
        recommendations.add("docs/thesis/THESIS_REFERENCE_REGISTRY.md")
    return sorted(recommendations)


def build_report(root: Path, explicit_changed_files: list[str] | None = None) -> dict[str, Any]:
    issues: list[Issue] = []
    if explicit_changed_files is None:
        changed_files, git_issues = get_git_changed_files(root)
        issues.extend(git_issues)
        source = "git-status"
    else:
        changed_files = sorted(set(normalize_path(path) for path in explicit_changed_files if normalize_path(path)))
        source = "explicit-arguments"

    trigger_files = [path for path in changed_files if is_thesis_trigger(path)]
    thesis_files = [path for path in changed_files if is_thesis_tracking_file(path)]
    recommendations = recommended_docs_for(trigger_files)

    if trigger_files and not thesis_files:
        issues.append(
            Issue(
                code="missing_thesis_update",
                severity="fail",
                path="docs/thesis",
                message=(
                    "Product, research, runtime, prompt, data, or workflow files changed without a thesis tracking doc. "
                    "Update at least one recommended thesis doc before the GitHub checkpoint."
                ),
            )
        )

    failure_count = sum(1 for issue in issues if issue.severity == "fail")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    status = "fail" if failure_count else "pass"
    return {
        "project": PROJECT_NAME,
        "root": str(root),
        "status": status,
        "source": source,
        "summary": {
            "changed_file_count": len(changed_files),
            "trigger_file_count": len(trigger_files),
            "thesis_tracking_file_count": len(thesis_files),
            "issue_count": len(issues),
            "failure_count": failure_count,
            "warning_count": warning_count,
            "network_calls_made": False,
            "auto_fixes_applied": False,
        },
        "changed_files": changed_files,
        "trigger_files": trigger_files,
        "thesis_tracking_files": thesis_files,
        "recommended_thesis_docs": recommendations,
        "issues": [issue.to_dict() for issue in issues],
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Thesis Update Gate Report",
        "",
        f"- Project: {report['project']}",
        f"- Root: `{report['root']}`",
        f"- Status: `{report['status']}`",
        f"- Changed files: {report['summary']['changed_file_count']}",
        f"- Thesis-triggering files: {report['summary']['trigger_file_count']}",
        f"- Thesis tracking files: {report['summary']['thesis_tracking_file_count']}",
        f"- Network calls made: {str(report['summary']['network_calls_made']).lower()}",
        f"- Auto fixes applied: {str(report['summary']['auto_fixes_applied']).lower()}",
        "",
        "## Recommended Thesis Docs",
        "",
    ]
    if report["recommended_thesis_docs"]:
        for path in report["recommended_thesis_docs"]:
            lines.append(f"- `{path}`")
    else:
        lines.append("No thesis docs required for the current change set.")
    lines.extend(["", "## Issues", ""])
    if not report["issues"]:
        lines.append("No thesis update gate issues found.")
    else:
        for issue in report["issues"]:
            lines.append(f"- `{issue['severity']}` `{issue['code']}` `{issue['path']}`: {issue['message']}")
    lines.append("")
    return "\n".join(lines)


def print_text_report(report: dict[str, Any]) -> None:
    print(f"{report['project']} thesis update gate")
    print(f"Root: {report['root']}")
    print(f"Status: {report['status']}")
    print(
        "Summary: "
        f"{report['summary']['changed_file_count']} changed file(s), "
        f"{report['summary']['trigger_file_count']} thesis-triggering file(s), "
        f"{report['summary']['thesis_tracking_file_count']} thesis tracking file(s), "
        f"{report['summary']['failure_count']} failure(s)"
    )
    print("Network calls made: false")
    print("Auto fixes applied: false")
    if report["recommended_thesis_docs"]:
        print()
        print("Recommended thesis docs:")
        for path in report["recommended_thesis_docs"]:
            print(f"- {path}")
    if report["issues"]:
        print()
        print("Issues:")
        for issue in report["issues"]:
            print(f"- {issue['severity'].upper()} {issue['code']} [{issue['path']}]: {issue['message']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether thesis tracking docs were updated before a GitHub checkpoint.")
    parser.add_argument("--root", default=str(ROOT), help="Project root. Defaults to this repository root.")
    parser.add_argument("--changed-file", action="append", help="Explicit changed file path. Repeat for validation fixtures.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--report-out", help="Optional Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    report = build_report(root, args.changed_file)

    if args.report_out:
        report_path = Path(args.report_out)
        if not report_path.is_absolute():
            report_path = root / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render_markdown(report), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text_report(report)

    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
