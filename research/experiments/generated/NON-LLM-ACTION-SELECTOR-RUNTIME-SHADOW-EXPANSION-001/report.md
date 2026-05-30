# NON-LLM-ACTION-SELECTOR-RUNTIME-SHADOW-EXPANSION-001

- Status: pass
- Cases: 21
- Campaign coverage: b2b_saas, generic_insurance, generic_telecom, home_services, public_openai_plan, routesignal_preservation
- Selector/runtime disagreements: 17
- Genuine actionable selector/runtime disagreements: 1
- Runtime action unmapped: 20
- Metadata extraction failures: 0
- Evidence not actionable yet: 20
- False ASR repair mappings: 0
- Selector possible improvements/regressions: 0/1
- Candidate response hashes recorded: 21
- Raw candidate responses in shadow records: 0
- Safety blockers: 0
- Provider/OpenAI/Ultravox/ElevenLabs/local LLM/Ollama/TTS calls: false
- Live selector control: false
- Response replacement: false

## Disagreement By Campaign

- b2b_saas: selector_possible_regression=1, unknown=2
- generic_insurance: unknown=3
- generic_telecom: unknown=3
- home_services: unknown=3
- public_openai_plan: runtime_more_specific=1, same_action=4
- routesignal_preservation: unknown=4

## Disagreement Review Classification

- runtime_action_unmapped: 20
- selector_possible_regression: 1

## Manual Review Table

| case_id | campaign | utterance | runtime_semantic | runtime_action_id | selector_action_id | disagreement_type | review | actionable | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| phase_4k8_public_openai_001_price | public_openai_plan | How much does ChatGPT Plus cost? | public_plan_direct_price_answer |  | answer_price | same_action | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_public_openai_002_plan_fit | public_openai_plan | I code every day and hit limits, which plan should I pick? | public_plan_plus_sufficiency_answered |  | recommend_pro | same_action | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_public_openai_003_privacy | public_openai_plan | Do you store raw call transcripts? | public_plan_privacy_claim_boundary |  | respect_boundary | runtime_more_specific | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_public_openai_004_signup | public_openai_plan | Where do I sign up if I want to start? | public_plan_self_serve_next_step_answered |  | answer_signup_path | same_action | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_public_openai_005_boundary | public_openai_plan | Can you buy the plan for me now? | public_plan_payment_boundary |  | respect_boundary | same_action | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_generic_insurance_001 | generic_insurance | yeah sure | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_generic_insurance_002 | generic_insurance | premium is a problem | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_generic_insurance_003 | generic_insurance | Can you tell me exactly what the policy covers? | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_generic_telecom_001 | generic_telecom | yeah sure | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_generic_telecom_002 | generic_telecom | coverage is the issue | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_generic_telecom_003 | generic_telecom | Can you guarantee the speed? | continue_with_session_policy |  | respect_boundary | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_home_services_001 | home_services | yeah sure | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_home_services_002 | home_services | the estimate is unclear | continue_with_session_policy |  | clarify_question_scope | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_home_services_003 | home_services | Can you quote it without an inspection? | guarded_composer_passthrough |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_b2b_saas_001 | b2b_saas | yeah sure | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_b2b_saas_002 | b2b_saas | manual work is a problem | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_b2b_saas_003 | b2b_saas | Does it integrate securely with Salesforce? | answer_campaign_claim_boundary | respect_boundary | ask_use_case_gap | selector_possible_regression | selector_possible_regression | true | runtime mapped to respect_boundary, while selector chose ask_use_case_gap |
| phase_4k8_routesignal_001 | routesignal_preservation | __agent_open__ | open_with_permission |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_routesignal_002 | routesignal_preservation | yeah sure | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_routesignal_003 | routesignal_preservation | callbacks are fine | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
| phase_4k8_routesignal_004 | routesignal_preservation | tomorrow at 3 works | continue_with_session_policy |  | ask_use_case_gap | unknown | runtime_action_unmapped | false | runtime metadata was present, but conservative mapping found no controlled runtime action |
