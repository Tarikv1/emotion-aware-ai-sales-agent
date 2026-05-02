# Product Command Map

Run commands from the repo root:

```powershell
cd D:\Codex\active\emotion-aware-ai-sales-agent
```

Default commands should stay local and offline. Commands that can call external providers are listed separately under "Explicit opt-in provider commands".

## Setup

Check the local product workspace without installing dependencies, calling providers, or printing secret values:

```powershell
python scripts\check_setup.py
```

Machine-readable setup check:

```powershell
python scripts\check_setup.py --json
```

Validate the setup checker itself:

```powershell
python scripts\validate_check_setup.py
```

## Relevant File Reading

Use this when a file is large and you only need the useful part. It reads local repo files only, blocks secret/private paths, makes no network calls, and returns small slices.

Show headings and lightweight symbols:

```powershell
python scripts\read_relevant.py outline --path docs\product\COMMANDS.md
```

Read a bounded line range:

```powershell
python scripts\read_relevant.py slice --path docs\product\COMMANDS.md --start 11 --end 30
```

Find matching lines with nearby context:

```powershell
python scripts\read_relevant.py find --path docs\product\COMMANDS.md --query "Cartesia" --context 1
```

Read a Markdown section by heading:

```powershell
python scripts\read_relevant.py section --path docs\product\COMMANDS.md --heading "Setup"
```

Validate the reader:

```powershell
python scripts\validate_read_relevant.py
```

## Core Product Contract

Validate the runtime output contract used before speaking or logging agent decisions:

```powershell
python scripts\validate_product_agent_output_contract.py
```

Run a single realtime turn:

```powershell
python scripts\realtime_turn_cli.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage relevance-check `
  --transcript "Nur wenn Sie garantieren koennen, dass es stabil ist."
```

Validate the realtime turn CLI:

```powershell
python scripts\validate_realtime_turn_cli.py
```

## Product Simulations

Render a product simulation packet:

```powershell
python scripts\run_product_simulation.py `
  --cases research\experiments\cases\prod-001-qualification-simulation.json `
  --out research\experiments\generated\PROD-001-evaluation-packet.md `
  --export-records research\experiments\generated\PROD-001-db-records.json
```

Run the deterministic rule baseline:

```powershell
python scripts\run_rule_baseline.py `
  --cases research\experiments\cases\prod-004-sales-difficulty-gauntlet.json `
  --out research\experiments\generated\PROD-004-rule-baseline-results.json `
  --report-out research\experiments\generated\PROD-004-rule-baseline-report.md
```

Run the realtime latency and call-control simulation:

```powershell
python scripts\run_realtime_turn_simulation.py `
  --cases research\experiments\cases\prod-005-realtime-latency-call-control.json `
  --out research\experiments\generated\PROD-005-realtime-results.json `
  --report-out research\experiments\generated\PROD-005-realtime-report.md
```

## Guarded Response And Voice Safety

Generate a guarded response packet from the realtime decision path:

```powershell
python scripts\generate_guarded_response.py `
  --campaign campaign-prod-005-b2c-telecom `
  --stage product-detail-check `
  --transcript "Welcher genaue Tarif ist das und wie viel Datenvolumen ist enthalten?" `
  --out research\experiments\generated\RESP-001-guarded-response-result.json `
  --report-out research\experiments\generated\RESP-001-guarded-response-report.md
```

Evaluate provider readiness without API calls or audio upload:

```powershell
python scripts\evaluate_voice_provider_readiness.py `
  --candidates research\experiments\cases\voice-007-provider-readiness-candidates.json `
  --out research\experiments\generated\VOICE-007-provider-readiness.json `
  --report-out research\experiments\generated\VOICE-007-provider-readiness-report.md
```

Validate the provider readiness gate:

```powershell
python scripts\validate_voice_007_provider_readiness.py
```

Run the local TTS smoke test in forced fallback mode:

```powershell
python scripts\run_voice_008_local_tts_smoke.py --force-fallback
```

Validate local TTS smoke behavior:

```powershell
python scripts\validate_voice_008_local_tts_smoke.py
```

Run the Cartesia TTS smoke test in no-key fallback mode:

```powershell
python scripts\run_voice_010_cartesia_tts_smoke.py --force-key-missing
```

Validate Cartesia smoke behavior without live provider calls:

```powershell
python scripts\validate_voice_010_cartesia_tts_smoke.py
```

## Guarded Local Demo Server

Use the guarded launcher for browser demos so long-lived servers do not hang the terminal:

```powershell
python scripts\start_guarded_local_server.py `
  --name VOICE-004 `
  --host 127.0.0.1 `
  --port 8765 `
  --startup-timeout 8 `
  --pid-out research\experiments\generated\VOICE-004-server.pid `
  --stdout-log research\experiments\generated\VOICE-004-server.stdout.log `
  --stderr-log research\experiments\generated\VOICE-004-server.stderr.log `
  -- python scripts\run_browser_speech_demo.py
```

## Explicit Opt-In Provider Commands

These commands can contact external providers. Do not run them as default setup checks.

Live LLM product-agent evaluation requires an environment-only API key:

```powershell
python scripts\run_llm_product_agent.py `
  --cases research\experiments\cases\prod-004-sales-difficulty-gauntlet.json `
  --out research\experiments\generated\PROD-004-llm-agent-results.json `
  --report-out research\experiments\generated\PROD-004-llm-agent-report.md `
  --limit 1
```

Live Cartesia TTS smoke testing requires `CARTESIA_API_KEY`, `CARTESIA_VOICE_ID`, and an explicit `--live` flag:

```powershell
python scripts\run_voice_010_cartesia_tts_smoke.py --live
```

## Safety Rules

- Do not commit API keys, private transcripts, raw private audio, customer exports, or client-specific sensitive details.
- Default validation should not require `OPENAI_API_KEY`, `CARTESIA_API_KEY`, or `CARTESIA_VOICE_ID`.
- Use `--live` only when provider, consent, retention, and logging assumptions have been reviewed.
- Keep generated artifacts under `research\experiments\generated` unless a script documents another output path.
