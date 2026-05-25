# PUBLIC-OPENAI-LIVE-REHEARSAL-001

- Status: `pass`
- Total private records scanned: `604`
- Current OpenAI live records found: `11`
- Records after `b58aa53` or latest marker: `11`
- Stale/historical OpenAI records ignored: `77`
- Live TTS used count: `11`
- Dry-run count: `0`
- ElevenLabs call made count: `11`
- TTS provider calls made count: `11`
- Audio file created count: `11`
- Raw voice ID logged count: `0`
- Runtime defect count: `0`
- Pre-patch private live defects: `8`
- Fixed by replay after patch: `8`
- Post-patch replay defects: `0`
- ASR product alias issue count: `0`
- Internal policy language leak count: `0`
- Price question refusal count: `0`
- Plan recommendation stall count: `0`
- Information-not-selling count: `0`
- Missed recommendation count: `0`
- Missed close count: `0`
- Weak value frame count: `0`
- Repeated competitor caveat count: `0`
- False limit-pain count: `0`
- Overqualified without recommendation count: `0`
- Sales-performance defect count: `0`
- Premature no-fit caveat count: `0`
- Price objection repeated-price count: `0`
- Wrong decision-stage count: `0`
- Pro-tier selection defect count: `0`
- Signup close stage-mismatch count: `0`
- Stability guard owned sales-turn count: `0`
- Sales momentum defect count: `0`
- Legacy field leakage count: `0`
- RouteSignal contamination count: `0`
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
  "current_live_openai_legacy_field_leakage": 2,
  "current_live_openai_loop_or_repeated_prompt": 8,
  "current_live_openai_missed_recommendation": 2,
  "current_live_openai_runtime_defect": 8,
  "current_live_openai_sales_performance_defect": 2,
  "current_live_openai_sales_quality_defect": 8,
  "current_openai_live_success": 3,
  "expected_dry_run_historical_record": 11,
  "fixed_by_replay_after_patch": 8,
  "needs_human_review": 8,
  "pre_patch_current_live_defect": 8,
  "stale_or_unknown_version_artifact": 66
}
```

## Human Review Examples

```json
[
  {
    "classifications": [
      "current_live_openai_loop_or_repeated_prompt"
    ],
    "final_response": "Are you comparing plans for yourself, a small team, or a larger organization?",
    "generated_at": "2026-05-25T12:07:37.160816+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140737.json",
    "transcript_hash": "e7ed65d6d512"
  },
  {
    "classifications": [
      "current_live_openai_loop_or_repeated_prompt",
      "current_live_openai_legacy_field_leakage"
    ],
    "final_response": "Quick check for a short legacy compatibility field only; primary close is official self-serve plan page or Enterprise contact-sales route: Are you mainly comparing plans for yourself, a small team, or a larger organization?",
    "generated_at": "2026-05-25T12:08:19.439347+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140819.json",
    "transcript_hash": "9fde2a350ac5"
  },
  {
    "classifications": [
      "current_live_openai_loop_or_repeated_prompt",
      "current_live_openai_missed_recommendation",
      "current_live_openai_legacy_field_leakage",
      "current_live_openai_sales_performance_defect"
    ],
    "final_response": "If it is relevant, a demo operator for simulation notes; official OpenAI sales team for Enterprise can do a short legacy compatibility field only; primary close is official self-serve plan page or Enterprise contact-sales route. Are you mainly comparing plans for yourself, a small team, or a larger organization?",
    "generated_at": "2026-05-25T12:08:58.130592+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140858.json",
    "transcript_hash": "7f9e65be5575"
  },
  {
    "classifications": [
      "current_live_openai_loop_or_repeated_prompt",
      "current_live_openai_missed_recommendation",
      "current_live_openai_sales_performance_defect"
    ],
    "final_response": "I can only keep this to the current call scope. Should I keep checking that, or stop here?",
    "generated_at": "2026-05-25T12:09:23.590830+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140923.json",
    "transcript_hash": "e06e309b66b3"
  },
  {
    "classifications": [
      "current_live_openai_loop_or_repeated_prompt"
    ],
    "final_response": "I can only keep this to the current call scope. Should I keep checking that, or stop here?",
    "generated_at": "2026-05-25T12:09:33.994316+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140933.json",
    "transcript_hash": "9c4507eaa88a"
  }
]
```
