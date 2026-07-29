from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any

EXPECTED_INPUT_FINGERPRINTS = {
    "packages/prompts/baseline-non-adaptive.txt": "BB1FD1EAC0D4DE858BFDCE4A880BBF2C59C14A216489A1A85EF149F3E88D7FCA",
    "packages/prompts/baseline-adaptive.txt": "EBD4106841987CA4A322C2B8B95A33ECFFC4238BB476DEC611A640D5B000EB42",
    "research/experiments/cases/exp-002-dataset-derived.json": "882B94C0A31C41A94540941A254AC7E8119CADE9AAD9B071089E854917BDC7D6",
    "research/experiments/EXP-002-dataset-derived-baseline.md": "D930C845AC912D44610B3CE263B55EA03BFFD7CAB8706C2BC95CB17045FF1316",
    "research/experiments/generated/EXP-002/EXP-002-prompt-packet.md": "14017F985D54D2B46A338EA2EFA796B24202E3E5A3D3EB8223346CEA96E5CD09",
    "docs/thesis/EVALUATION_RUBRIC.md": "39D3CF33E38A0C13ADEE178F3DB4174D4D8E3A42B1DE4C274BF96FFA36FFB416",
}
DIMENSIONS = (
    "Context fit",
    "Strategy coherence",
    "Emotional appropriateness",
    "Persuasive quality",
    "Human-likeness",
)
CASE_SECTION_PATTERN = re.compile(r"(?ms)^### (EXP-002-C\d{2})\n(.*?)(?=^### |\Z)")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalized_prompt_packet_digest(path: Path) -> str:
    text = path.read_bytes().decode("utf-8")
    normalized, count = re.subn(
        r"(?m)^- Source case file: `[^`\r\n]+`(?=\r?$)",
        "- Source case file: `<normalized>`",
        text,
    )
    if count != 1:
        raise ValueError(f"expected one source-case line in {path}")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()


def _extract_response(body: str, variant: str) -> str:
    match = re.search(
        rf"(?ms)^{re.escape(variant)} response:\s*\n`([^`\r\n]+)`",
        body,
    )
    if match is None or not match.group(1).strip():
        raise ValueError(f"missing frozen {variant} response")
    return match.group(1)


def _extract_scores(body: str, variant: str) -> dict[str, int]:
    match = re.search(
        rf"(?m)^- {re.escape(variant)}:\s*$\n(?P<lines>(?:  - [^\r\n]+\r?\n){{6}})",
        body,
    )
    if match is None:
        raise ValueError(f"missing {variant} score block")
    pairs = re.findall(r"(?m)^  - ([A-Za-z -]+): (\d+)$", match.group("lines"))
    scores = {label: int(value) for label, value in pairs}
    if len(pairs) != 6 or set(scores) != {*DIMENSIONS, "Total"}:
        raise ValueError(f"{variant} score fields mismatch")
    if any(not 1 <= scores[dimension] <= 5 for dimension in DIMENSIONS):
        raise ValueError(f"{variant} dimension score is outside 1..5")
    if scores["Total"] != sum(scores[dimension] for dimension in DIMENSIONS):
        raise ValueError(f"{variant} recorded total does not equal its dimensions")
    return scores


def parse_frozen_response_baseline(markdown: str, case_ids: list[str]) -> list[dict[str, Any]]:
    sections = CASE_SECTION_PATTERN.findall(markdown)
    if len(sections) != len(case_ids) or [case_id for case_id, _ in sections] != case_ids:
        raise ValueError("frozen response sections do not exactly match the case file")
    parsed: list[dict[str, Any]] = []
    for case_id, body in sections:
        non_adaptive_response = _extract_response(body, "Non-adaptive")
        adaptive_response = _extract_response(body, "Adaptive")
        non_adaptive_scores = _extract_scores(body, "Non-adaptive")
        adaptive_scores = _extract_scores(body, "Adaptive")
        preferred_match = re.search(r"(?m)^Preferred: (Adaptive|Non-adaptive|Tie)\s*$", body)
        if preferred_match is None or re.search(r"(?ms)^Why:\s*\n\s*\n\S", body) is None:
            raise ValueError(f"{case_id} lacks a recorded preference or rationale")
        computed_preference = (
            "Adaptive"
            if adaptive_scores["Total"] > non_adaptive_scores["Total"]
            else "Non-adaptive"
            if non_adaptive_scores["Total"] > adaptive_scores["Total"]
            else "Tie"
        )
        if preferred_match.group(1) != computed_preference:
            raise ValueError(f"{case_id} recorded preference disagrees with total scores")
        parsed.append({
            "case_id": case_id,
            "response_sha256": {
                "non_adaptive": hashlib.sha256(non_adaptive_response.encode("utf-8")).hexdigest().upper(),
                "adaptive": hashlib.sha256(adaptive_response.encode("utf-8")).hexdigest().upper(),
            },
            "scores": {
                "non_adaptive": non_adaptive_scores,
                "adaptive": adaptive_scores,
            },
            "preferred": computed_preference,
        })
    return parsed


def _average(total: int, count: int) -> float:
    value = (Decimal(total) / Decimal(count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(value)


def build_frozen_baseline_result(root: Path) -> dict[str, Any]:
    actual_fingerprints = {
        relative_path: sha256_file(root / relative_path)
        for relative_path in EXPECTED_INPUT_FINGERPRINTS
    }
    if actual_fingerprints != EXPECTED_INPUT_FINGERPRINTS:
        raise ValueError("frozen EXP-002 baseline input drift")
    cases = json.loads((root / "research" / "experiments" / "cases" / "exp-002-dataset-derived.json").read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) != 6:
        raise ValueError("EXP-002 case file must contain exactly six cases")
    case_ids = [case["case_id"] for case in cases]
    markdown = (root / "research" / "experiments" / "EXP-002-dataset-derived-baseline.md").read_text(encoding="utf-8")
    parsed = parse_frozen_response_baseline(markdown, case_ids)
    non_adaptive_total = sum(item["scores"]["non_adaptive"]["Total"] for item in parsed)
    adaptive_total = sum(item["scores"]["adaptive"]["Total"] for item in parsed)
    summary = {
        "case_count": len(parsed),
        "response_count": len(parsed) * 2,
        "adaptive_preferred_count": sum(item["preferred"] == "Adaptive" for item in parsed),
        "non_adaptive_preferred_count": sum(item["preferred"] == "Non-adaptive" for item in parsed),
        "tie_count": sum(item["preferred"] == "Tie" for item in parsed),
        "non_adaptive_average_total": _average(non_adaptive_total, len(parsed)),
        "adaptive_average_total": _average(adaptive_total, len(parsed)),
    }
    return {
        "checkpoint_id": "EXP-002-frozen-response-baseline",
        "schema_version": 1,
        "status": "frozen_response_score_arithmetic_runnable_and_recorded",
        "input_fingerprints": actual_fingerprints,
        "response_generation_performed": False,
        "semantic_judgment_recomputed": False,
        "evaluator_provenance_status": "not_recorded",
        "score_arithmetic_recomputed": True,
        "cases": parsed,
        "summary": summary,
    }


def render_frozen_baseline_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join([
        "# Frozen EXP-002 Response Baseline",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Responses: `{summary['response_count']}`",
        f"- Adaptive preferred: `{summary['adaptive_preferred_count']}`",
        f"- Non-adaptive average: `{summary['non_adaptive_average_total']}`",
        f"- Adaptive average: `{summary['adaptive_average_total']}`",
        f"- Score arithmetic recomputed: `{payload['score_arithmetic_recomputed']}`",
        f"- Response generation performed: `{payload['response_generation_performed']}`",
        f"- Semantic judgment recomputed: `{payload['semantic_judgment_recomputed']}`",
        f"- Evaluator provenance status: `{payload['evaluator_provenance_status']}`",
        "",
        "This is a deterministic rerun of frozen response/rating structure and arithmetic. It is not fresh response generation or fresh semantic evaluation. The frozen record does not establish evaluator type, identity or role, count, or procedure.",
        "",
    ])


def frozen_baseline_self_check(root: Path) -> str:
    payload = build_frozen_baseline_result(root)
    if payload["summary"] != {
        "case_count": 6,
        "response_count": 12,
        "adaptive_preferred_count": 6,
        "non_adaptive_preferred_count": 0,
        "tie_count": 0,
        "non_adaptive_average_total": 18.67,
        "adaptive_average_total": 23.67,
    }:
        raise AssertionError("frozen baseline summary mismatch")
    markdown_path = root / "research" / "experiments" / "EXP-002-dataset-derived-baseline.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    case_ids = [item["case_id"] for item in payload["cases"]]
    tampered = markdown.replace("  - Total: 18", "  - Total: 19", 1)
    try:
        parse_frozen_response_baseline(tampered, case_ids)
    except ValueError:
        pass
    else:
        raise AssertionError("tampered frozen score unexpectedly passed")
    return "pass"
