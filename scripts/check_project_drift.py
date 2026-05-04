#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_NAME = "emotion-aware-ai-sales-agent"
ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "docs/third-party-inspirations.md",
    "docs/product-review-gates.md",
    "docs/product/COMMANDS.md",
    "docs/product/CONTEXT_READING_POLICY.md",
    "docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md",
    "docs/product/VOICE_PROVIDER_RUN_BOUNDARY.md",
    "docs/product/VOICE_GENERATED_AUDIO_ASSET_LOG.md",
    "docs/product/PROJECT_DRIFT_GUARD.md",
    "docs/data/PRIVATE_CALL_CENTER_DATA_POLICY.md",
    "docs/data/PRIVATE_CALL_LEARNING_PIPELINE.md",
    "docs/thesis/ROADMAP.md",
    "docs/thesis/METHODOLOGY_LOG.md",
    "docs/thesis/DECISION_LOG.md",
    "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
    "docs/thesis/THESIS_WRITING_GUIDE.md",
    "data/private/.gitignore",
    "scripts/check_project_drift.py",
    "scripts/check_thesis_reference_registry.py",
    "scripts/validate_thesis_reference_registry.py",
    "scripts/check_thesis_update_gate.py",
    "scripts/validate_thesis_update_gate.py",
    "scripts/speech_realism.py",
    "scripts/run_voice_023_speech_realism.py",
    "scripts/validate_voice_023_speech_realism.py",
    "scripts/validate_private_data_boundary.py",
    "scripts/check_private_call_learning_pipeline.py",
    "scripts/init_private_call_learning_workspace.py",
    "scripts/validate_private_call_learning_pipeline.py",
    "scripts/validate_context_reading_policy.py",
    "scripts/validate_project_drift_guard.py",
]

ALLOWED_EXTERNAL_REFERENCE_FILES = {
    "AGENTS.md",
    "docs/internal-development-tools.md",
    "docs/product-local-tooling-candidates.md",
    "docs/third-party-inspirations.md",
    "docs/product/COMMANDS.md",
    "docs/product/PROJECT_SELF_CONTAINMENT_POLICY.md",
    "docs/product/PROJECT_DRIFT_GUARD.md",
    "docs/product-review-gates.md",
    "docs/thesis/METHODOLOGY_LOG.md",
    "docs/thesis/ROADMAP.md",
}

TEXT_EXTENSIONS = {
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sql",
    ".toml",
    ".ts",
    ".txt",
    ".yml",
    ".yaml",
}

BINARY_EXTENSIONS = {
    ".db",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".pdf",
    ".png",
    ".pyc",
    ".sqlite",
    ".wav",
}

SKIP_DIRS = {
    ".git",
    ".tmp",
    "__pycache__",
}

SKIP_DIR_PREFIXES = {
    ("data", "public"),
    ("data", "private"),
    ("data", "private-restricted"),
    ("data", "processed"),
    ("config", "local"),
}

AUDIO_EXTENSIONS = {".mp3", ".wav"}

CURATED_GENERATED_AUDIO_FILES = {
    "research/experiments/generated/VOICE-002-customer-placeholder.wav",
}

SECRET_PATTERNS = [
    r"sk_car_[A-Za-z0-9_-]{20,}",
    r"sk-[A-Za-z0-9_-]{20,}",
    r"AIza[0-9A-Za-z_-]{20,}",
    r"xox[baprs]-[A-Za-z0-9-]{20,}",
    r"CARTESIA_API_KEY\s*=\s*[^\s]+",
    r"ELEVENLABS_API_KEY\s*=\s*[^\s]+",
    r"OPENAI_API_KEY\s*=\s*[^\s]+",
    r"Authorization:\s*Bearer\s+[A-Za-z0-9]",
    r"X-API-Key\s*[:=]\s*[A-Za-z0-9]",
    r"xi-api-key\s*[:=]\s*[A-Za-z0-9]",
]

SECRET_RE = re.compile("|".join(SECRET_PATTERNS))


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }
        if self.line is not None:
            payload["line"] = self.line
        return payload


def join_path(*parts: str, sep: str) -> str:
    return sep.join(parts)


def build_external_workspace_patterns() -> list[str]:
    active = "active"
    workspace = ("D:", "Codex")
    projects = [
        ("career-ops",),
        ("youtube-channel",),
        ("client-websites",),
        ("codex-workspace-dashboard",),
    ]
    patterns = [
        join_path(*workspace, "shared", sep="/"),
        join_path(*workspace, "shared", sep="\\"),
        join_path("..", "..", "shared", sep="/"),
        join_path("..", "..", "shared", sep="\\"),
    ]
    for project in projects:
        patterns.append(join_path(active, *project, sep="/"))
        patterns.append(join_path(active, *project, sep="\\"))
        patterns.append(join_path(*workspace, active, *project, sep="/"))
        patterns.append(join_path(*workspace, active, *project, sep="\\"))
    return patterns


EXTERNAL_WORKSPACE_PATTERNS = build_external_workspace_patterns()


def normalize_relative(path: Path) -> str:
    return path.as_posix()


def relative_to_root(root: Path, path: Path) -> str:
    return normalize_relative(path.relative_to(root))


def should_skip_path(relative_path: Path) -> bool:
    parts = relative_path.parts
    if any(part in SKIP_DIRS for part in parts):
        return True
    for prefix in SKIP_DIR_PREFIXES:
        if len(parts) >= len(prefix) and tuple(parts[: len(prefix)]) == prefix:
            return True
    return relative_path.suffix.lower() in BINARY_EXTENSIONS


def iter_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if should_skip_path(relative_path):
            continue
        suffix = path.suffix.lower()
        if suffix and suffix not in TEXT_EXTENSIONS:
            continue
        files.append(path)
    return sorted(files)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def detect_missing_required_files(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    for relative_path in REQUIRED_FILES:
        if not (root / relative_path).is_file():
            issues.append(
                Issue(
                    code="missing_required_file",
                    severity="fail",
                    path=relative_path,
                    message="Required project-local guard or documentation file is missing.",
                )
            )
    return issues


def detect_line_issues(root: Path, files: list[Path]) -> list[Issue]:
    issues: list[Issue] = []
    for path in files:
        text = read_text(path)
        if text is None:
            continue
        relative_path = relative_to_root(root, path)
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("<<<<<<< ") or stripped == "=======" or stripped.startswith(">>>>>>> "):
                issues.append(
                    Issue(
                        code="conflict_marker",
                        severity="fail",
                        path=relative_path,
                        line=line_number,
                        message="Git conflict marker found. Resolve the file before continuing.",
                    )
                )
            if SECRET_RE.search(line):
                issues.append(
                    Issue(
                        code="secret_like_value",
                        severity="fail",
                        path=relative_path,
                        line=line_number,
                        message="Secret-like value found. Move credentials to environment variables and rotate if exposed.",
                    )
                )
            if relative_path not in ALLOWED_EXTERNAL_REFERENCE_FILES:
                matched_external = any(pattern in line for pattern in EXTERNAL_WORKSPACE_PATTERNS)
                if matched_external:
                    issues.append(
                        Issue(
                            code="external_workspace_dependency",
                            severity="fail",
                            path=relative_path,
                            line=line_number,
                            message="Project file depends on material outside Emotion Aware. Adapt it locally or document it as inspiration only.",
                        )
                    )
    return issues


def load_gitignore_patterns(root: Path) -> list[str]:
    gitignore_path = root / ".gitignore"
    if not gitignore_path.is_file():
        return []
    patterns: list[str] = []
    for raw_line in gitignore_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line.replace("\\", "/"))
    return patterns


def ignore_pattern_matches(relative_path: str, pattern: str) -> bool:
    negated = pattern.startswith("!")
    if negated:
        pattern = pattern[1:]
    pattern = pattern.lstrip("/")
    if not pattern:
        return False
    if pattern.endswith("/"):
        return relative_path.startswith(pattern)
    if "/" not in pattern:
        path_parts = relative_path.split("/")
        return any(fnmatch.fnmatch(part, pattern) for part in path_parts)
    return fnmatch.fnmatch(relative_path, pattern)


def is_ignored_by_gitignore(relative_path: str, patterns: list[str]) -> bool:
    ignored = False
    for pattern in patterns:
        if ignore_pattern_matches(relative_path, pattern):
            ignored = not pattern.startswith("!")
    return ignored


def detect_unignored_generated_audio(root: Path) -> list[Issue]:
    generated_root = root / "research" / "experiments" / "generated"
    if not generated_root.is_dir():
        return []
    patterns = load_gitignore_patterns(root)
    issues: list[Issue] = []
    for path in sorted(generated_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        relative_path = relative_to_root(root, path)
        if relative_path in CURATED_GENERATED_AUDIO_FILES:
            continue
        if not is_ignored_by_gitignore(relative_path, patterns):
            issues.append(
                Issue(
                    code="generated_audio_not_ignored",
                    severity="fail",
                    path=relative_path,
                    message="Generated audio artifact is not covered by .gitignore. Keep provider outputs local unless explicitly curated.",
                )
            )
    return issues


def summarize(issues: list[Issue], files_scanned: int) -> tuple[str, dict[str, Any]]:
    failure_count = sum(1 for issue in issues if issue.severity == "fail")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    status = "fail" if failure_count else "pass"
    return status, {
        "issue_count": len(issues),
        "failure_count": failure_count,
        "warning_count": warning_count,
        "files_scanned": files_scanned,
        "auto_fixes_applied": False,
    }


def build_report(root: Path) -> dict[str, Any]:
    files = iter_scan_files(root) if root.is_dir() else []
    issues: list[Issue] = []
    if not root.is_dir():
        issues.append(Issue("missing_project_root", "fail", ".", "Project root is missing."))
    else:
        issues.extend(detect_missing_required_files(root))
        issues.extend(detect_line_issues(root, files))
        issues.extend(detect_unignored_generated_audio(root))

    issue_payload = [issue.to_dict() for issue in sorted(issues, key=lambda item: (item.severity, item.path, item.line or 0, item.code))]
    status, summary = summarize(issues, len(files))
    return {
        "project": PROJECT_NAME,
        "root": str(root),
        "status": status,
        "summary": summary,
        "issues": issue_payload,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Project Drift Guard Report",
        "",
        f"- Project: {report['project']}",
        f"- Root: `{report['root']}`",
        f"- Status: `{report['status']}`",
        f"- Issues: {report['summary']['issue_count']}",
        f"- Failures: {report['summary']['failure_count']}",
        f"- Warnings: {report['summary']['warning_count']}",
        f"- Files scanned: {report['summary']['files_scanned']}",
        f"- Auto fixes applied: {str(report['summary']['auto_fixes_applied']).lower()}",
        "",
        "## Issues",
        "",
    ]
    if not report["issues"]:
        lines.append("No project drift issues found.")
    else:
        for issue in report["issues"]:
            location = issue["path"]
            if "line" in issue:
                location = f"{location}:{issue['line']}"
            lines.append(f"- `{issue['severity']}` `{issue['code']}` `{location}`: {issue['message']}")
    lines.append("")
    return "\n".join(lines)


def print_text_report(report: dict[str, Any]) -> None:
    print(f"{report['project']} project drift guard")
    print(f"Root: {report['root']}")
    print(f"Status: {report['status']}")
    print(
        "Summary: "
        f"{report['summary']['failure_count']} failure(s), "
        f"{report['summary']['warning_count']} warning(s), "
        f"{report['summary']['files_scanned']} file(s) scanned"
    )
    print("Auto fixes applied: false")
    if report["issues"]:
        print()
        print("Issues:")
        for issue in report["issues"]:
            location = issue["path"]
            if "line" in issue:
                location = f"{location}:{issue['line']}"
            print(f"- {issue['severity'].upper()} {issue['code']} [{location}]: {issue['message']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect self-containment and safety drift in the Emotion Aware project.")
    parser.add_argument("--root", default=str(ROOT), help="Project root to scan. Defaults to this repository root.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--report-out", help="Optional Markdown report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    report = build_report(root)

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
