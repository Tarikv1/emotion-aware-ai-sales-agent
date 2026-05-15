#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.entrypoints.generate_guarded_response import build_guarded_response_packet
from runtime.entrypoints.realtime_turn_cli import find_campaign
from runtime.core.realtime_turns import load_realtime_cases
from runtime.voice.runtime_voice_delivery import attach_runtime_voice_delivery


DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_OUT_DIR = ROOT / "research" / "experiments" / "generated" / "RESP-002-bilingual-voice-parity"


PARITY_CASES = [
    {
        "case_id": "RESP-002-PARITY-DE-OBJECTION",
        "pair_id": "objection",
        "language": "de",
        "campaign_id": "campaign-prod-005-b2c-telecom",
        "stage": "relevance-check",
        "transcript": "Das klingt zu teuer.",
        "candidate_response": "Ich habe verstanden. Wenn es passt, gibt es einen kurzen naechsten Schritt.",
        "required_spoken_fragments": ["Ich hab", "Wenn's", "gibt's"],
        "forbidden_spoken_fragments": ["Ich habe", "Wenn es", "gibt es"],
    },
    {
        "case_id": "RESP-002-PARITY-EN-OBJECTION",
        "pair_id": "objection",
        "language": "en",
        "campaign_id": "campaign-prod-005-b2b-software",
        "stage": "relevance-check",
        "transcript": "That sounds expensive.",
        "candidate_response": "I will keep this simple. You are right to ask. It is only useful if there is a practical next step.",
        "required_spoken_fragments": ["I'll", "You're", "It's", "there's"],
        "forbidden_spoken_fragments": ["I will", "You are", "It is", "there is"],
    },
    {
        "case_id": "RESP-002-PARITY-DE-TRUST",
        "pair_id": "trust",
        "language": "de",
        "campaign_id": "campaign-prod-005-b2c-telecom",
        "stage": "relevance-check",
        "transcript": "Ich kenne Sie nicht. Warum sollte ich Ihnen glauben?",
        "candidate_response": "Ich habe verstanden. Wenn es hilft, geht es nur um eine kurze Einordnung.",
        "required_spoken_fragments": ["Ich hab", "Wenn's", "geht's"],
        "forbidden_spoken_fragments": ["Ich habe", "Wenn es", "geht es"],
    },
    {
        "case_id": "RESP-002-PARITY-EN-TRUST",
        "pair_id": "trust",
        "language": "en",
        "campaign_id": "campaign-prod-005-b2b-software",
        "stage": "relevance-check",
        "transcript": "I do not know your company. Why should I trust this?",
        "candidate_response": "I am not asking you to decide now. That is why I will keep it brief.",
        "required_spoken_fragments": ["I'm", "That's", "I'll"],
        "forbidden_spoken_fragments": ["I am", "That is", "I will"],
    },
    {
        "case_id": "RESP-002-PARITY-DE-NEXT-STEP",
        "pair_id": "next_step",
        "language": "de",
        "campaign_id": "campaign-prod-005-b2c-telecom",
        "stage": "relevance-check",
        "transcript": "Vielleicht, aber ich will mich nicht festlegen.",
        "candidate_response": "Ich habe verstanden. Wenn es passt, macht es Sinn, einen kurzen Rueckruf zu planen.",
        "required_spoken_fragments": ["Ich hab", "Wenn's", "macht's"],
        "forbidden_spoken_fragments": ["Ich habe", "Wenn es", "macht es"],
    },
    {
        "case_id": "RESP-002-PARITY-EN-NEXT-STEP",
        "pair_id": "next_step",
        "language": "en",
        "campaign_id": "campaign-prod-005-b2b-software",
        "stage": "relevance-check",
        "transcript": "Maybe, but I do not want to commit.",
        "candidate_response": "I would suggest one simple next step. We will keep it practical, and you are free to say no.",
        "required_spoken_fragments": ["I'd", "We'll", "you're"],
        "forbidden_spoken_fragments": ["I would", "We will", "you are"],
    },
]


def resolve_path(path_text: str | None, default: Path) -> Path:
    if not path_text:
        return default
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def contains_any(text: str, fragments: list[str]) -> bool:
    return any(fragment in text for fragment in fragments)


def collect_metrics(case: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    delivery = packet["voice_delivery"]
    validation = delivery["validation"]
    spoken = delivery["spoken_text_normalization"]
    speech_realism = delivery["speech_realism"]
    speech_interaction = delivery["speech_interaction"]
    imperfections = delivery["speech_imperfections"]
    provider = delivery["provider_rendering"]
    spoken_text = spoken["tts_text"]
    provider_text = provider["rendered_text"]
    required_fragments_present = all(fragment in spoken_text for fragment in case["required_spoken_fragments"])
    forbidden_fragments_absent = not contains_any(spoken_text, case["forbidden_spoken_fragments"])
    return {
        "case_id": case["case_id"],
        "pair_id": case["pair_id"],
        "language": case["language"],
        "campaign_id": case["campaign_id"],
        "final_response": packet["final_response"],
        "spoken_tts_text": spoken_text,
        "provider_rendered_text": provider_text,
        "final_response_unchanged": delivery["final_response_unchanged"],
        "provider_calls_made": delivery["provider_calls_made"],
        "customer_audio_uploaded": delivery["customer_audio_uploaded"],
        "voice_cloning_used": delivery["voice_cloning_used"],
        "validation_passed": validation["passed"],
        "spoken_normalization_count": spoken["normalization_count"],
        "speech_realism_bundle_count": len(speech_realism.get("bundles", [])),
        "interaction_marker_count": speech_interaction["marker_count"],
        "imperfection_count": imperfections["imperfection_count"],
        "prosody_cue_count": delivery["prosody"]["cue_count"],
        "pacing_tuned_segment_count": delivery["voice_pacing_calibration"]["tuned_segment_count"],
        "pacing_average_speed_ratio": delivery["voice_pacing_calibration"]["average_speed_ratio"],
        "connected_speech_flow_join_count": delivery["voice_connected_speech"]["flow_join_count"],
        "listening_adjustment_count": delivery["voice_listening_calibration"]["listening_adjustment_count"],
        "emotion_smoothed_transition_count": delivery["voice_emotion_smoothing"]["smoothed_transition_count"],
        "semantic_emphasis_rewrite_count": delivery["voice_semantic_emphasis"]["rewrite_count"],
        "low_pressure_focus_rewrite_count": delivery["voice_low_pressure_focus"]["rewrite_count"],
        "provider_tag_count": provider["provider_tag_count"],
        "protected_segment_provider_tag_count": provider["protected_segment_provider_tag_count"],
        "required_spoken_fragments_present": required_fragments_present,
        "forbidden_spoken_fragments_absent": forbidden_fragments_absent,
        "provider_rendering_changed": provider_text != packet["final_response"],
        "safe": (
            validation["passed"]
            and delivery["final_response_unchanged"] is True
            and delivery["provider_calls_made"] is False
            and delivery["customer_audio_uploaded"] is False
            and delivery["voice_cloning_used"] is False
            and required_fragments_present
            and forbidden_fragments_absent
            and spoken["normalization_count"] >= 1
            and delivery["prosody"]["cue_count"] >= 1
            and delivery["voice_pacing_calibration"]["tuned_segment_count"] >= 1
            and delivery["voice_emotion_smoothing"]["smoothed_transition_count"] >= 1
            and provider["protected_segment_provider_tag_count"] == 0
            and provider_text != packet["final_response"]
        ),
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_language = {
        language: [row for row in rows if row["language"] == language]
        for language in sorted({row["language"] for row in rows})
    }
    by_pair = {
        pair_id: [row for row in rows if row["pair_id"] == pair_id]
        for pair_id in sorted({row["pair_id"] for row in rows})
    }
    return {
        "case_count": len(rows),
        "safe_case_count": sum(1 for row in rows if row["safe"]),
        "unsafe_case_count": sum(1 for row in rows if not row["safe"]),
        "languages": sorted(by_language),
        "language_counts": {language: len(items) for language, items in by_language.items()},
        "pair_counts": {pair_id: len(items) for pair_id, items in by_pair.items()},
        "matched_pair_count": sum(
            1 for items in by_pair.values()
            if {row["language"] for row in items} == {"de", "en"}
        ),
        "english_case_count": len(by_language.get("en", [])),
        "german_case_count": len(by_language.get("de", [])),
        "provider_calls_made": any(row["provider_calls_made"] for row in rows),
        "customer_audio_uploaded": any(row["customer_audio_uploaded"] for row in rows),
        "voice_cloning_used": any(row["voice_cloning_used"] for row in rows),
        "both_languages_have_spoken_normalization": all(
            any(row["spoken_normalization_count"] > 0 for row in by_language.get(language, []))
            for language in ("de", "en")
        ),
        "both_languages_have_prosody": all(
            any(row["prosody_cue_count"] > 0 for row in by_language.get(language, []))
            for language in ("de", "en")
        ),
        "both_languages_have_pacing": all(
            any(row["pacing_tuned_segment_count"] > 0 for row in by_language.get(language, []))
            for language in ("de", "en")
        ),
        "both_languages_have_emotion_smoothing": all(
            any(row["emotion_smoothed_transition_count"] > 0 for row in by_language.get(language, []))
            for language in ("de", "en")
        ),
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# RESP-002 Bilingual Voice Parity Report",
        "",
        "This report checks that English and German voice-delivery improvements are evaluated side by side before live TTS provider use.",
        "",
        "## Boundary",
        "",
        "- Provider calls made: `false`",
        "- Customer audio uploaded: `false`",
        "- Voice cloning used: `false`",
        "- Generated audio created: `false`",
        "",
        "## Result",
        "",
        f"- Safe cases: `{summary['safe_case_count']}/{summary['case_count']}`",
        f"- English cases: `{summary['english_case_count']}`",
        f"- German cases: `{summary['german_case_count']}`",
        f"- Matched scenario pairs: `{summary['matched_pair_count']}`",
        f"- Both languages have spoken normalization: `{summary['both_languages_have_spoken_normalization']}`",
        f"- Both languages have prosody cues: `{summary['both_languages_have_prosody']}`",
        f"- Both languages have pacing calibration: `{summary['both_languages_have_pacing']}`",
        f"- Both languages have emotion smoothing: `{summary['both_languages_have_emotion_smoothing']}`",
        "",
        "## Case Table",
        "",
        "| Case | Pair | Lang | Normalizations | Prosody | Pacing | Connected | Emotion | Provider changed | Safe |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["cases"]:
        lines.append(
            "| {case_id} | {pair_id} | {language} | {normalizations} | {prosody} | {pacing} | {connected} | {emotion} | {provider_changed} | {safe} |".format(
                case_id=row["case_id"],
                pair_id=row["pair_id"],
                language=row["language"],
                normalizations=row["spoken_normalization_count"],
                prosody=row["prosody_cue_count"],
                pacing=row["pacing_tuned_segment_count"],
                connected=row["connected_speech_flow_join_count"],
                emotion=row["emotion_smoothed_transition_count"],
                provider_changed=row["provider_rendering_changed"],
                safe=row["safe"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "English and German are both covered by the same runtime voice-delivery gate. Counts do not need to be identical because the languages have different speech mechanics, but each language must show concrete eligible freeform delivery shaping and preserve protected text boundaries.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RESP-002 English/German voice parity evaluation.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Campaign case file.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output directory.")
    parser.add_argument("--provider", default="elevenlabs", choices=["elevenlabs", "cartesia"], help="Offline provider preview.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_path(args.cases, DEFAULT_CASES)
    out_dir = resolve_path(args.out_dir, DEFAULT_OUT_DIR)
    campaigns, _cases = load_realtime_cases(cases_path)
    rows: list[dict[str, Any]] = []
    for parity_case in PARITY_CASES:
        campaign = find_campaign(campaigns, parity_case["campaign_id"])
        guarded = build_guarded_response_packet(
            campaign=campaign,
            stage=parity_case["stage"],
            input_type="speech-final",
            transcript=parity_case["transcript"],
            silence_count=0,
            candidate_response_override=parity_case["candidate_response"],
        )
        packet = attach_runtime_voice_delivery(
            guarded,
            campaign,
            provider_key=args.provider,
            seed=parity_case["case_id"],
        )
        rows.append(collect_metrics(parity_case, packet))

    payload = {
        "experiment_id": "RESP-002-bilingual-voice-parity",
        "provider_preview": args.provider,
        "provider_calls_made": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "generated_audio_created": False,
        "config": {
            "cases_path": str(cases_path.relative_to(ROOT)),
            "case_count": len(PARITY_CASES),
        },
        "summary": build_summary(rows),
        "cases": rows,
    }
    write_json(out_dir / "result.json", payload)
    write_text(out_dir / "report.md", render_report(payload))
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
