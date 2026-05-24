# LIVE-INSPIRED-ADVERSARIAL-DIALOGUE-MATRIX-001 Review Packet

This packet is mechanical triage evidence only. Codex did not assign final sales-quality labels.

- Scenario count: `729`
- Core gate failures: `0`
- Exploratory red findings: `263`

## Review Priorities
### adv-multi-campaign-contamination-stress-synthetic-automotive-service-review-02
- Campaign: `synthetic-automotive-service-review`
- Family: `multi_campaign_contamination_stress`
- Mechanical flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around repair timing. If that is not relevant, I should stop here.

### adv-multi-campaign-contamination-stress-synthetic-insurance-review-02
- Campaign: `synthetic-insurance-review`
- Family: `multi_campaign_contamination_stress`
- Mechanical flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around premium pressure. If that is not relevant, I should stop here.

### adv-multi-campaign-contamination-stress-synthetic-telecom-plan-review-02
- Campaign: `synthetic-telecom-plan-review`
- Family: `multi_campaign_contamination_stress`
- Mechanical flags: `internal_wording_leak`
- Buyer script: `['__agent_open__', 'I need insurance coverage', 'why are you talking about something else']`
- Final response: Fair question. This call is about a short human review around plan fit. If that is not relevant, I should stop here.

### adv-buyer-correction-contradiction-stress-synthetic-automotive-service-review-04
- Campaign: `synthetic-automotive-service-review`
- Family: `buyer_correction_contradiction_stress`
- Mechanical flags: `false_assumption_not_repaired, repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', "that's not my issue"]`
- Final response: The quick check is whether any of these areas is worth a short service advisor inspection review: vehicle issue, repair timing, or warranty or estimate. If not, I can stop here; which part should I check first?

### adv-buyer-says-agent-is-wrong-routesignal_live_demo-04
- Campaign: `routesignal_live_demo`
- Family: `buyer_says_agent_is_wrong`
- Mechanical flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'this sounds automated']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-hostile-challenging-buyer-routesignal_live_demo-03
- Campaign: `routesignal_live_demo`
- Family: `hostile_challenging_buyer`
- Mechanical flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'this is pointless']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-hostile-challenging-buyer-routesignal_live_demo-04
- Campaign: `routesignal_live_demo`
- Family: `hostile_challenging_buyer`
- Mechanical flags: `hostile_response_not_deescalated, repeated_full_menu`
- Buyer script: `['__agent_open__', 'prove this is useful']`
- Final response: This is about inbound demo follow-up: one person should be responsible for the next reply. That prevents missed follow-up. Which part is least clear today?

### adv-asr-near-miss-gap-phrases-synthetic-automotive-service-review-04
- Campaign: `synthetic-automotive-service-review`
- Family: `asr_near_miss_gap_phrases`
- Mechanical flags: `repeated_full_menu`
- Buyer script: `['__agent_open__', 'yeah', 'service timing is long', 'it wastes time']`
- Final response: If vehicle issue, repair timing, or warranty or estimate are actually relevant, a service advisor can do a short service advisor inspection review. If not, I can stop here; should I ask one quick fit question?

### adv-asr-near-miss-gap-phrases-synthetic-b2b-saas-operations-03
- Campaign: `synthetic-b2b-saas-operations`
- Family: `asr_near_miss_gap_phrases`
- Mechanical flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'integration thing is confusing']`
- Final response: Maybe integration, understood. Is that an active concern now, or just something you might want checked later?

### adv-asr-near-miss-gap-phrases-synthetic-membership-plan-review-03
- Campaign: `synthetic-membership-plan-review`
- Family: `asr_near_miss_gap_phrases`
- Mechanical flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'usage thing is unclear']`
- Final response: Maybe usage or value, understood. Is that an active concern now, or just something you might want checked later?

### adv-asr-near-miss-gap-phrases-synthetic-telecom-plan-review-03
- Campaign: `synthetic-telecom-plan-review`
- Family: `asr_near_miss_gap_phrases`
- Mechanical flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'yeah', 'contact switching is confusing']`
- Final response: Maybe contract or switching, understood. Is that an active concern now, or just something you might want checked later?

### adv-asr-near-miss-invented-transcript-stress-routesignal_live_demo-01
- Campaign: `routesignal_live_demo`
- Family: `asr_near_miss_invented_transcript_stress`
- Mechanical flags: `asr_near_miss_not_clarified`
- Buyer script: `['__agent_open__', 'what should I care']`
- Final response: Fair question. Only if inbound demo follow-up slipping is costing time, creating delays, or hurting follow-up quality. If that is happening, a short review can confirm whether it is worth fixing. Is that showing up now?

