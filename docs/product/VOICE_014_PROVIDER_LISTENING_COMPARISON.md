# VOICE-014 Provider Listening Comparison

## Purpose

VOICE-014 creates a structured local comparison between Cartesia VOICE-011 and ElevenLabs VOICE-013.

It does not call any provider and does not require an API key. It only reads the existing generated provider artifacts and local audio files.

## Comparison Scope

Providers:

- Cartesia Sonic 3 WebSocket from `VOICE-011`
- ElevenLabs HTTP streaming from `VOICE-013`

Cases:

- German objection handling
- German bridge and handoff
- English B2B objection handling
- English scheduling and close

The comparison uses the same longer synthetic scripts for both providers.

## Generated Artifacts

```text
research/experiments/generated/VOICE-014-provider-listening-comparison.json
research/experiments/generated/VOICE-014-provider-listening-comparison-report.md
research/experiments/generated/VOICE-014-provider-listening-comparison.html
```

The HTML page provides local audio controls and a manual scoring table for each pair.

## Rating Rubric

Score each provider from `1` to `5` for:

- naturalness
- clarity
- language pronunciation
- sales-call pacing
- low muffling or artifacts
- emotional appropriateness
- trustworthiness
- overall preference

Do not declare a final provider winner until these ratings are recorded.

## Current Timing Summary

All four comparison pairs have both provider audio files available.

ElevenLabs has lower total provider latency in all four pairs.

First-audio timing:

- Cartesia starts faster in `VOICE-014-C01` by `106.921 ms`
- ElevenLabs starts faster in `VOICE-014-C02` by `71.719 ms`
- ElevenLabs starts faster in `VOICE-014-C03` by `108.763 ms`
- ElevenLabs starts faster in `VOICE-014-C04` by `46.416 ms`

This means timing alone does not fully decide the provider. Listening quality and trustworthiness remain important.

## Validation

Run:

```powershell
python scripts\validate_voice_014_provider_listening_comparison.py
```

The validator checks:

- four comparison pairs exist
- German and English pairs are covered
- Cartesia and ElevenLabs audio exists for every pair
- no provider calls are made
- no API keys are required
- no customer audio is uploaded
- no quality claim is allowed before human ratings are recorded

## Product Meaning

VOICE-014 keeps the voice provider decision evidence-based.

The product should not pick a provider only because it sounds better once, or only because it has lower latency once. The provider decision should combine:

- first-audio timing
- total latency
- German and English quality
- trustworthiness
- fit with VOICE-012 naturalized speech
- privacy and account constraints
