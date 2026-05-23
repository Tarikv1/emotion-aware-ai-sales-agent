# CONVERSATIONAL-RESONANCE-REVIEW-001

## 1. Summary
Generated a dry-run conversational resonance packet for human review. Runtime behavior was not changed.

## 2. Packet Size
- Conversations: `60`
- Turn records: `310`

## 3. Campaign Coverage
- `routesignal_live_demo`
- `synthetic-insurance-review`
- `synthetic-b2b-saas-operations`
- `synthetic-automotive-service-review`
- `synthetic-home-services-estimate`

## 4. Arc Coverage
- `b2b_workplace_interruption`
- `b2c_home_life_interruption`
- `busy_distracted`
- `casual_small_talk`
- `emotional_frustration_venting`
- `family_stakeholder_context`
- `financial_stress_budget_emotion`
- `irrelevant_story_off_topic_ramble`
- `joking_sarcasm`
- `prior_bad_experience`
- `sensitive_personal_data_boundary`
- `serious_hardship_bad_timing`

## 5. Resonance Warning Counts
- `asked_personal_probe`: `4`
- `collected_sensitive_detail`: `10`
- `continued_sales_during_hardship`: `23`
- `failed_to_stop_on_serious_bad_timing`: `5`
- `fake_callback_or_calendar_claim`: `24`
- `full_sales_menu_after_social_context`: `105`
- `ignored_human_context`: `297`
- `no_relevance_bridge`: `30`
- `pushy_after_financial_stress`: `3`
- `wrong_person_not_handled`: `27`

## 6. Strongest-Looking Conversations By Mechanical Signals Only
- `conversational-resonance-review-001-02-01-synthetic-insurance-review-casual_small_talk`: `2` warnings
- `conversational-resonance-review-001-03-08-synthetic-b2b-saas-operations-emotional_frustration_venting`: `3` warnings
- `conversational-resonance-review-001-01-08-routesignal_live_demo-emotional_frustration_venting`: `4` warnings
- `conversational-resonance-review-001-03-01-synthetic-b2b-saas-operations-casual_small_talk`: `4` warnings
- `conversational-resonance-review-001-03-02-synthetic-b2b-saas-operations-busy_distracted`: `4` warnings
- `conversational-resonance-review-001-03-04-synthetic-b2b-saas-operations-financial_stress_budget_emotion`: `4` warnings
- `conversational-resonance-review-001-03-05-synthetic-b2b-saas-operations-prior_bad_experience`: `4` warnings
- `conversational-resonance-review-001-03-07-synthetic-b2b-saas-operations-joking_sarcasm`: `4` warnings
- `conversational-resonance-review-001-03-11-synthetic-b2b-saas-operations-b2c_home_life_interruption`: `4` warnings
- `conversational-resonance-review-001-03-12-synthetic-b2b-saas-operations-b2b_workplace_interruption`: `4` warnings

## 7. Most Concerning Conversations By Mechanical Signals Only
- `conversational-resonance-review-001-01-03-routesignal_live_demo-serious_hardship_bad_timing`: `11` warnings; flags `continued_sales_during_hardship, failed_to_stop_on_serious_bad_timing, fake_callback_or_calendar_claim, ignored_human_context`
- `conversational-resonance-review-001-02-09-synthetic-insurance-review-irrelevant_story_off_topic_ramble`: `11` warnings; flags `full_sales_menu_after_social_context, ignored_human_context, no_relevance_bridge`
- `conversational-resonance-review-001-04-09-synthetic-automotive-service-review-irrelevant_story_off_topic_ramble`: `11` warnings; flags `full_sales_menu_after_social_context, ignored_human_context, no_relevance_bridge`
- `conversational-resonance-review-001-05-09-synthetic-home-services-estimate-irrelevant_story_off_topic_ramble`: `11` warnings; flags `full_sales_menu_after_social_context, ignored_human_context, no_relevance_bridge`
- `conversational-resonance-review-001-01-06-routesignal_live_demo-family_stakeholder_context`: `10` warnings; flags `fake_callback_or_calendar_claim, ignored_human_context, wrong_person_not_handled`
- `conversational-resonance-review-001-01-09-routesignal_live_demo-irrelevant_story_off_topic_ramble`: `10` warnings; flags `fake_callback_or_calendar_claim, ignored_human_context, no_relevance_bridge`
- `conversational-resonance-review-001-01-10-routesignal_live_demo-sensitive_personal_data_boundary`: `10` warnings; flags `asked_personal_probe, collected_sensitive_detail, fake_callback_or_calendar_claim, ignored_human_context, wrong_person_not_handled`
- `conversational-resonance-review-001-02-03-synthetic-insurance-review-serious_hardship_bad_timing`: `10` warnings; flags `continued_sales_during_hardship, full_sales_menu_after_social_context, ignored_human_context`
- `conversational-resonance-review-001-04-03-synthetic-automotive-service-review-serious_hardship_bad_timing`: `10` warnings; flags `continued_sales_during_hardship, full_sales_menu_after_social_context, ignored_human_context`
- `conversational-resonance-review-001-05-03-synthetic-home-services-estimate-serious_hardship_bad_timing`: `10` warnings; flags `continued_sales_during_hardship, full_sales_menu_after_social_context, ignored_human_context`

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

## 9. What ChatGPT/Human Reviewer Should Evaluate Next
- Whether human context is acknowledged without turning the agent into a general chatbot.
- Whether serious hardship and sensitive data boundaries stop or redirect respectfully.
- Whether financial stress and prior bad experiences are handled with control rather than pressure.
- Whether stakeholder/right-person context is handled without fake handoff actions.

## 10. Preliminary Recommendation Only
Preliminary only: use this packet to decide whether a later implementation slice should add social-context and hardship-specific response shapes. Do not treat the warning counts as final sales-quality scores.
