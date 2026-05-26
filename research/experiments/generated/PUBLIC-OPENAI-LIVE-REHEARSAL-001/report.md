# PUBLIC-OPENAI-LIVE-REHEARSAL-001

- Status: `pass`
- Total private records scanned: `677`
- Current OpenAI live records found: `11`
- Records after `b58aa53` or latest marker: `11`
- Stale/historical OpenAI records ignored: `150`
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
- Semantic 4H6 classification counts: `{"current_live_openai_asr_alias_gap_chacha_pt": 0, "current_live_openai_asr_alias_not_normalized": 0, "current_live_openai_blank_response_passed_validator": 0, "current_live_openai_business_enterprise_false_route": 0, "current_live_openai_cloud_claude_alias_gap": 0, "current_live_openai_conjunction_fidelity_error": 0, "current_live_openai_entity_keyword_overrode_intent": 0, "current_live_openai_internal_policy_spoken": 0, "current_live_openai_legacy_field_post_permission": 0, "current_live_openai_live_pipeline_integration_defect": 0, "current_live_openai_live_semantic_bypass": 0, "current_live_openai_negation_scope_ignored": 0, "current_live_openai_response_variation_failure": 0, "current_live_openai_semantic_generalization_defect": 0, "current_live_openai_semantic_misclassification": 0, "current_live_openai_speech_act_priority_failure": 0, "current_live_openai_stability_guard_generated_commercial_speech": 0, "current_live_openai_stability_guard_owned_recognized_turn": 0, "current_live_openai_state_mutation_from_explanation": 0, "current_live_openai_state_mutation_invariant_failed": 0, "current_live_openai_team_state_poisoned_by_negation": 0}`
- 4H7 live semantic pipeline counts: `{"current_live_openai_asr_alias_gap_chacha_pt": 0, "current_live_openai_business_enterprise_false_route": 0, "current_live_openai_cloud_claude_alias_gap": 0, "current_live_openai_legacy_field_post_permission": 0, "current_live_openai_live_pipeline_integration_defect": 0, "current_live_openai_live_semantic_bypass": 0, "current_live_openai_negation_scope_ignored": 0, "current_live_openai_stability_guard_owned_recognized_turn": 0, "current_live_openai_state_mutation_invariant_failed": 0, "current_live_openai_team_state_poisoned_by_negation": 0}`
- Spoken sales naturalness defect count: `0`
- Uploaded transcript spoken naturalness defect count: `8`
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
  "current_live_openai_internal_policy_spoken": 7,
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
  "stale_or_unknown_version_artifact": 139
}
```

## Latest Uploaded Transcript Audit

```json
{
  "classification_counts": {
    "current_live_openai_asr_alias_gap_chacha_pt": 2,
    "current_live_openai_asr_alias_not_normalized": 2,
    "current_live_openai_business_enterprise_false_route": 2,
    "current_live_openai_cloud_claude_alias_gap": 2,
    "current_live_openai_entity_keyword_overrode_intent": 2,
    "current_live_openai_internal_policy_spoken": 3,
    "current_live_openai_internal_process_wording": 3,
    "current_live_openai_legacy_field_leakage": 2,
    "current_live_openai_legacy_field_post_permission": 2,
    "current_live_openai_live_pipeline_integration_defect": 6,
    "current_live_openai_live_semantic_bypass": 2,
    "current_live_openai_negation_scope_ignored": 2,
    "current_live_openai_repeated_exact_response_after_new_question": 1,
    "current_live_openai_response_variation_failure": 1,
    "current_live_openai_semantic_generalization_defect": 2,
    "current_live_openai_semantic_misclassification": 2,
    "current_live_openai_speech_act_priority_failure": 3,
    "current_live_openai_spoken_sales_naturalness_defect": 8,
    "current_live_openai_stability_guard_generated_commercial_speech": 1,
    "current_live_openai_stability_guard_owned_recognized_turn": 1,
    "current_live_openai_state_mutation_invariant_failed": 2,
    "current_live_openai_team_state_poisoned_by_negation": 2
  },
  "latest_source_file": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-3c465ff1-c5e7-4211-8e70-8e1bdc789af5-transcript.json",
  "raw_private_transcript_copied_to_public_evidence": false,
  "record_count": 12,
  "records": [
    {
      "classification_counts": {
        "current_live_openai_internal_policy_spoken": 1,
        "current_live_openai_internal_process_wording": 1,
        "current_live_openai_spoken_sales_naturalness_defect": 1
      },
      "classifications": [
        "current_live_openai_internal_process_wording",
        "current_live_openai_internal_policy_spoken",
        "current_live_openai_spoken_sales_naturalness_defect"
      ],
      "evidence": [
        {
          "agent_response_hash": "917d89afc6be",
          "classes": [
            "current_live_openai_internal_process_wording",
            "current_live_openai_internal_policy_spoken",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "bf1255eaea13",
          "sanitized_agent_markers": [
            "internal/process wording"
          ],
          "turn_index": 6
        }
      ],
      "generated_at": "2026-05-26T19:20:21.519Z",
      "raw_private_transcript_copied_to_public_evidence": false,
      "session_id_hash": "e69044a285a5",
      "source_file": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-adc8611a-34ab-4155-9285-e461bf597f5a-transcript.json",
      "source_file_hash": "3aed6fb6f647",
      "turn_count": 7
    },
    {
      "classification_counts": {
        "current_live_openai_asr_alias_gap_chacha_pt": 1,
        "current_live_openai_asr_alias_not_normalized": 1,
        "current_live_openai_business_enterprise_false_route": 2,
        "current_live_openai_cloud_claude_alias_gap": 1,
        "current_live_openai_entity_keyword_overrode_intent": 2,
        "current_live_openai_internal_policy_spoken": 1,
        "current_live_openai_internal_process_wording": 1,
        "current_live_openai_legacy_field_leakage": 1,
        "current_live_openai_legacy_field_post_permission": 1,
        "current_live_openai_live_pipeline_integration_defect": 4,
        "current_live_openai_live_semantic_bypass": 1,
        "current_live_openai_negation_scope_ignored": 2,
        "current_live_openai_repeated_exact_response_after_new_question": 1,
        "current_live_openai_response_variation_failure": 1,
        "current_live_openai_semantic_generalization_defect": 2,
        "current_live_openai_semantic_misclassification": 1,
        "current_live_openai_speech_act_priority_failure": 1,
        "current_live_openai_spoken_sales_naturalness_defect": 5,
        "current_live_openai_state_mutation_invariant_failed": 2,
        "current_live_openai_team_state_poisoned_by_negation": 2
      },
      "classifications": [
        "current_live_openai_live_semantic_bypass",
        "current_live_openai_legacy_field_post_permission",
        "current_live_openai_internal_process_wording",
        "current_live_openai_semantic_misclassification",
        "current_live_openai_speech_act_priority_failure",
        "current_live_openai_legacy_field_leakage",
        "current_live_openai_internal_policy_spoken",
        "current_live_openai_live_pipeline_integration_defect",
        "current_live_openai_spoken_sales_naturalness_defect",
        "current_live_openai_negation_scope_ignored",
        "current_live_openai_state_mutation_invariant_failed",
        "current_live_openai_team_state_poisoned_by_negation",
        "current_live_openai_business_enterprise_false_route",
        "current_live_openai_semantic_generalization_defect",
        "current_live_openai_entity_keyword_overrode_intent",
        "current_live_openai_asr_alias_gap_chacha_pt",
        "current_live_openai_cloud_claude_alias_gap",
        "current_live_openai_asr_alias_not_normalized",
        "current_live_openai_repeated_exact_response_after_new_question",
        "current_live_openai_response_variation_failure"
      ],
      "evidence": [
        {
          "agent_response_hash": "6cfec7235ae1",
          "classes": [
            "current_live_openai_live_semantic_bypass",
            "current_live_openai_legacy_field_post_permission",
            "current_live_openai_internal_process_wording",
            "current_live_openai_semantic_misclassification",
            "current_live_openai_speech_act_priority_failure",
            "current_live_openai_legacy_field_leakage",
            "current_live_openai_internal_policy_spoken",
            "current_live_openai_live_pipeline_integration_defect",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "9472e06492ce",
          "sanitized_agent_markers": [
            "internal/process wording",
            "legacy field after permission",
            "semantic bypass after permission",
            "live pipeline integration defect"
          ],
          "turn_index": 2
        },
        {
          "agent_response_hash": "585e608fb88f",
          "classes": [
            "current_live_openai_negation_scope_ignored",
            "current_live_openai_state_mutation_invariant_failed",
            "current_live_openai_team_state_poisoned_by_negation",
            "current_live_openai_business_enterprise_false_route",
            "current_live_openai_semantic_generalization_defect",
            "current_live_openai_entity_keyword_overrode_intent",
            "current_live_openai_live_pipeline_integration_defect",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "f0f50cc110e1",
          "sanitized_agent_markers": [
            "negation scope ignored",
            "team state poisoned by negation",
            "business-enterprise false route",
            "state mutation invariant failed",
            "live pipeline integration defect"
          ],
          "turn_index": 3
        },
        {
          "agent_response_hash": "7c75d68dc552",
          "classes": [
            "current_live_openai_asr_alias_gap_chacha_pt",
            "current_live_openai_cloud_claude_alias_gap",
            "current_live_openai_asr_alias_not_normalized",
            "current_live_openai_live_pipeline_integration_defect",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "861e73580984",
          "sanitized_agent_markers": [
            "chacha/chatgpt alias gap",
            "cloud/claude alias gap",
            "live pipeline integration defect"
          ],
          "turn_index": 5
        },
        {
          "agent_response_hash": "713f2b2cdee1",
          "classes": [
            "current_live_openai_negation_scope_ignored",
            "current_live_openai_state_mutation_invariant_failed",
            "current_live_openai_team_state_poisoned_by_negation",
            "current_live_openai_business_enterprise_false_route",
            "current_live_openai_semantic_generalization_defect",
            "current_live_openai_entity_keyword_overrode_intent",
            "current_live_openai_live_pipeline_integration_defect",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "d7962b8d246d",
          "sanitized_agent_markers": [
            "negation scope ignored",
            "team state poisoned by negation",
            "business-enterprise false route",
            "state mutation invariant failed",
            "live pipeline integration defect"
          ],
          "turn_index": 6
        },
        {
          "agent_response_hash": "7c75d68dc552",
          "classes": [
            "current_live_openai_repeated_exact_response_after_new_question",
            "current_live_openai_response_variation_failure",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "32a1b9aa6b0e",
          "sanitized_agent_markers": [],
          "turn_index": 10
        }
      ],
      "generated_at": "2026-05-26T19:24:44.703Z",
      "raw_private_transcript_copied_to_public_evidence": false,
      "session_id_hash": "3cf65c81a9f1",
      "source_file": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-4680965d-f60e-4186-bfe3-4eaceb0ad183-transcript.json",
      "source_file_hash": "fd08ae8e4d93",
      "turn_count": 10
    },
    {
      "classification_counts": {
        "current_live_openai_asr_alias_gap_chacha_pt": 1,
        "current_live_openai_asr_alias_not_normalized": 1,
        "current_live_openai_cloud_claude_alias_gap": 1,
        "current_live_openai_internal_policy_spoken": 1,
        "current_live_openai_internal_process_wording": 1,
        "current_live_openai_legacy_field_leakage": 1,
        "current_live_openai_legacy_field_post_permission": 1,
        "current_live_openai_live_pipeline_integration_defect": 2,
        "current_live_openai_live_semantic_bypass": 1,
        "current_live_openai_semantic_misclassification": 1,
        "current_live_openai_speech_act_priority_failure": 2,
        "current_live_openai_spoken_sales_naturalness_defect": 2,
        "current_live_openai_stability_guard_generated_commercial_speech": 1,
        "current_live_openai_stability_guard_owned_recognized_turn": 1
      },
      "classifications": [
        "current_live_openai_live_semantic_bypass",
        "current_live_openai_legacy_field_post_permission",
        "current_live_openai_internal_process_wording",
        "current_live_openai_semantic_misclassification",
        "current_live_openai_speech_act_priority_failure",
        "current_live_openai_legacy_field_leakage",
        "current_live_openai_internal_policy_spoken",
        "current_live_openai_live_pipeline_integration_defect",
        "current_live_openai_spoken_sales_naturalness_defect",
        "current_live_openai_asr_alias_gap_chacha_pt",
        "current_live_openai_cloud_claude_alias_gap",
        "current_live_openai_stability_guard_owned_recognized_turn",
        "current_live_openai_asr_alias_not_normalized",
        "current_live_openai_stability_guard_generated_commercial_speech"
      ],
      "evidence": [
        {
          "agent_response_hash": "6cfec7235ae1",
          "classes": [
            "current_live_openai_live_semantic_bypass",
            "current_live_openai_legacy_field_post_permission",
            "current_live_openai_internal_process_wording",
            "current_live_openai_semantic_misclassification",
            "current_live_openai_speech_act_priority_failure",
            "current_live_openai_legacy_field_leakage",
            "current_live_openai_internal_policy_spoken",
            "current_live_openai_live_pipeline_integration_defect",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "9472e06492ce",
          "sanitized_agent_markers": [
            "internal/process wording",
            "legacy field after permission",
            "semantic bypass after permission",
            "live pipeline integration defect"
          ],
          "turn_index": 2
        },
        {
          "agent_response_hash": "61cccbea609b",
          "classes": [
            "current_live_openai_asr_alias_gap_chacha_pt",
            "current_live_openai_cloud_claude_alias_gap",
            "current_live_openai_stability_guard_owned_recognized_turn",
            "current_live_openai_asr_alias_not_normalized",
            "current_live_openai_stability_guard_generated_commercial_speech",
            "current_live_openai_speech_act_priority_failure",
            "current_live_openai_live_pipeline_integration_defect",
            "current_live_openai_spoken_sales_naturalness_defect"
          ],
          "customer_transcript_hash": "e6c4b0197073",
          "sanitized_agent_markers": [
            "chacha/chatgpt alias gap",
            "cloud/claude alias gap",
            "stability guard owned recognized turn",
            "live pipeline integration defect"
          ],
          "turn_index": 4
        }
      ],
      "generated_at": "2026-05-26T19:30:43.523Z",
      "raw_private_transcript_copied_to_public_evidence": false,
      "session_id_hash": "b91fa05a43cc",
      "source_file": "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-3c465ff1-c5e7-4211-8e70-8e1bdc789af5-transcript.json",
      "source_file_hash": "7556e298f6c6",
      "turn_count": 10
    }
  ],
  "selected_record_count": 3,
  "status": "classified_pre_patch_live_defects",
  "target_record_count": 3,
  "target_source_files": [
    "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-adc8611a-34ab-4155-9285-e461bf597f5a-transcript.json",
    "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-4680965d-f60e-4186-bfe3-4eaceb0ad183-transcript.json",
    "data/private/live-demo-003/raw-turns/browser-transcript/LIVE-DEMO-001-3c465ff1-c5e7-4211-8e70-8e1bdc789af5-transcript.json"
  ]
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
      "current_live_openai_internal_policy_spoken",
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
      "current_live_openai_internal_policy_spoken",
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
      "current_live_openai_internal_policy_spoken",
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
