# PUBLIC-OPENAI-LIVE-REHEARSAL-001

- Status: `fail`
- Total private records scanned: `537`
- Current OpenAI live records found: `9`
- Records after `729d06e` or latest marker: `9`
- Stale/historical OpenAI records ignored: `12`
- Live TTS used count: `9`
- Dry-run count: `0`
- ElevenLabs call made count: `9`
- TTS provider calls made count: `9`
- Audio file created count: `9`
- Raw voice ID logged count: `0`
- Runtime defect count: `2`
- ASR issue count: `0`
- TTS/audio issue count: `0`
- Latency/turn-taking issue count: `0`

## Voice Source Summary

```json
{
  "voice_id_hash_values": [
    "433413ba"
  ],
  "voice_id_source_values": [
    "local_voice_ids:elevenlabs.en"
  ]
}
```

## Classification Counts

```json
{
  "current_live_openai_human_followup_owner_leakage": 1,
  "current_live_openai_legacy_compatibility_leakage": 2,
  "current_live_openai_runtime_defect": 2,
  "current_openai_live_success": 7,
  "expected_dry_run_historical_record": 11,
  "needs_human_review": 2,
  "stale_or_unknown_version_artifact": 1
}
```

## Human Review Examples

```json
[
  {
    "classifications": [
      "current_live_openai_legacy_compatibility_leakage"
    ],
    "final_response": "Quick check for a short legacy compatibility field only; primary close is official self-serve plan page or Enterprise contact-sales route: Are you mainly comparing plans for yourself, a small team, or a larger organization?",
    "generated_at": "2026-05-25T01:00:42.550436+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-030042.json",
    "transcript_hash": "ebd70beca47d"
  },
  {
    "classifications": [
      "current_live_openai_legacy_compatibility_leakage",
      "current_live_openai_human_followup_owner_leakage"
    ],
    "final_response": "If it is relevant, a demo operator for simulation notes; official OpenAI sales team for Enterprise can do a short legacy compatibility field only; primary close is official self-serve plan page or Enterprise contact-sales route. Are you mainly comparing plans for yourself, a small team, or a larger organization?",
    "generated_at": "2026-05-25T01:01:14.690284+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-030114.json",
    "transcript_hash": "b0e64f9b52b9"
  }
]
```
