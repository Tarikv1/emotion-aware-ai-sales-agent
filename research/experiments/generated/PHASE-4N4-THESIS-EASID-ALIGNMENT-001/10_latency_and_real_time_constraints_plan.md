# Latency And Real-Time Constraints Plan

## Measurement Target

Latency matters because a voice sales agent must respond fast enough for natural turn-taking. This package defines the field and future table only; it does not measure latency.

## Field

`latency_ms` records measured agent response latency for a turn. It remains null when no runtime measurement exists.

## Constraints To Track Later

- median latency_ms
- p95 latency_ms
- timeout or retry count
- buyer interruption count
- evaluator notes about awkward silence or overtalking

## Current Boundary

No provider/model/TTS calls are made in this checkpoint, so there is no latency result. Any future latency claim must identify the runtime path, model/provider shell, measurement method, and test conditions.
