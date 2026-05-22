# CAMPAIGN-REGISTRY-001

Status: pass
Failure count: 0

## Contract

- File-backed synthetic campaign configs load through `runtime.core.campaign_registry`.
- Invalid generic campaign configs fail locally and do not fall back to RouteSignal.
- Generic config-path runtime helper preserves in-memory campaign behavior and keeps live TTS/provider side effects off.
- RouteSignal live-demo path remains unchanged.

## Files

- Schema: `runtime\campaigns\schema\campaign_config.schema.json`
- Examples: `runtime\campaigns\examples`

## Failures

- None
