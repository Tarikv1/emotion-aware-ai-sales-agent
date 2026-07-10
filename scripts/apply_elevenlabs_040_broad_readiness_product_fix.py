#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import apply_elevenlabs_038_end_call_terminal_control as patcher


CHECKPOINT_ID = "ELEVENLABS-040-broad-live-readiness"
CONFIRMATION = "confirm-provider-write"
DOCUMENTS = {
    "price-scope": "atlas_price_scope_cost_drivers.md",
    "output-quality": "atlas_output_quality_rules.md",
}
OUT_DIR = patcher.ROOT / "research/experiments/generated" / CHECKPOINT_ID


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Update only the canonical Atlas price/scope KB document."
    )
    parser.add_argument(
        "--confirm-provider-write",
        choices=(CONFIRMATION,),
        required=True,
    )
    parser.add_argument("--document", choices=tuple(DOCUMENTS), required=True)
    return parser.parse_args()


def write_evidence(name: str, payload: dict[str, object]) -> None:
    patcher.write_json(OUT_DIR / name, patcher.sanitize(payload))


def main() -> int:
    args = parse_args()
    api_key = os.environ.get(patcher.API_KEY_ENV_VAR)
    if not api_key:
        raise SystemExit(f"{patcher.API_KEY_ENV_VAR} is not set")

    agent_id = patcher.DEFAULT_AGENT_ID
    target_document = DOCUMENTS[args.document]
    source_path = (
        patcher.ROOT
        / "runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio"
        / target_document
    )
    pre = patcher.json_request(
        "GET", f"/v1/convai/agents/{agent_id}", api_key=api_key
    )["response"]
    patcher.validate_target_agent(
        pre, agent_id, {patcher.EXPECTED_AGENT_NAME}
    )
    canonical, _selection = patcher.select_canonical_kb_docs(pre, api_key)
    entry = next(
        (item for item in canonical if item.get("name") == target_document),
        None,
    )
    if not entry:
        raise RuntimeError(f"canonical KB document {target_document!r} not found")
    if entry.get("type") != "file":
        raise RuntimeError("canonical price/scope KB document is not file-backed")

    source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
    before_fingerprint = patcher.unrelated_tool_fingerprint(pre)
    write_evidence(
        f"live_product_kb_patch_{args.document}_request.json",
        {
            "checkpoint_id": CHECKPOINT_ID,
            "request_id": f"update_kb_file::{target_document}",
            "method": "PATCH",
            "document_id": entry["id"],
            "document_name": target_document,
            "source_path": patcher.rel(source_path),
            "source_sha256": source_sha256,
            "outbound_calls_made": False,
        },
    )

    result = patcher.multipart_update_file(
        api_key=api_key,
        documentation_id=str(entry["id"]),
        source_path=source_path,
    )
    post = patcher.json_request(
        "GET", f"/v1/convai/agents/{agent_id}", api_key=api_key
    )["response"]
    patcher.validate_target_agent(
        post, agent_id, {patcher.EXPECTED_AGENT_NAME}
    )
    patcher.assert_unrelated_tool_fingerprint_unchanged(
        before_fingerprint,
        patcher.unrelated_tool_fingerprint(post),
        context=CHECKPOINT_ID,
    )
    patcher.assert_protected_unrelated_state_unchanged(
        pre, post, context=CHECKPOINT_ID
    )

    actual_kb = patcher.kb_signature(
        patcher.get_prompt(post).get("knowledge_base", [])
    )
    expected_kb = patcher.kb_signature(canonical)
    if actual_kb != expected_kb:
        raise RuntimeError("KB IDs or order changed during price/scope update")

    payload = {
        "checkpoint_id": CHECKPOINT_ID,
        "status": "passed",
        "agent_id": agent_id,
        "agent_name": post.get("name"),
        "document_id": entry["id"],
        "document_name": target_document,
        "source_sha256": source_sha256,
        "status_code": result.get("status_code"),
        "kb_count": len(actual_kb),
        "kb_ids_order_preserved": True,
        "unrelated_tool_fingerprint_preserved": True,
        "protected_state_preserved": True,
        "procedures_inactive": not bool(post.get("procedures")),
        "simulations_run": False,
        "outbound_calls_made": False,
    }
    write_evidence(f"live_product_kb_patch_{args.document}_result.json", payload)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
