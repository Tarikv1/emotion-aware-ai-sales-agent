#!/usr/bin/env python3
import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from generate_guarded_response import apply_guarded_response_to_decision
from generate_voice_response import build_voice_packet, resolve_project_path
from realtime_turn_cli import build_turn_case, find_campaign, run_turn_decision
from run_realtime_turn_simulation import load_realtime_cases


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "research" / "experiments" / "cases" / "prod-005-realtime-latency-call-control.json"
DEFAULT_CAMPAIGN_ID = "campaign-prod-005-b2c-telecom"
DEFAULT_STAGE = "relevance-check"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
SAMPLE_TRANSCRIPT = "Nur wenn Sie garantieren koennen, dass es stabil ist."
PRICE_SAMPLE_TRANSCRIPT = "Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt."
LOOKUP_SAMPLE_TRANSCRIPT = "Welcher genaue Tarif ist das und wie viel Datenvolumen ist enthalten?"
VOICE_MILESTONE = "VOICE-004"
PROVIDER_ID = "browser-speech-recognition-demo"


def project_relative_string(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def load_campaign(campaign_id: str, cases_path: Path) -> dict:
    campaigns, _cases = load_realtime_cases(cases_path)
    campaign = find_campaign(campaigns, campaign_id)
    campaign["_case_file"] = cases_path
    return campaign


def build_metadata(campaign_id: str, stage: str, host: str, port: int, cases_path: Path) -> dict:
    return {
        "voice_milestone": VOICE_MILESTONE,
        "provider": PROVIDER_ID,
        "description": (
            "No-key browser speech recognition demo backed by the local realtime sales-agent core "
            "and RESP-001 guarded response generation."
        ),
        "requires_api_key": False,
        "api_calls_from_python": False,
        "audio_uploaded_to_local_server": False,
        "transcript_sent_to_local_server": True,
        "consent_required": True,
        "browser_microphone_permission": "user-initiated",
        "browser_asr_disclosure": (
            "Browser speech recognition behavior depends on the user's browser. "
            "Do not use private customer audio in this prototype."
        ),
        "supported_recognition_languages": ["de-DE", "en-US", "tr-TR"],
        "default_recognition_language": "de-DE",
        "local_server": {
            "host": host,
            "port": port,
            "url": f"http://{host}:{port}/",
        },
        "local_server_endpoints": ["/", "/metadata", "/decide"],
        "default_campaign_id": campaign_id,
        "default_stage": stage,
        "sample_transcript": SAMPLE_TRANSCRIPT,
        "alternate_sample_transcripts": {
            "price_objection": PRICE_SAMPLE_TRANSCRIPT,
            "product_detail_lookup": LOOKUP_SAMPLE_TRANSCRIPT,
        },
        "case_file": project_relative_string(cases_path),
    }


def response_generation_for_voice(guarded_response: dict) -> dict:
    return {
        "response_generation_id": guarded_response["response_generation_id"],
        "provider": guarded_response["provider"],
        "generation_mode": guarded_response["generation_mode"],
        "policy_response": guarded_response["policy_response"],
        "candidate_response": guarded_response["candidate_response"],
        "final_response": guarded_response["final_response"],
        "validation": guarded_response["validation"],
        "guardrails": guarded_response["guardrails"],
        "response_constraints": guarded_response["response_constraints"],
        "latency": guarded_response["latency"],
        "llm_used": guarded_response["llm_used"],
        "requires_api_key": guarded_response["requires_api_key"],
        "api_calls_made": guarded_response["api_calls_made"],
    }


def build_browser_decision_packet(
    transcript: str,
    campaign_id: str,
    stage: str,
    input_type: str,
    silence_count: int,
    cases_path: Path,
) -> dict:
    campaign = load_campaign(campaign_id, cases_path)
    case = build_turn_case(campaign_id, stage, transcript, input_type, silence_count)
    decision = run_turn_decision(case)
    guarded_response = apply_guarded_response_to_decision(
        campaign=campaign,
        stage=stage,
        input_type=input_type,
        transcript=transcript,
        silence_count=silence_count,
        decision=decision,
    )
    decision["agent_response"] = guarded_response["final_response"]
    if decision.get("bridge_response") is not None:
        decision["bridge_response"] = guarded_response["final_response"]
    response_packet = build_voice_packet(
        campaign=campaign,
        stage=stage,
        input_type=input_type,
        transcript=transcript,
        silence_count=silence_count,
        decision=decision,
        provider="dry-run",
        voice_name=None,
        audio_output_path=None,
    )
    response_packet["response_generation"] = response_generation_for_voice(guarded_response)
    return {
        "voice_demo_run_id": f"{VOICE_MILESTONE}-browser-speech-recognition",
        "voice_milestone": VOICE_MILESTONE,
        "provider": PROVIDER_ID,
        "campaign_id": campaign_id,
        "campaign": response_packet["campaign"],
        "stage": stage,
        "input_type": input_type,
        "asr_adapter": {
            "provider": PROVIDER_ID,
            "transcript_source": "browser-final-result",
            "transcript": transcript,
            "confidence": None,
            "language": campaign.get("language"),
            "requires_api_key": False,
            "audio_uploaded_to_local_server": False,
            "transcript_sent_to_local_server": True,
            "browser_api": "SpeechRecognition or webkitSpeechRecognition",
            "consent_boundary": "user-initiated microphone permission for local prototype only",
        },
        "response_packet": response_packet,
        "trace": {
            "source": "scripts/run_browser_speech_demo.py",
            "realtime_source": "scripts/realtime_turn_cli.py",
            "response_packet_source": "scripts/generate_voice_response.py",
            "response_generation_source": "scripts/generate_guarded_response.py",
            "case_file": project_relative_string(cases_path),
        },
    }


def render_html(metadata: dict) -> str:
    metadata_json = json.dumps(metadata, ensure_ascii=False)
    sample = json.dumps(metadata["sample_transcript"], ensure_ascii=False)
    price_sample = json.dumps(metadata["alternate_sample_transcripts"]["price_objection"], ensure_ascii=False)
    lookup_sample = json.dumps(metadata["alternate_sample_transcripts"]["product_detail_lookup"], ensure_ascii=False)
    title = "VOICE-004 Browser Speech Demo"
    escaped_url = html.escape(metadata["local_server"]["url"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      --ink: #16201d;
      --muted: #53615c;
      --paper: #f5ebdc;
      --card: #fff9ee;
      --line: #d8c8b2;
      --teal: #186f67;
      --rust: #bf5b35;
      --gold: #e3b75d;
      --shadow: rgba(54, 38, 25, 0.18);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at 14% 14%, rgba(24, 111, 103, 0.20), transparent 30%),
        radial-gradient(circle at 86% 10%, rgba(191, 91, 53, 0.20), transparent 28%),
        linear-gradient(140deg, #fbf4e9 0%, #ead8c0 100%);
      font-family: "Bahnschrift", "Trebuchet MS", sans-serif;
    }}
    main {{
      width: min(1080px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 42px 0;
    }}
    .hero {{
      display: grid;
      gap: 18px;
      padding: 34px;
      border: 1px solid var(--line);
      border-radius: 34px;
      background: rgba(255, 249, 238, 0.92);
      box-shadow: 0 30px 90px var(--shadow);
    }}
    h1 {{
      margin: 0;
      max-width: 820px;
      font-family: "Palatino Linotype", "Book Antiqua", serif;
      font-size: clamp(2.4rem, 7vw, 5.8rem);
      line-height: 0.9;
      letter-spacing: -0.06em;
    }}
    p {{ color: var(--muted); line-height: 1.65; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
      margin-top: 18px;
    }}
    section {{
      padding: 22px;
      border: 1px solid var(--line);
      border-radius: 24px;
      background: rgba(255, 255, 255, 0.72);
    }}
    h2 {{
      margin: 0 0 12px;
      font-size: 0.92rem;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }}
    textarea, pre {{
      width: 100%;
      min-height: 130px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: #fffdf8;
      color: var(--ink);
      font: 0.98rem/1.55 "Cascadia Mono", Consolas, monospace;
      white-space: pre-wrap;
    }}
    button {{
      border: 0;
      border-radius: 999px;
      padding: 13px 18px;
      margin: 6px 8px 6px 0;
      background: var(--teal);
      color: white;
      font: 700 0.96rem "Bahnschrift", "Trebuchet MS", sans-serif;
      cursor: pointer;
      box-shadow: 0 12px 26px rgba(24, 111, 103, 0.22);
    }}
    button.secondary {{ background: var(--rust); box-shadow: 0 12px 26px rgba(191, 91, 53, 0.22); }}
    button.ghost {{ background: #2d352f; box-shadow: none; }}
    button:disabled {{ opacity: 0.46; cursor: not-allowed; }}
    label {{
      display: flex;
      gap: 10px;
      align-items: flex-start;
      color: var(--muted);
      line-height: 1.45;
    }}
    .status {{
      display: inline-block;
      margin-top: 12px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(227, 183, 93, 0.24);
      color: #674b13;
      font-weight: 700;
    }}
    .full {{ grid-column: 1 / -1; }}
    @media (max-width: 760px) {{
      .grid {{ grid-template-columns: 1fr; }}
      .hero {{ padding: 24px; }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="hero">
      <h1>VOICE-004 Browser Speech Demo</h1>
      <p>No API key. Browser speech recognition captures the transcript, then this local page sends text only to the local Python agent at <strong>{escaped_url}</strong>. The sales decision comes from the reusable realtime agent core, and the spoken wording passes through RESP-001 guarded response generation.</p>
      <p>Choose the recognition language before speaking. If you speak English while the recognizer is set to German, the browser may force the words into German-looking text.</p>
      <label>
        <input id="consentCheckbox" type="checkbox">
        I understand this is a local prototype. I will not use private customer audio, and I consent to starting browser microphone recognition for this demo.
      </label>
      <label>
        Recognition language
        <select id="languageSelect">
          <option value="de-DE" selected>German (de-DE)</option>
          <option value="en-US">English (en-US)</option>
          <option value="tr-TR">Turkish (tr-TR)</option>
        </select>
      </label>
      <div>
        <button id="listenButton" type="button">Start browser speech recognition</button>
        <button id="sampleButton" class="secondary" type="button">Sample: claim boundary</button>
        <button id="priceSampleButton" class="secondary" type="button">Sample: price objection</button>
        <button id="lookupSampleButton" class="secondary" type="button">Sample: product detail lookup</button>
        <button id="sendButton" class="ghost" type="button">Send transcript to local agent</button>
      </div>
      <span id="status" class="status">Ready</span>
    </div>

    <div class="grid">
      <section>
        <h2>Transcript</h2>
        <textarea id="transcriptBox" placeholder="Speak or paste a transcript here"></textarea>
      </section>
      <section>
        <h2>Agent Response</h2>
        <pre id="responseBox">Waiting for a local decision...</pre>
        <button id="speakButton" type="button">Play response</button>
      </section>
      <section>
        <h2>Last Sent Transcript</h2>
        <pre id="lastSentTranscript">Nothing sent yet.</pre>
      </section>
      <section>
        <h2>Decision Summary</h2>
        <pre id="decisionSummary">No decision yet.</pre>
      </section>
      <section class="full">
        <h2>Decision Packet</h2>
        <pre id="packetBox">No packet yet.</pre>
      </section>
    </div>
  </main>

  <script>
    const metadata = {metadata_json};
    const sampleTranscript = {sample};
    const priceSampleTranscript = {price_sample};
    const lookupSampleTranscript = {lookup_sample};
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const consentCheckbox = document.querySelector("#consentCheckbox");
    const languageSelect = document.querySelector("#languageSelect");
    const listenButton = document.querySelector("#listenButton");
    const sampleButton = document.querySelector("#sampleButton");
    const priceSampleButton = document.querySelector("#priceSampleButton");
    const lookupSampleButton = document.querySelector("#lookupSampleButton");
    const sendButton = document.querySelector("#sendButton");
    const speakButton = document.querySelector("#speakButton");
    const transcriptBox = document.querySelector("#transcriptBox");
    const responseBox = document.querySelector("#responseBox");
    const lastSentTranscript = document.querySelector("#lastSentTranscript");
    const decisionSummary = document.querySelector("#decisionSummary");
    const packetBox = document.querySelector("#packetBox");
    const status = document.querySelector("#status");
    let latestResponse = "";

    function setStatus(message) {{
      status.textContent = message;
    }}

    listenButton.addEventListener("click", () => {{
      if (!consentCheckbox.checked) {{
        setStatus("Please confirm consent before using the microphone.");
        return;
      }}
      if (!SpeechRecognition) {{
        setStatus("SpeechRecognition is not available in this browser. Try the sample transcript.");
        return;
      }}
      const recognition = new SpeechRecognition();
      recognition.lang = languageSelect.value;
      recognition.interimResults = true;
      recognition.continuous = false;
      recognition.onstart = () => setStatus(`Listening with ${{languageSelect.value}}...`);
      recognition.onerror = event => setStatus(`Recognition error: ${{event.error}}`);
      recognition.onend = () => setStatus("Recognition ended. Review transcript, then send.");
      recognition.onresult = event => {{
        let transcript = "";
        for (let index = event.resultIndex; index < event.results.length; index += 1) {{
          transcript += event.results[index][0].transcript;
        }}
        transcriptBox.value = transcript.trim();
      }};
      recognition.start();
    }});

    sampleButton.addEventListener("click", () => {{
      transcriptBox.value = sampleTranscript;
      setStatus("Claim-boundary sample loaded.");
    }});

    priceSampleButton.addEventListener("click", () => {{
      transcriptBox.value = priceSampleTranscript;
      setStatus("Price-objection sample loaded.");
    }});

    lookupSampleButton.addEventListener("click", () => {{
      transcriptBox.value = lookupSampleTranscript;
      setStatus("Product-detail lookup sample loaded.");
    }});

    sendButton.addEventListener("click", async () => {{
      const transcript = transcriptBox.value.trim();
      if (!transcript) {{
        setStatus("Add a transcript before sending.");
        return;
      }}
      lastSentTranscript.textContent = transcript;
      setStatus("Sending transcript to local agent core...");
      const response = await fetch("/decide", {{
        method: "POST",
        headers: {{ "Content-Type": "application/json" }},
        body: JSON.stringify({{
          transcript,
          campaign_id: metadata.default_campaign_id,
          stage: metadata.default_stage,
          input_type: "speech-final"
        }})
      }});
      if (!response.ok) {{
        setStatus(`Local decision failed: ${{response.status}}`);
        return;
      }}
      const packet = await response.json();
      latestResponse = packet.response_packet.tts_text;
      const decision = packet.response_packet.decision;
      responseBox.textContent = latestResponse;
      decisionSummary.textContent = JSON.stringify({{
        detected_emotion: decision.detected_emotion,
        sales_difficulty: decision.sales_difficulty,
        interest_state: decision.interest_state,
        selected_strategy: decision.selected_strategy,
        next_action: decision.next_action,
        call_control: decision.call_control
      }}, null, 2);
      packetBox.textContent = JSON.stringify(packet, null, 2);
      setStatus(`Decision: ${{decision.call_control}}. Response may stay the same when transcripts map to the same sales difficulty.`);
    }});

    speakButton.addEventListener("click", () => {{
      if (!latestResponse) {{
        latestResponse = responseBox.textContent.trim();
      }}
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(latestResponse);
      utterance.lang = "en-US";
      utterance.rate = 0.95;
      window.speechSynthesis.speak(utterance);
    }});
  </script>
</body>
</html>
"""


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_handler(metadata: dict, cases_path: Path):
    class BrowserSpeechDemoHandler(BaseHTTPRequestHandler):
        def _send_json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, body_text: str) -> None:
            body = body_text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:
            return

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                self._send_html(render_html(metadata))
                return
            if path == "/metadata":
                self._send_json(metadata)
                return
            self._send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path != "/decide":
                self._send_json({"error": "not found"}, status=404)
                return

            length = int(self.headers.get("Content-Length", "0"))
            try:
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body or "{}")
                transcript = str(payload.get("transcript", "")).strip()
                if not transcript:
                    self._send_json({"error": "transcript is required"}, status=400)
                    return
                packet = build_browser_decision_packet(
                    transcript=transcript,
                    campaign_id=payload.get("campaign_id") or metadata["default_campaign_id"],
                    stage=payload.get("stage") or metadata["default_stage"],
                    input_type=payload.get("input_type") or "speech-final",
                    silence_count=int(payload.get("silence_count") or 0),
                    cases_path=cases_path,
                )
                self._send_json(packet)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)

    return BrowserSpeechDemoHandler


def serve(metadata: dict, cases_path: Path) -> None:
    server = ThreadingHTTPServer(
        (metadata["local_server"]["host"], metadata["local_server"]["port"]),
        make_handler(metadata, cases_path),
    )
    print(metadata["local_server"]["url"])
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or export the VOICE-004 browser speech recognition demo.")
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN_ID, help="Default campaign ID for the demo.")
    parser.add_argument("--stage", default=DEFAULT_STAGE, help="Default call stage for the demo.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Local server host.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Local server port.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES_PATH), help="Campaign wrapper case file to load.")
    parser.add_argument("--export-html", help="Write the browser demo HTML and exit.")
    parser.add_argument("--export-metadata", help="Write demo metadata JSON and exit.")
    parser.add_argument("--decision-transcript", help="Run one local decision for this transcript and exit.")
    parser.add_argument("--decision-out", help="Optional path to write the decision JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = resolve_project_path(args.cases)
    if cases_path is None:
        raise SystemExit("--cases is required.")

    metadata = build_metadata(args.campaign, args.stage, args.host, args.port, cases_path)

    if args.decision_transcript:
        packet = build_browser_decision_packet(
            transcript=args.decision_transcript,
            campaign_id=args.campaign,
            stage=args.stage,
            input_type="speech-final",
            silence_count=0,
            cases_path=cases_path,
        )
        decision_out = resolve_project_path(args.decision_out)
        if decision_out is not None:
            write_json(decision_out, packet)
        print(json.dumps(packet, indent=2, ensure_ascii=False))
        return

    exported = False
    export_html = resolve_project_path(args.export_html)
    if export_html is not None:
        write_text(export_html, render_html(metadata))
        exported = True

    export_metadata = resolve_project_path(args.export_metadata)
    if export_metadata is not None:
        write_json(export_metadata, metadata)
        exported = True

    if exported:
        print(json.dumps(metadata, indent=2, ensure_ascii=False))
        return

    serve(metadata, cases_path)


if __name__ == "__main__":
    main()
