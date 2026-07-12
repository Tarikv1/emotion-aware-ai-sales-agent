# Task 9 Care Explicit-Cost Report

## Status

Implemented the second narrow Atlas care-follow-up product correction in the three authorized product sources only.

No provider, API, dashboard, browser, Procedures, or outbound calls were made. I did not edit tests, criteria, validators, runners, manifests, evidence artifacts, tools, provider settings, or KB attachments. Dirty generated evidence already present in the worktree was left untouched.

## Files Changed

- `runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md`
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md`
- `runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md`

## Product Change

- Kept the existing care mapping unchanged: Essential Care `$79`, Business Care `$149`, Growth Care `$249`.
- Tightened care follow-up so that, after one care plan is quoted, another care-plan price now requires a direct `price` / `cost` / `fee` question for that different scope.
- Treated follow-up questions about what counts as ordinary or heavy edits/reporting, what is included, whether edits are separate, or what would move the work into another plan as scope clarification only.
- Removed the prior exception that let Emma disclose another care-plan price merely because the buyer asked about ordinary edits or monthly reporting.

## Exact Validation Results

```text
python scripts/validate_elevenlabs_039_end_call_edge_case_hardening.py
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-039-end-call-edge-case-hardening",
  "prompt_word_count": 1948,
  "analysis_criteria_count": 30,
  "test_count": 4,
  "active_upload_manifest_changed": false,
  "procedures_changed": false,
  "dashboard_test_execution_not_performed_by_validator": true
}

python scripts/validate_elevenlabs_036_natural_sales_scenarios_tests.py
{
  "status": "pass",
  "checkpoint_id": "ELEVENLABS-036-natural-sales-scenarios",
  "test_count": 10,
  "target_folder": "ELEVENLABS-036-natural-sales-scenarios",
  "simulated_user_model": "gemini-2.5-flash",
  "evaluation_model": "gemini-2.5-flash",
  "max_turns_by_test": {
    "sim_036_email_confirmation_spoken_email_two_step": 12,
    "sim_036_email_plus_free_question_confirmation": 14,
    "sim_036_future_price_ballpark_no_overpricing": 16,
    "sim_036_scheduling_simple_request_vs_live_integration": 16,
    "sim_036_crm_payment_capability_before_price": 16,
    "sim_036_custom_dashboard_scoped_separately": 16,
    "sim_036_free_mockup_visual_not_working_site": 12,
    "sim_036_next_step_questions_no_cta_fatigue": 18,
    "sim_036_guarantee_required_clean_disqualify": 10,
    "sim_036_goodbye_take_care_no_loop": 12
  },
  "businesses": [
    "Blue Harbor Kayak Rentals",
    "Cedar Ridge Auto Glass",
    "ClearPath Tutoring",
    "Iron Gate Garage Doors",
    "Mesa Fit Studio",
    "Oakwood Pediatric Dentistry",
    "Pine & Stone Landscaping",
    "RapidRooter Plumbing",
    "Sunrise Bagel Shop",
    "Velvet Paw Grooming"
  ],
  "vertical_count": 10,
  "alpha_routing_markers_present": false,
  "live_provider_calls_made": false,
  "active_upload_manifest_changed": false
}

git diff --check
warning: in the working copy of 'runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_output_quality_rules.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'runtime/providers/elevenlabs_agents/knowledge_base/atlas_web_studio/atlas_price_scope_cost_drivers.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'runtime/providers/elevenlabs_agents/prompts/web_design_atlas_sales_prompt.md', LF will be replaced by CRLF the next time Git touches it
```

## Self-Review

- Scope stayed inside the three authorized product files plus this report.
- The net behavior change is narrow: the agent can still quote `$149` or `$249`, but only after a direct price/cost/fee ask for that different care scope.
- Scope-only follow-ups now explain boundaries without naming another care price, which directly addresses the observed failure mode.
- The change does increase prompt length versus the prior state; the required validator still passes at `prompt_word_count = 1948`.

## Commit

- Committed with message: `fix: tighten Atlas care follow-up price gate`
