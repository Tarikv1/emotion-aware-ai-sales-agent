# PUBLIC-OPENAI-LIVE-REHEARSAL-001

- Status: `pass`
- Total private records scanned: `549`
- Current OpenAI live records found: `11`
- Records after `b58aa53` or latest marker: `11`
- Stale/historical OpenAI records ignored: `22`
- Live TTS used count: `11`
- Dry-run count: `0`
- ElevenLabs call made count: `11`
- TTS provider calls made count: `11`
- Audio file created count: `11`
- Raw voice ID logged count: `0`
- Runtime defect count: `0`
- Pre-patch private live defects: `9`
- Fixed by replay after patch: `9`
- Post-patch replay defects: `0`
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
  "current_live_openai_assumption_repair_defect": 1,
  "current_live_openai_human_followup_owner_leakage": 1,
  "current_live_openai_legacy_compatibility_leakage": 2,
  "current_live_openai_loop_or_repeated_prompt": 8,
  "current_live_openai_premature_plan_comparison": 3,
  "current_live_openai_runtime_defect": 9,
  "current_live_openai_source_trust_answer_defect": 3,
  "current_openai_live_success": 2,
  "expected_dry_run_historical_record": 11,
  "fixed_by_replay_after_patch": 9,
  "needs_human_review": 9,
  "pre_patch_current_live_defect": 9,
  "stale_or_unknown_version_artifact": 11
}
```

## Human Review Examples

```json
[
  {
    "classifications": [
      "current_live_openai_premature_plan_comparison",
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
      "current_live_openai_assumption_repair_defect"
    ],
    "final_response": "Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?",
    "generated_at": "2026-05-25T12:07:51.246389+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140751.json",
    "transcript_hash": "b51cb0a85d6c"
  },
  {
    "classifications": [
      "current_live_openai_premature_plan_comparison",
      "current_live_openai_loop_or_repeated_prompt",
      "current_live_openai_legacy_compatibility_leakage"
    ],
    "final_response": "Quick check for a short legacy compatibility field only; primary close is official self-serve plan page or Enterprise contact-sales route: Are you mainly comparing plans for yourself, a small team, or a larger organization?",
    "generated_at": "2026-05-25T12:08:19.439347+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140819.json",
    "transcript_hash": "9fde2a350ac5"
  },
  {
    "classifications": [
      "current_live_openai_premature_plan_comparison",
      "current_live_openai_loop_or_repeated_prompt",
      "current_live_openai_legacy_compatibility_leakage",
      "current_live_openai_human_followup_owner_leakage"
    ],
    "final_response": "If it is relevant, a demo operator for simulation notes; official OpenAI sales team for Enterprise can do a short legacy compatibility field only; primary close is official self-serve plan page or Enterprise contact-sales route. Are you mainly comparing plans for yourself, a small team, or a larger organization?",
    "generated_at": "2026-05-25T12:08:58.130592+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140858.json",
    "transcript_hash": "7f9e65be5575"
  },
  {
    "classifications": [
      "current_live_openai_loop_or_repeated_prompt"
    ],
    "final_response": "I can only keep this to the current call scope. Should I keep checking that, or stop here?",
    "generated_at": "2026-05-25T12:09:23.590830+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140923.json",
    "transcript_hash": "e06e309b66b3"
  }
]
```
