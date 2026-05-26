# PUBLIC-OPENAI-LIVE-REHEARSAL-001

- Status: `pass`
- Total private records scanned: `638`
- Current OpenAI live records found: `11`
- Records after `b58aa53` or latest marker: `11`
- Stale/historical OpenAI records ignored: `111`
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
- Opening origin missing count: `0`
- Explanation question misrouted count: `0`
- Plan-label trap count: `0`
- Team-context false-positive count: `0`
- Repeated wrong explanation count: `0`
- State initialized with recommendation count: `0`
- Stability guard owned adapter-turn count: `0`
- Intent-priority defect count: `0`
- Logic-generalization defect count: `0`
- Spoken sales naturalness defect count: `0`
- Uploaded transcript spoken naturalness defect count: `6`
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
  "current_live_openai_intent_priority_defect": 1,
  "current_live_openai_internal_process_wording": 7,
  "current_live_openai_legacy_field_leakage": 2,
  "current_live_openai_loop_or_repeated_prompt": 8,
  "current_live_openai_missed_recommendation": 2,
  "current_live_openai_opening_origin_missing": 1,
  "current_live_openai_runtime_defect": 9,
  "current_live_openai_sales_performance_defect": 8,
  "current_live_openai_sales_quality_defect": 9,
  "current_live_openai_spoken_sales_naturalness_defect": 7,
  "current_openai_live_success": 2,
  "expected_dry_run_historical_record": 11,
  "fixed_by_replay_after_patch": 9,
  "needs_human_review": 9,
  "pre_patch_current_live_defect": 9,
  "stale_or_unknown_version_artifact": 100
}
```

## Latest Uploaded Transcript Audit

```json
{
  "classification_counts": {
    "current_live_openai_article_says_spoken": 3,
    "current_live_openai_internal_process_wording": 1,
    "current_live_openai_repeated_exact_response_after_new_question": 1,
    "current_live_openai_source_note_spoken": 3,
    "current_live_openai_source_of_truth_spoken": 3,
    "current_live_openai_spoken_sales_naturalness_defect": 6,
    "current_live_openai_state_downgrade_after_headroom": 3
  },
  "latest_source_file": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-d290511e-02dd-4bb2-8460-73715c637838-transcript.json",
  "raw_private_transcript_copied_to_public_evidence": false,
  "record_count": 9,
  "records": [
    {
      "classification_counts": {
        "current_live_openai_article_says_spoken": 3,
        "current_live_openai_internal_process_wording": 1,
        "current_live_openai_repeated_exact_response_after_new_question": 1,
        "current_live_openai_source_note_spoken": 3,
        "current_live_openai_source_of_truth_spoken": 3,
        "current_live_openai_spoken_sales_naturalness_defect": 6,
        "current_live_openai_state_downgrade_after_headroom": 3
      },
      "classifications": [
        "current_live_openai_internal_process_wording",
        "current_live_openai_spoken_sales_naturalness_defect",
        "current_live_openai_source_note_spoken",
        "current_live_openai_article_says_spoken",
        "current_live_openai_source_of_truth_spoken",
        "current_live_openai_repeated_exact_response_after_new_question",
        "current_live_openai_state_downgrade_after_headroom"
      ],
      "evidence": [
        {
          "agent_response_hash": "eda918ce2514",
          "classes": [
            "current_live_openai_internal_process_wording",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "7d2a521bf264",
          "sanitized_agent_markers": [
            "internal/process wording"
          ],
          "turn_index": 7
        },
        {
          "agent_response_hash": "6fa61784a68b",
          "classes": [
            "current_live_openai_source_note_spoken",
            "current_live_openai_article_says_spoken",
            "current_live_openai_source_of_truth_spoken",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "81c39181f546",
          "sanitized_agent_markers": [
            "current_live_openai_source_note_spoken",
            "current_live_openai_article_says_spoken",
            "current_live_openai_source_of_truth_spoken"
          ],
          "turn_index": 8
        },
        {
          "agent_response_hash": "394779b76aab",
          "classes": [
            "current_live_openai_source_note_spoken",
            "current_live_openai_article_says_spoken",
            "current_live_openai_source_of_truth_spoken",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "5178bf81a580",
          "sanitized_agent_markers": [
            "current_live_openai_source_note_spoken",
            "current_live_openai_article_says_spoken",
            "current_live_openai_source_of_truth_spoken"
          ],
          "turn_index": 9
        },
        {
          "agent_response_hash": "394779b76aab",
          "classes": [
            "current_live_openai_source_note_spoken",
            "current_live_openai_article_says_spoken",
            "current_live_openai_source_of_truth_spoken",
            "current_live_openai_repeated_exact_response_after_new_question",
            "current_live_openai_state_downgrade_after_headroom",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "63275155ddd2",
          "sanitized_agent_markers": [
            "current_live_openai_source_note_spoken",
            "current_live_openai_article_says_spoken",
            "current_live_openai_source_of_truth_spoken"
          ],
          "turn_index": 10
        },
        {
          "agent_response_hash": "da1a77147a2e",
          "classes": [
            "current_live_openai_state_downgrade_after_headroom",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "10ebeef3c868",
          "sanitized_agent_markers": [],
          "turn_index": 11
        },
        {
          "agent_response_hash": "2a0399884c1a",
          "classes": [
            "current_live_openai_state_downgrade_after_headroom",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "b859418681bf",
          "sanitized_agent_markers": [],
          "turn_index": 12
        }
      ],
      "generated_at": "2026-05-26T15:16:37.586Z",
      "raw_private_transcript_copied_to_public_evidence": false,
      "session_id_hash": "6787af0c8f20",
      "source_file": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-d290511e-02dd-4bb2-8460-73715c637838-transcript.json",
      "source_file_hash": "28eecc47429f",
      "turn_count": 12
    }
  ],
  "status": "classified_pre_patch_live_defects"
}
```

## Human Review Examples

```json
[
  {
    "classifications": [
      "current_live_openai_opening_origin_missing",
      "current_live_openai_intent_priority_defect",
      "current_live_openai_sales_performance_defect"
    ],
    "final_response": "Hi, this is Maya. I'm running a public-data ChatGPT plan-fit simulation. I can help compare ChatGPT plans at a high level using OpenAI's public plan information. Do you have a minute?",
    "generated_at": "2026-05-25T12:07:17.190656+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140717.json",
    "transcript_hash": "58f0d512c6ee"
  },
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
      "current_live_openai_internal_process_wording",
      "current_live_openai_loop_or_repeated_prompt",
      "current_live_openai_legacy_field_leakage",
      "current_live_openai_spoken_sales_naturalness_defect",
      "current_live_openai_sales_performance_defect"
    ],
    "final_response": "Quick check for a short legacy compatibility field only; primary close is official self-serve plan page or Enterprise contact-sales route: Are you mainly comparing plans for yourself, a small team, or a larger organization?",
    "generated_at": "2026-05-25T12:08:19.439347+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140819.json",
    "transcript_hash": "9fde2a350ac5"
  },
  {
    "classifications": [
      "current_live_openai_internal_process_wording",
      "current_live_openai_loop_or_repeated_prompt",
      "current_live_openai_missed_recommendation",
      "current_live_openai_legacy_field_leakage",
      "current_live_openai_spoken_sales_naturalness_defect",
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
      "current_live_openai_internal_process_wording",
      "current_live_openai_loop_or_repeated_prompt",
      "current_live_openai_missed_recommendation",
      "current_live_openai_spoken_sales_naturalness_defect",
      "current_live_openai_sales_performance_defect"
    ],
    "final_response": "I can only keep this to the current call scope. Should I keep checking that, or stop here?",
    "generated_at": "2026-05-25T12:09:23.590830+00:00",
    "redacted_synthetic_replay_hint": "Private buyer transcript withheld; use synthetic replay validator if a current dialogue defect is listed.",
    "source_file": "data/private/live-demo-001/LIVE-DEMO-001-turn-20260525-140923.json",
    "transcript_hash": "e06e309b66b3"
  }
]
```
