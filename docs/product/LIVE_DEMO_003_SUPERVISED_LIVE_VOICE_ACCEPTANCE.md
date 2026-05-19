# LIVE-DEMO-003 Supervised Live Voice Acceptance

`LIVE-DEMO-003-supervised-live-voice-acceptance` is a narrow checkpoint after the passing `LIVE-DEMO-002` text/runtime validation. It does not open `PROD-102`, claim production readiness, enable payment collection, create a provider-hosted durable agent, use voice cloning, make LLM calls required for live response, or let an LLM write final spoken responses.

## Goal

Create a supervised live voice acceptance workflow so Tarik can run the local demo, review what he heard, and decide whether the agent is acceptable for the next iteration.

This checkpoint separates automated text/runtime success from live voice quality. It checks the human-heard path: browser ASR, turn-taking, TTS playback, voice consistency, interruption/talk-over behavior, perceived latency, callback handling, buyer agency, naturalness, and sales steering.

Passing this checkpoint means only that the supervised demo is acceptable for the next iteration. It is not production readiness. Failing this checkpoint should create narrow follow-up tickets, not a broad runtime rewrite.

## Tooling

Generate a synthetic provider-off acceptance packet:

```powershell
python scripts\generate_live_demo_003_acceptance_packet.py
```

This writes the machine packet, report, human-readable review form, and fillable CSV:

- `research\experiments\generated\LIVE-DEMO-003-supervised-live-voice-acceptance\acceptance_packet.json`
- `research\experiments\generated\LIVE-DEMO-003-supervised-live-voice-acceptance\acceptance_report.md`
- `research\experiments\generated\LIVE-DEMO-003-supervised-live-voice-acceptance\manual_review_form.md`
- `research\experiments\generated\LIVE-DEMO-003-supervised-live-voice-acceptance\manual_review.csv`

Validate the tooling without live voice or provider calls:

```powershell
python scripts\validate_live_demo_003_supervised_live_voice_acceptance.py
```

For live ElevenLabs playback, keep the API key in ignored `runtime\config\local\elevenlabs.env`:

```powershell
Copy-Item runtime\config\local\elevenlabs.env.example runtime\config\local\elevenlabs.env
```

Then fill `ELEVENLABS_API_KEY` in that ignored file. Voice IDs can remain in ignored `config\local\voice_ids.json`; `--live-tts` now fails before the browser starts if the key or voice ID cannot be resolved.

After a real supervised local run, build a private review packet from ignored turn JSON files:

```powershell
python scripts\generate_live_demo_003_acceptance_packet.py --from-private-turns data\private\live-demo-003\raw-turns --out data\private\live-demo-003\acceptance_packet.json --report-out data\private\live-demo-003\acceptance_report.md --review-form-out data\private\live-demo-003\manual_review_form.md --review-csv-out data\private\live-demo-003\manual_review.csv
```

Use `manual_review_form.md` as the plain-language guide. Fill `manual_review.csv`; do not edit raw JSON unless you need the machine artifact directly. Then evaluate it:

```powershell
python scripts\generate_live_demo_003_acceptance_packet.py --input data\private\live-demo-003\acceptance_packet.json --manual-review-csv data\private\live-demo-003\manual_review.csv --out data\private\live-demo-003\acceptance_packet.reviewed.json --report-out data\private\live-demo-003\acceptance_report.reviewed.md --review-form-out data\private\live-demo-003\manual_review_form.reviewed.md --review-csv-out data\private\live-demo-003\manual_review.reviewed.csv
```

## Recommended Spoken Path

These turns are sample scenarios only, not runtime caps:

1. Start Conversation
2. `hmm okay`
3. `I didn't understand what you asked`
4. `callbacks are probably the problem`
5. `what do you mean by callbacks?`
6. `tell me more`
7. `why does that matter?`
8. `what does it cost?`
9. `I am not sure it fits our workflow`
10. `no`
11. `what next?`
12. `call me back later`
13. `tomorrow at 3 works`

Optional stress turns:

- `you called me`
- `I don't have a question`
- `I don't know what you're talking about`
- `does it replace my CRM?`
- `does it have SOC 2?`
- `send me a short summary`
- `tomorrow at 3 works`

## Acceptance Criteria

Hard gates:

- no provider-hosted durable agent
- no voice cloning
- no customer audio upload to the Python server
- no LLM blocking the live spoken response
- no LLM mutation of final response
- no payment collection
- no bare workflow `callback` treated as scheduling
- explicit `call me back later` still treated as scheduling
- terminal call-control stops listening restart
- no exact repeated final response
- no obvious customer-sentence echoing
- no internal wording leaked, including `runtime`, `guardrail`, `anti-loop`, or `decision log`

Human quality gates:

- turn-taking average at least `4/5`
- latency acceptability average at least `4/5`
- voice consistency average at least `4/5`
- response naturalness average at least `3/5`
- sales steering average at least `4/5`
- buyer agency preserved
- accepted for next iteration

## Evidence

Generated evidence:

- `research/experiments/generated/LIVE-DEMO-003-supervised-live-voice-acceptance/result.json`
- `research/experiments/generated/LIVE-DEMO-003-supervised-live-voice-acceptance/report.md`
- `research/experiments/generated/LIVE-DEMO-003-supervised-live-voice-acceptance/acceptance_packet.json`
- `research/experiments/generated/LIVE-DEMO-003-supervised-live-voice-acceptance/acceptance_report.md`
- `research/experiments/generated/LIVE-DEMO-003-supervised-live-voice-acceptance/manual_review_form.md`
- `research/experiments/generated/LIVE-DEMO-003-supervised-live-voice-acceptance/manual_review.csv`

The validator does not run live voice, browser ASR, or provider TTS. Tarik's manual supervised review is required before this checkpoint can be accepted for the next iteration.
