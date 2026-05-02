#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2_000_000
DEFAULT_MAX_LINES = 240

BLOCKED_SEGMENTS = {
    ".git",
    ".tmp",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "private-restricted",
}

BLOCKED_NAME_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"^\.env",
        r"secret",
        r"credential",
        r"token",
        r"private[-_]?key",
        r"\.pem$",
        r"\.pfx$",
        r"\.p12$",
        r"\.key$",
        r"id_rsa",
    ]
]


def fail(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def is_blocked_path(path: Path) -> bool:
    if any(part in BLOCKED_SEGMENTS for part in path.parts):
        return True
    text = str(path)
    name = path.name
    return any(pattern.search(name) or pattern.search(text) for pattern in BLOCKED_NAME_PATTERNS)


def normalize_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def resolve_safe_path(raw_path: str) -> Path:
    if not raw_path:
        fail("--path is required.")
    path = Path(raw_path)
    resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    if not is_relative_to(resolved, ROOT) or is_blocked_path(resolved):
        fail("Blocked path", 2)
    if not resolved.is_file():
        fail("Not a file", 2)
    if resolved.stat().st_size > MAX_BYTES:
        fail(f"File is above the {MAX_BYTES} byte relevant-reader limit.", 2)
    return resolved


def read_lines(raw_path: str) -> tuple[Path, list[str]]:
    path = resolve_safe_path(raw_path)
    text = path.read_text(encoding="utf-8")
    if "\0" in text:
        fail("Binary-like file", 2)
    return path, text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def numbered_lines(lines: list[str], start: int, end: int) -> list[dict[str, Any]]:
    return [
        {"number": number, "text": lines[number - 1]}
        for number in range(start, end + 1)
    ]


def render_lines(lines: list[dict[str, Any]]) -> str:
    return "\n".join(f"{line['number']}: {line['text']}" for line in lines)


def with_summary(payload: dict[str, Any]) -> dict[str, Any]:
    payload["summary"] = {
        "network_calls_made": False,
        "secret_values_logged": False,
    }
    return payload


def command_outline(args: argparse.Namespace) -> dict[str, Any]:
    path, lines = read_lines(args.path)
    headings = []
    symbols = []
    for index, line in enumerate(lines, start=1):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            headings.append({
                "line": index,
                "level": len(heading.group(1)),
                "title": heading.group(2).strip(),
            })
            continue
        symbol = (
            re.match(r"\s*def\s+([A-Za-z_]\w*)\s*\(", line)
            or re.match(r"\s*class\s+([A-Za-z_]\w*)\b", line)
        )
        if symbol:
            symbols.append({
                "line": index,
                "name": symbol.group(1),
                "preview": line.strip(),
            })
    return with_summary({
        "path": normalize_path(path),
        "total_lines": len(lines),
        "headings": headings,
        "symbols": symbols,
    })


def command_slice(args: argparse.Namespace) -> dict[str, Any]:
    start = args.start
    end = args.end
    if start < 1:
        fail("--start must be a positive integer.")
    if end < start:
        fail("--end must be greater than or equal to --start.")

    path, lines = read_lines(args.path)
    final_end = min(end, start + args.max_lines - 1, len(lines))
    chunk = numbered_lines(lines, start, final_end)
    return with_summary({
        "path": normalize_path(path),
        "start": start,
        "end": final_end,
        "total_lines": len(lines),
        "truncated": end > final_end,
        "lines": chunk,
        "text": render_lines(chunk),
    })


def command_find(args: argparse.Namespace) -> dict[str, Any]:
    query = args.query.strip()
    if not query:
        fail("--query is required.")
    path, lines = read_lines(args.path)
    needle = query.lower()
    matches = []
    context = max(0, args.context)
    for index, line in enumerate(lines, start=1):
        if needle not in line.lower():
            continue
        start = max(1, index - context)
        end = min(len(lines), index + context)
        matches.append({
            "line": index,
            "text": line,
            "context": numbered_lines(lines, start, end),
        })
        if len(matches) >= args.limit:
            break
    return with_summary({
        "path": normalize_path(path),
        "query": query,
        "total_lines": len(lines),
        "matches": matches,
    })


def command_section(args: argparse.Namespace) -> dict[str, Any]:
    heading_query = args.heading.strip().lower()
    if not heading_query:
        fail("--heading is required.")
    path, lines = read_lines(args.path)
    start_index = -1
    heading_level = 0
    heading_title = ""
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading and heading.group(2).strip().lower() == heading_query:
            start_index = index
            heading_level = len(heading.group(1))
            heading_title = heading.group(2).strip()
            break
    if start_index == -1:
        fail("Heading not found", 2)

    end_index = len(lines) - 1
    for index in range(start_index + 1, len(lines)):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", lines[index])
        if heading and len(heading.group(1)) <= heading_level:
            end_index = index - 1
            break

    chunk = numbered_lines(lines, start_index + 1, end_index + 1)
    return with_summary({
        "path": normalize_path(path),
        "heading": heading_title,
        "start": start_index + 1,
        "end": end_index + 1,
        "total_lines": len(lines),
        "lines": chunk,
        "text": render_lines(chunk),
    })


def print_text(payload: dict[str, Any], mode: str) -> None:
    print(f"File: {payload['path']}")
    if mode == "outline":
        print(f"Total lines: {payload['total_lines']}")
        print("\nHeadings:")
        if payload["headings"]:
            for heading in payload["headings"]:
                print(f"{heading['line']}: {'#' * heading['level']} {heading['title']}")
        else:
            print("- none")
        if payload["symbols"]:
            print("\nSymbols:")
            for symbol in payload["symbols"]:
                print(f"{symbol['line']}: {symbol['name']}")
        return

    if mode == "find":
        print(f"Query: {payload['query']}")
        print(f"Matches: {len(payload['matches'])}\n")
        if not payload["matches"]:
            print("No matches.")
            return
        for match in payload["matches"]:
            print(f"Match at line {match['line']}: {match['text']}")
            for line in match["context"]:
                print(f"{line['number']}: {line['text']}")
            print()
        return

    print(f"Lines: {payload['start']}-{payload['end']} of {payload['total_lines']}")
    print()
    print(payload["text"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read only relevant slices of product-local files.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    outline = subparsers.add_parser("outline", help="Show headings and lightweight symbols.")
    outline.add_argument("--path", required=True)
    outline.add_argument("--json", action="store_true")

    slice_parser = subparsers.add_parser("slice", help="Show a bounded line range.")
    slice_parser.add_argument("--path", required=True)
    slice_parser.add_argument("--start", required=True, type=int)
    slice_parser.add_argument("--end", required=True, type=int)
    slice_parser.add_argument("--max-lines", default=DEFAULT_MAX_LINES, type=int)
    slice_parser.add_argument("--json", action="store_true")

    find = subparsers.add_parser("find", help="Find a query with nearby context.")
    find.add_argument("--path", required=True)
    find.add_argument("--query", required=True)
    find.add_argument("--context", default=2, type=int)
    find.add_argument("--limit", default=25, type=int)
    find.add_argument("--json", action="store_true")

    section = subparsers.add_parser("section", help="Show a Markdown section by heading.")
    section.add_argument("--path", required=True)
    section.add_argument("--heading", required=True)
    section.add_argument("--json", action="store_true")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "outline":
        payload = command_outline(args)
    elif args.command == "slice":
        payload = command_slice(args)
    elif args.command == "find":
        payload = command_find(args)
    elif args.command == "section":
        payload = command_section(args)
    else:
        fail("Unknown command.")

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_text(payload, args.command)


if __name__ == "__main__":
    main()
