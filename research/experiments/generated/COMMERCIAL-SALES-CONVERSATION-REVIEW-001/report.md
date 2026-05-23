# COMMERCIAL-SALES-CONVERSATION-REVIEW-001

## 1. Summary
Validated a dry-run commercial sales conversation packet for human review. Codex did not assign final sales-quality scores.
- Validation status: `passed`

## 2. Packet Size
- Conversations: `50`
- Turn records: `275`

## 3. Campaign Coverage
- `routesignal_live_demo`
- `synthetic-automotive-service-review`
- `synthetic-b2b-saas-operations`
- `synthetic-home-services-estimate`
- `synthetic-insurance-review`

## 4. Arc Coverage
- `asr_garble`
- `confusion_loop_resistance`
- `direct_question`
- `no_fit_stop`
- `objection`
- `smooth_qualified_appointment`
- `social_conversation_management`
- `tentative_pain`
- `time_pressure`
- `trust_challenge`

## 5. Mechanical Warning Counts
- `appointment_not_asked_when_ready`: `40`
- `no_acknowledgement`: `132`
- `over_deferential_stop_offer`: `74`
- `repeated_full_menu`: `15`

## 6. Strongest-Looking Conversations By Mechanical Signals Only
- `commercial-sales-conversation-review-001-01-05-routesignal_live_demo-objection`: `1` warnings
- `commercial-sales-conversation-review-001-01-07-routesignal_live_demo-confusion_loop_resistance`: `1` warnings
- `commercial-sales-conversation-review-001-02-05-synthetic-insurance-review-objection`: `1` warnings
- `commercial-sales-conversation-review-001-03-05-synthetic-b2b-saas-operations-objection`: `1` warnings
- `commercial-sales-conversation-review-001-04-05-synthetic-automotive-service-review-objection`: `1` warnings
- `commercial-sales-conversation-review-001-05-05-synthetic-home-services-estimate-objection`: `1` warnings
- `commercial-sales-conversation-review-001-01-02-routesignal_live_demo-time_pressure`: `2` warnings
- `commercial-sales-conversation-review-001-01-09-routesignal_live_demo-asr_garble`: `2` warnings

## 7. Most Concerning Conversations By Mechanical Signals Only
- `commercial-sales-conversation-review-001-02-08-synthetic-insurance-review-social_conversation_management`: `8` warnings; flags `no_acknowledgement, over_deferential_stop_offer, repeated_full_menu`
- `commercial-sales-conversation-review-001-04-08-synthetic-automotive-service-review-social_conversation_management`: `8` warnings; flags `no_acknowledgement, over_deferential_stop_offer, repeated_full_menu`
- `commercial-sales-conversation-review-001-05-08-synthetic-home-services-estimate-social_conversation_management`: `8` warnings; flags `no_acknowledgement, over_deferential_stop_offer, repeated_full_menu`
- `commercial-sales-conversation-review-001-01-04-routesignal_live_demo-direct_question`: `6` warnings; flags `appointment_not_asked_when_ready, no_acknowledgement, over_deferential_stop_offer`
- `commercial-sales-conversation-review-001-03-04-synthetic-b2b-saas-operations-direct_question`: `6` warnings; flags `appointment_not_asked_when_ready, no_acknowledgement, over_deferential_stop_offer`
- `commercial-sales-conversation-review-001-03-08-synthetic-b2b-saas-operations-social_conversation_management`: `6` warnings; flags `no_acknowledgement, over_deferential_stop_offer`
- `commercial-sales-conversation-review-001-04-04-synthetic-automotive-service-review-direct_question`: `6` warnings; flags `appointment_not_asked_when_ready, no_acknowledgement, over_deferential_stop_offer`
- `commercial-sales-conversation-review-001-05-04-synthetic-home-services-estimate-direct_question`: `6` warnings; flags `appointment_not_asked_when_ready, no_acknowledgement, over_deferential_stop_offer`

## 8. Safety Boundary Summary
- Provider calls made: `false`
- Local LLM calls made: `false`
- Live TTS used: `false`
- Sends email: `false`
- Creates calendar event: `false`
- Writes CRM: `false`
- Opens PROD-102: `false`
- Customer audio uploaded to Python server: `false`
- Customer audio uploaded to TTS provider: `false`
- Raw email-like values found: `0`
- Secret-like values found: `0`

## Universalization Drift Risks
- `UDR-001` `actual_architecture_drift`: Universal runtime branches on synthetic fixture campaign ids.
  - File: `runtime/core/universal_conversation_policy_runtime.py` lines `417, 419, 421, 423`
  - Risk: Generic sales behavior can become coupled to fixture ids instead of campaign facts.
  - Follow-up: Move primary diagnostic phrase selection to campaign config/adapters.
- `UDR-002` `temporary_bridge_should_move_to_campaign_config`: Universal runtime maps verticals directly to customer-facing gap phrases.
  - File: `runtime/core/universal_conversation_policy_runtime.py` lines `417, 419, 421, 423`
  - Risk: A new campaign in the same vertical may inherit the wrong primary pain hypothesis.
  - Follow-up: Use campaign fact slots such as core_diagnostic_gaps, gap_label, and gap_value_bridge.
- `UDR-003` `temporary_bridge_should_move_to_campaign_config`: RouteSignal-specific phrasing appears inside universal response rendering.
  - File: `runtime/core/universal_conversation_policy_runtime.py` lines `292, 293, 392, 393, 405, 406, 416, 754, 756, 757, 758`
  - Risk: RouteSignal preservation logic can leak into generic universal response shape code.
  - Follow-up: Keep RouteSignal-specific wording in RouteSignal campaign/playbook facts.
- `UDR-004` `temporary_bridge_should_move_to_campaign_config`: Customer-facing gap phrases are hardcoded in universal runtime helpers.
  - File: `runtime/core/universal_conversation_policy_runtime.py` lines `207, 294, 295, 296, 298, 299, 300, 382, 418, 420, 422, 424, 521, 524, 525, 556, 557, 559, 560, 561, 741, 742, 743, 744, 745, 746, 747, 748, 749, 750, 751, 752, 1155`
  - Risk: Sales copy and primary pain language will require code changes instead of config changes.
  - Follow-up: Expose the preferred customer-facing phrase per gap through campaign config.

## 9. What ChatGPT/Human Reviewer Should Evaluate Next
- Whether skeptical buyers would trust the agent after identity, privacy, and challenge turns.
- Whether pain implication questions feel commercially useful rather than scripted.
- Whether appointment asks arrive after enough consequence has been established.
- Whether social and ASR recovery turns preserve control without sounding evasive.

## 10. Recommended Next Likely Implementation Area
Preliminary only: social and conversation-management repair remains the most likely next implementation slice, because current matrix evidence still clusters there. Human review should confirm before implementation.
