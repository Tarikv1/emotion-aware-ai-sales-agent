#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VOICE_MILESTONE = "VOICE-014"
DEFAULT_CASES = ROOT / "research" / "experiments" / "cases" / "voice-014-provider-listening-comparison.json"
DEFAULT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-014-provider-listening-comparison.json"
DEFAULT_REPORT_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-014-provider-listening-comparison-report.md"
DEFAULT_HTML_OUT = ROOT / "research" / "experiments" / "generated" / "VOICE-014-provider-listening-comparison.html"


def resolve_project_path(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def project_relative_string(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def index_cases(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["case_id"]: case for case in payload.get("cases", [])}


def audio_path_info(path_text: str | None) -> dict[str, Any]:
    if not path_text:
        return {
            "audio_path": None,
            "audio_exists": False,
            "audio_byte_size_on_disk": 0,
            "html_audio_src": None,
        }
    path = resolve_project_path(path_text)
    if path is None:
        return {
            "audio_path": path_text,
            "audio_exists": False,
            "audio_byte_size_on_disk": 0,
            "html_audio_src": path_text,
        }
    exists = path.is_file()
    return {
        "audio_path": project_relative_string(path),
        "audio_exists": exists,
        "audio_byte_size_on_disk": path.stat().st_size if exists else 0,
        "html_audio_src": path.name,
    }


def provider_entry(provider_name: str, case: dict[str, Any]) -> dict[str, Any]:
    if provider_name == "cartesia":
        tts = case["cartesia_websocket"]
        audio = audio_path_info(tts.get("audio_output_path"))
        return {
            "provider_key": "cartesia",
            "provider_name": "Cartesia Sonic 3 WebSocket",
            "case_id": case["case_id"],
            "audio_format": "wav",
            "audio_file_created": tts["audio_file_created"],
            "recorded_audio_byte_size": tts["audio_byte_size"],
            "first_audio_ms": tts["time_to_first_audio_chunk_ms"],
            "total_latency_ms": tts["total_stream_latency_ms"],
            "fallback_used": tts["fallback_used"],
            "fallback_reason": tts["fallback_reason"],
            **audio,
        }
    if provider_name == "elevenlabs":
        tts = case["elevenlabs_tts"]
        audio = audio_path_info(tts.get("audio_output_path"))
        return {
            "provider_key": "elevenlabs",
            "provider_name": "ElevenLabs HTTP Stream",
            "case_id": case["case_id"],
            "audio_format": "mp3",
            "audio_file_created": tts["audio_file_created"],
            "recorded_audio_byte_size": tts["audio_byte_size"],
            "first_audio_ms": tts["time_to_first_audio_byte_ms"],
            "total_latency_ms": tts["total_provider_latency_ms"],
            "fallback_used": tts["fallback_used"],
            "fallback_reason": tts["fallback_reason"],
            **audio,
        }
    raise ValueError(f"Unknown provider: {provider_name}")


def empty_rating_template(criteria: list[str]) -> dict[str, Any]:
    return {criterion: None for criterion in criteria}


def build_comparison_pair(
    pair_config: dict[str, Any],
    cartesia_cases: dict[str, dict[str, Any]],
    elevenlabs_cases: dict[str, dict[str, Any]],
    criteria: list[str],
) -> dict[str, Any]:
    cartesia_case = cartesia_cases[pair_config["cartesia_case_id"]]
    elevenlabs_case = elevenlabs_cases[pair_config["elevenlabs_case_id"]]
    cartesia = provider_entry("cartesia", cartesia_case)
    elevenlabs = provider_entry("elevenlabs", elevenlabs_case)
    first_audio_delta = None
    if cartesia["first_audio_ms"] is not None and elevenlabs["first_audio_ms"] is not None:
        first_audio_delta = round(elevenlabs["first_audio_ms"] - cartesia["first_audio_ms"], 3)
    total_latency_delta = None
    if cartesia["total_latency_ms"] is not None and elevenlabs["total_latency_ms"] is not None:
        total_latency_delta = round(elevenlabs["total_latency_ms"] - cartesia["total_latency_ms"], 3)

    return {
        "comparison_id": pair_config["comparison_id"],
        "language": pair_config["language"],
        "scenario": pair_config["scenario"],
        "campaign_id": cartesia_case["campaign_id"],
        "tts_quality_script": elevenlabs_case.get("tts_quality_script") or cartesia_case.get("tts_quality_script"),
        "providers": [cartesia, elevenlabs],
        "timing_comparison": {
            "first_audio_delta_ms_elevenlabs_minus_cartesia": first_audio_delta,
            "total_latency_delta_ms_elevenlabs_minus_cartesia": total_latency_delta,
            "lower_first_audio_provider": lower_latency_provider(cartesia, elevenlabs, "first_audio_ms"),
            "lower_total_latency_provider": lower_latency_provider(cartesia, elevenlabs, "total_latency_ms"),
        },
        "human_rating_template": {
            "cartesia": empty_rating_template(criteria),
            "elevenlabs": empty_rating_template(criteria),
            "preferred_provider": None,
            "notes": None,
        },
    }


def lower_latency_provider(first: dict[str, Any], second: dict[str, Any], key: str) -> str | None:
    first_value = first.get(key)
    second_value = second.get(key)
    if first_value is None or second_value is None:
        return None
    if first_value < second_value:
        return first["provider_key"]
    if second_value < first_value:
        return second["provider_key"]
    return "tie"


def aggregate(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    pair_count = len(comparisons)
    complete_audio_pairs = 0
    provider_audio_counts = {"cartesia": 0, "elevenlabs": 0}
    language_counts: dict[str, int] = {}
    for comparison in comparisons:
        language_counts[comparison["language"]] = language_counts.get(comparison["language"], 0) + 1
        if all(provider["audio_exists"] for provider in comparison["providers"]):
            complete_audio_pairs += 1
        for provider in comparison["providers"]:
            if provider["audio_exists"]:
                provider_audio_counts[provider["provider_key"]] += 1

    return {
        "comparison_count": pair_count,
        "languages": language_counts,
        "providers": ["cartesia", "elevenlabs"],
        "complete_audio_pairs": complete_audio_pairs,
        "provider_audio_counts": provider_audio_counts,
        "provider_calls_made": False,
        "requires_api_key": False,
        "customer_audio_uploaded": False,
        "voice_cloning_used": False,
        "human_ratings_recorded": False,
        "quality_claim_allowed": False,
    }


def build_payload(cases_path: Path) -> dict[str, Any]:
    config = load_json(cases_path)
    cartesia_path = resolve_project_path(config["source_artifacts"]["cartesia"])
    elevenlabs_path = resolve_project_path(config["source_artifacts"]["elevenlabs"])
    if cartesia_path is None or elevenlabs_path is None:
        raise SystemExit("Source artifact paths could not be resolved.")
    cartesia_payload = load_json(cartesia_path)
    elevenlabs_payload = load_json(elevenlabs_path)
    criteria = config["rating_rubric"]["criteria"]
    comparisons = [
        build_comparison_pair(pair, index_cases(cartesia_payload), index_cases(elevenlabs_payload), criteria)
        for pair in config["pairs"]
    ]
    return {
        "voice_milestone": VOICE_MILESTONE,
        "experiment_scope": config["experiment_scope"],
        "case_file": project_relative_string(cases_path),
        "source_artifacts": {
            "cartesia": project_relative_string(cartesia_path),
            "elevenlabs": project_relative_string(elevenlabs_path),
        },
        "safety_gate": config["safety_gate"],
        "rating_rubric": config["rating_rubric"],
        "summary": aggregate(comparisons),
        "comparisons": comparisons,
    }


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# VOICE-014 Provider Listening Comparison",
        "",
        "This report was generated by `scripts/run_voice_014_provider_listening_comparison.py`.",
        "",
        "No provider calls were made. This comparison uses local generated audio artifacts from VOICE-011 and VOICE-013.",
        "",
        "## Summary",
        "",
        f"- Comparison pairs: `{summary['comparison_count']}`",
        f"- German pairs: `{summary['languages'].get('de', 0)}`",
        f"- English pairs: `{summary['languages'].get('en', 0)}`",
        f"- Complete audio pairs: `{summary['complete_audio_pairs']} / {summary['comparison_count']}`",
        f"- Cartesia audio files available: `{summary['provider_audio_counts']['cartesia']}`",
        f"- ElevenLabs audio files available: `{summary['provider_audio_counts']['elevenlabs']}`",
        f"- Provider calls made: `{summary['provider_calls_made']}`",
        f"- Customer audio uploaded: `{summary['customer_audio_uploaded']}`",
        f"- Human ratings recorded: `{summary['human_ratings_recorded']}`",
        f"- Quality claim allowed: `{summary['quality_claim_allowed']}`",
        "",
        "## Rating Rubric",
        "",
    ]
    for criterion in payload["rating_rubric"]["criteria"]:
        lines.append(f"- `{criterion}`")
    lines.extend(["", "## Comparison Pairs", ""])
    for comparison in payload["comparisons"]:
        timing = comparison["timing_comparison"]
        lines.extend(
            [
                f"### {comparison['comparison_id']}: {comparison['scenario']}",
                "",
                f"- Language: `{comparison['language']}`",
                f"- Campaign: `{comparison['campaign_id']}`",
                f"- First-audio delta, ElevenLabs minus Cartesia: `{timing['first_audio_delta_ms_elevenlabs_minus_cartesia']} ms`",
                f"- Total-latency delta, ElevenLabs minus Cartesia: `{timing['total_latency_delta_ms_elevenlabs_minus_cartesia']} ms`",
                f"- Lower first-audio provider: `{timing['lower_first_audio_provider']}`",
                f"- Lower total-latency provider: `{timing['lower_total_latency_provider']}`",
                "",
            ]
        )
        for provider in comparison["providers"]:
            lines.extend(
                [
                    f"- {provider['provider_name']}:",
                    f"  audio: `{provider['audio_path']}`",
                    f"  exists: `{provider['audio_exists']}`",
                    f"  first audio: `{provider['first_audio_ms']} ms`",
                    f"  total latency: `{provider['total_latency_ms']} ms`",
                    f"  bytes: `{provider['audio_byte_size_on_disk']}`",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def render_html(payload: dict[str, Any]) -> str:
    cards = []
    for comparison in payload["comparisons"]:
        provider_blocks = []
        for provider in comparison["providers"]:
            audio_src = html.escape(provider["html_audio_src"] or "")
            audio_control = (
                f'<audio controls preload="metadata" src="{audio_src}"></audio>'
                if provider["audio_exists"] and audio_src
                else "<p class=\"missing\">Audio file missing.</p>"
            )
            provider_blocks.append(
                f"""
                <section class="provider-card">
                  <h3>{html.escape(provider["provider_name"])}</h3>
                  {audio_control}
                  <dl>
                    <div><dt>First audio</dt><dd>{provider["first_audio_ms"]} ms</dd></div>
                    <div><dt>Total latency</dt><dd>{provider["total_latency_ms"]} ms</dd></div>
                    <div><dt>Format</dt><dd>{html.escape(provider["audio_format"])}</dd></div>
                  </dl>
                </section>
                """
            )
        criteria_rows = "\n".join(
            f"<tr><td>{html.escape(criterion)}</td><td></td><td></td><td></td></tr>"
            for criterion in payload["rating_rubric"]["criteria"]
        )
        cards.append(
            f"""
            <article class="comparison">
              <div class="comparison-head">
                <p class="eyebrow">{html.escape(comparison["comparison_id"])} · {html.escape(comparison["language"].upper())}</p>
                <h2>{html.escape(comparison["scenario"])}</h2>
              </div>
              <p class="script">{html.escape(comparison["tts_quality_script"])}</p>
              <div class="providers">
                {''.join(provider_blocks)}
              </div>
              <table>
                <thead>
                  <tr><th>Criterion</th><th>Cartesia 1-5</th><th>ElevenLabs 1-5</th><th>Notes</th></tr>
                </thead>
                <tbody>{criteria_rows}</tbody>
              </table>
            </article>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>VOICE-014 Provider Listening Comparison</title>
  <style>
    :root {{
      --ink: #1e2621;
      --muted: #617066;
      --paper: #f7f0e5;
      --card: #fffaf2;
      --accent: #0f6b5f;
      --line: #dccfbb;
      --shadow: rgba(47, 37, 24, 0.14);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at 8% 6%, rgba(15, 107, 95, 0.18), transparent 28%),
        radial-gradient(circle at 92% 16%, rgba(177, 103, 46, 0.14), transparent 28%),
        linear-gradient(135deg, #f9f2e7 0%, #eadfce 100%);
      color: var(--ink);
      font-family: Georgia, "Times New Roman", serif;
    }}
    main {{
      width: min(1180px, calc(100vw - 28px));
      margin: 0 auto;
      padding: 44px 0 64px;
    }}
    header {{
      padding: 34px;
      border: 1px solid var(--line);
      border-radius: 30px;
      background: rgba(255, 250, 242, 0.84);
      box-shadow: 0 22px 70px var(--shadow);
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: clamp(2.4rem, 7vw, 5.8rem);
      line-height: 0.9;
      letter-spacing: -0.06em;
    }}
    p {{
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.6;
    }}
    .comparison {{
      margin-top: 26px;
      padding: 28px;
      border: 1px solid var(--line);
      border-radius: 26px;
      background: rgba(255, 250, 242, 0.92);
      box-shadow: 0 18px 50px var(--shadow);
    }}
    .eyebrow {{
      margin: 0 0 8px;
      color: var(--accent);
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-size: 0.8rem;
    }}
    h2 {{
      margin: 0;
      font-size: clamp(1.5rem, 3vw, 2.4rem);
    }}
    .script {{
      margin: 18px 0;
      padding: 18px;
      border-left: 5px solid var(--accent);
      border-radius: 18px;
      background: #fff;
      color: var(--ink);
    }}
    .providers {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .provider-card {{
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: #fff;
    }}
    audio {{ width: 100%; margin: 10px 0; }}
    dl {{ margin: 12px 0 0; display: grid; gap: 8px; }}
    dl div {{ display: flex; justify-content: space-between; gap: 16px; color: var(--muted); }}
    dt {{ font-weight: 700; color: var(--ink); }}
    table {{
      width: 100%;
      margin-top: 20px;
      border-collapse: collapse;
      background: #fff;
      border-radius: 18px;
      overflow: hidden;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 11px;
      text-align: left;
      height: 42px;
    }}
    th {{ background: #f1e5d2; }}
    .missing {{ color: #9b3d2e; }}
    @media (max-width: 760px) {{
      .providers {{ grid-template-columns: 1fr; }}
      header, .comparison {{ padding: 20px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <p class="eyebrow">VOICE-014</p>
      <h1>Provider Listening Comparison</h1>
      <p>Listen pair-by-pair. Score each provider from 1 to 5, then add notes. This page makes no provider calls and uses only local generated audio files.</p>
    </header>
    {''.join(cards)}
  </main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build VOICE-014 Cartesia vs ElevenLabs listening comparison artifacts.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="VOICE-014 comparison case file.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="JSON output path.")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_OUT), help="Markdown report output path.")
    parser.add_argument("--html-out", default=str(DEFAULT_HTML_OUT), help="HTML listening page output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    out_path = resolve_project_path(args.out)
    report_path = resolve_project_path(args.report_out)
    html_path = resolve_project_path(args.html_out)
    if cases_path is None or out_path is None or report_path is None or html_path is None:
        raise SystemExit("VOICE-014 paths could not be resolved.")
    payload = build_payload(cases_path)
    write_json(out_path, payload)
    write_text(report_path, render_report(payload))
    write_text(html_path, render_html(payload))
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
