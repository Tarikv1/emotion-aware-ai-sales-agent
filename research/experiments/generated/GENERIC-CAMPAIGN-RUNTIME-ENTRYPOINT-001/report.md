# GENERIC-CAMPAIGN-RUNTIME-ENTRYPOINT-001

Status: pass
Failure count: 0

## Contract

- Helper imported: `true`
- Helper accepts in-memory campaign configs and does not require cases_path lookup.
- Live TTS/provider calls remain disabled by default.

## Synthetic Scenarios

- Insurance happy path: open, permission, premium pain, usable appointment time.
- Telecom send-info path with redacted synthetic email evidence.
- Home-services regulated caution for exact-price request.
- B2B SaaS right-person path with department and redacted synthetic email evidence.
- Invalid generic campaign does not fall back to RouteSignal.
- RouteSignal live-demo build_turn_packet preservation.

## Failures

- None
