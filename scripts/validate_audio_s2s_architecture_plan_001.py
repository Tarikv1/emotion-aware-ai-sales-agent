#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "runtime" / "audio_backends" / "speech_to_speech_architecture_plan.json"
EVIDENCE_DIR = ROOT / "research" / "experiments" / "generated" / "LOCAL-AUDIO-S2S-ARCHITECTURE-PLAN-001"
REQUIRED_PIPELINES = {"current_modular_path", "liquid_inspired_future_path"}
REQUIRED_BOUNDARIES = {
    "sales/conversation brain",
    "campaign facts",
    "source grounding",
    "memory ledger",
    "safety verifier",
}
REQUIRED_QUESTIONS = {
    "Can Liquid run locally on RTX 4070 Super 12GB?",
    "Can it do ASR on known bad phrases?",
    "Can it produce TTS fast enough?",
    "Can interleaved generation reduce time-to-first-audio?",
    "Can we extract transcript text for verifier/memory?",
    "Can we prevent hallucinated product facts?",
    "Can generated audio be gated by verifier before playback?",
    "Is streaming partial audio safe in a sales conversation?",
    "What must be blocked from live use until verified?"
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AssertionError(f"missing file: {rel(path)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError(f"{rel(path)} must be a JSON object")
    return payload


def main() -> int:
    failures: list[str] = []
    plan = load_json(PLAN_PATH)
    if plan.get("plan_id") != "local-audio-s2s-architecture-plan-001":
        failures.append("wrong plan_id")
    pipelines = plan.get("pipelines") if isinstance(plan.get("pipelines"), list) else []
    pipeline_ids = {item.get("pipeline_id") for item in pipelines if isinstance(item, dict)}
    missing_pipelines = sorted(REQUIRED_PIPELINES - pipeline_ids)
    if missing_pipelines:
        failures.append(f"missing pipelines: {missing_pipelines}")

    boundaries = set(plan.get("project_owned_boundaries") or [])
    missing_boundaries = sorted(REQUIRED_BOUNDARIES - boundaries)
    if missing_boundaries:
        failures.append(f"missing project-owned boundaries: {missing_boundaries}")

    questions = set(plan.get("feasibility_questions") or [])
    missing_questions = sorted(REQUIRED_QUESTIONS - questions)
    if missing_questions:
        failures.append(f"missing feasibility questions: {missing_questions}")

    text = PLAN_PATH.read_text(encoding="utf-8").lower()
    if "must not become the unverified sales" not in text:
        failures.append("plan must state Liquid must not become the unverified sales brain")
    if "before verifier gate" not in text and "before verifier gating" not in text:
        failures.append("plan must block partial audio before verifier gating")

    flags = plan.get("boundary_flags") if isinstance(plan.get("boundary_flags"), dict) else {}
    for key in (
        "live_runtime_allowed",
        "provider_calls_made",
        "openai_api_calls_made",
        "elevenlabs_calls_made",
        "live_tts_calls_made",
        "local_model_generation_made",
        "model_downloads_performed",
        "runtime_behavior_changed",
        "response_text_changed",
        "raw_private_transcripts_included",
    ):
        if flags.get(key) is not False:
            failures.append(f"boundary_flags.{key} must be false")

    for evidence_name in ("result.json", "report.md"):
        if not (EVIDENCE_DIR / evidence_name).is_file():
            failures.append(f"missing evidence: {rel(EVIDENCE_DIR / evidence_name)}")

    result = {
        "status": "pass" if not failures else "fail",
        "plan": rel(PLAN_PATH),
        "evidence_dir": rel(EVIDENCE_DIR),
        "failures": failures,
        "provider_calls_made": False,
        "model_downloads_performed": False,
        "runtime_behavior_changed": False,
        "response_text_changed": False
    }
    print(json.dumps(result, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
