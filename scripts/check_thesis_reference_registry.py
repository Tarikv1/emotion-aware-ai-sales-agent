#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_NAME = "emotion-aware-ai-sales-agent"
ROOT = Path(__file__).resolve().parents[1]

REFERENCE_FILES = [
    "docs/thesis/THESIS_REFERENCE_REGISTRY.md",
    "docs/thesis/SPEECH_REALISM_REFERENCES.md",
    "docs/third-party-inspirations.md",
]

SCAN_PREFIXES = [
    "AGENTS.md",
    "README.md",
    "program.md",
    "docs",
    "research",
    "scripts",
    "packages",
    "db",
]

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

SKIP_DIRS = {
    ".git",
    ".tmp",
    "__pycache__",
    "node_modules",
}

SKIP_DIR_PREFIXES = {
    ("config", "local"),
    ("data", "private"),
    ("data", "private-restricted"),
    ("data", "processed"),
    ("research", "experiments", "generated"),
}

ALLOWED_NON_REFERENCE_URL_PREFIXES = (
    "http://127.0.0.1",
    "https://127.0.0.1",
    "http://localhost",
    "https://localhost",
    "http://0.0.0.0",
    "https://0.0.0.0",
    "https://api.cartesia.ai",
    "wss://api.cartesia.ai",
    "https://api.elevenlabs.io",
    "https://api.openai.com",
)

ALLOWED_NON_REFERENCE_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "schemas.example.test",
}

URL_RE = re.compile(r"\b(?:https?|wss?)://[^\s<>\]\[()\"'`{}]+")
TRAILING_PUNCTUATION = ".,;:!?"


@dataclass(frozen=True)
class Issue:
    code: str
    severity: str
    path: str
    message: str
    line: int | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }
        if self.line is not None:
            payload["line"] = self.line
        if self.url is not None:
            payload["url"] = self.url
        return payload


def normalize_relative(path: Path) -> str:
    return path.as_posix()


def relative_to_root(root: Path, path: Path) -> str:
    return normalize_relative(path.relative_to(root))


def normalize_url(raw_url: str) -> str:
    url = raw_url.rstrip(TRAILING_PUNCTUATION)
    while url.endswith((")", "]")) and not any(ch in url[:-1] for ch in "(["):
        url = url[:-1]
    return url


def extract_urls(text: str) -> set[str]:
    return {normalize_url(match.group(0)) for match in URL_RE.finditer(text)}


def url_domain(url: str) -> str:
    without_scheme = url.split("://", 1)[-1]
    return without_scheme.split("/", 1)[0].split(":", 1)[0].lower()


def is_allowed_non_reference_url(url: str) -> bool:
    if url.startswith(ALLOWED_NON_REFERENCE_URL_PREFIXES):
        return True
    return url_domain(url) in ALLOWED_NON_REFERENCE_DOMAINS


def should_scan_relative(relative_path: Path) -> bool:
    relative_text = normalize_relative(relative_path)
    return any(relative_text == prefix or relative_text.startswith(f"{prefix}/") for prefix in SCAN_PREFIXES)


def should_skip_path(relative_path: Path) -> bool:
    parts = relative_path.parts
    if any(part in SKIP_DIRS for part in parts):
        return True
    for prefix in SKIP_DIR_PREFIXES:
        if len(parts) >= len(prefix) and tuple(parts[: len(prefix)]) == prefix:
            return True
    return False


def iter_scan_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if should_skip_path(relative_path):
            continue
        if not should_scan_relative(relative_path):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        files.append(path)
    return sorted(files)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def load_registered_urls(root: Path) -> tuple[set[str], list[Issue]]:
    registered_urls: set[str] = set()
    issues: list[Issue] = []
    for relative_path in REFERENCE_FILES:
        path = root / relative_path
        if not path.is_file():
            issues.append(
                Issue(
                    code="missing_reference_file",
                    severity="fail",
                    path=relative_path,
                    message="Required reference registry file is missing.",
                )
            )
            continue
        text = read_text(path)
        if text is None:
            issues.append(
                Issue(
                    code="unreadable_reference_file",
                    severity="fail",
                    path=relative_path,
                    message="Required reference registry file could not be read as UTF-8 text.",
                )
            )
            continue
        registered_urls.update(extract_urls(text))
    return registered_urls, issues


def detect_unregistered_urls(root: Path, registered_urls: set[str], files: list[Path]) -> list[Issue]:
    issues: list[Issue] = []
    reference_file_set = set(REFERENCE_FILES)
    seen_locations: set[tuple[str, int, str]] = set()
    for path in files:
        relative_path = relative_to_root(root, path)
        if relative_path in reference_file_set:
            continue
        text = read_text(path)
        if text is None:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            for raw_url in URL_RE.findall(line):
                url = normalize_url(raw_url)
                if url in registered_urls or is_allowed_non_reference_url(url):
                    continue
                location_key = (relative_path, line_number, url)
                if location_key in seen_locations:
                    continue
                seen_locations.add(location_key)
                issues.append(
                    Issue(
                        code="unregistered_external_reference",
                        severity="fail",
                        path=relative_path,
                        line=line_number,
                        url=url,
                        message=(
                            "External URL is used outside the thesis/source registry. "
                            "Add it to docs/thesis/THESIS_REFERENCE_REGISTRY.md or docs/third-party-inspirations.md."
                        ),
                    )
                )
    return issues


def summarize(issues: list[Issue], files_scanned: int, registered_url_count: int) -> tuple[str, dict[str, Any]]:
    failure_count = sum(1 for issue in issues if issue.severity == "fail")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    status = "fail" if failure_count else "pass"
    return status, {
        "issue_count": len(issues),
        "failure_count": failure_count,
        "warning_count": warning_count,
        "files_scanned": files_scanned,
        "registered_url_count": registered_url_count,
        "network_calls_made": False,
        "auto_fixes_applied": False,
    }


def build_report(root: Path) -> dict[str, Any]:
    files = iter_scan_files(root) if root.is_dir() else []
    registered_urls, issues = load_registered_urls(root) if root.is_dir() else (set(), [])
    if not root.is_dir():
        issues.append(Issue("missing_project_root", "fail", ".", "Project root is missing."))
    else:
        issues.extend(detect_unregistered_urls(root, registered_urls, files))

    issue_payload = [issue.to_dict() for issue in sorted(issues, key=lambda item: (item.path, item.line or 0, item.code))]
    status, summary = summarize(issues, len(files), len(registered_urls))
    return {
        "project": PROJECT_NAME,
        "root": str(root),
        "status": status,
        "summary": summary,
        "issues": issue_payload,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Thesis Reference Registry Guard Report",
        "",
        f"- Project: {report['project']}",
        f"- Root: `{report['root']}`",
        f"- Status: `{report['status']}`",
        f"- Issues: {report['summary']['issue_count']}",
        f"- Failures: {report['summary']['failure_count']}",
        f"- Warnings: {report['summary']['warning_count']}",
        f"- Files scanned: {report['summary']['files_scanned']}",
        f"- Registered URLs: {report['summary']['registered_url_count']}",
        f"- Network calls made: {str(report['summary']['network_calls_made']).lower()}",
        f"- Auto fixes applied: {str(report['summary']['auto_fixes_applied']).lower()}",
        "",
        "## Issues",
        "",
    ]
    if not report["issues"]:
        lines.append("No unregistered external references found.")
    else:
        for issue in report["issues"]:
            location = issue["path"]
            if "line" in issue:
                location = f"{location}:{issue['line']}"
            url = f" `{issue['url']}`" if "url" in issue else ""
            lines.append(f"- `{issue['severity']}` `{issue['code']}` `{location}`{url}: {issue['message']}")
    lines.append("")
    return "\n".join(lines)


def print_text_report(report: dict[str, Any]) -> None:
    print(f"{report['project']} thesis reference registry guard")
    print(f"Root: {report['root']}")
    print(f"Status: {report['status']}")
    print(
        "Summary: "
        f"{report['summary']['failure_count']} failure(s), "
        f"{report['summary']['warning_count']} warning(s), "
        f"{report['summary']['files_scanned']} file(s) scanned, "
        f"{report['summary']['registered_url_count']} registered URL(s)"
    )
    print("Network calls made: false")
    print("Auto fixes applied: false")
    if report["issues"]:
        print()
        print("Issues:")
        for issue in report["issues"]:
            location = issue["path"]
            if "line" in issue:
                location = f"{location}:{issue['line']}"
            url = f" {issue['url']}" if "url" in issue else ""
            print(f"- {issue['severity'].upper()} {issue['code']} [{location}]{url}: {issue['message']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check that external source URLs are recorded for thesis traceability.")
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
