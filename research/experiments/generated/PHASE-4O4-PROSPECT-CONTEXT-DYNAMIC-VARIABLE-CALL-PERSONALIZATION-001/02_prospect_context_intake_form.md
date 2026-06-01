# Prospect Context Intake Form

Use this form before an outbound Atlas call. It is a lead-context record, not a scraping instruction.

## Required Context

- prospect_id:
- business_name:
- business_type:
- vertical:
- city:
- service_area:
- known_website_url:
- known_website_status:
- known_social_presence:
- known_booking_or_ordering_path:
- known_phone_or_contact_path:
- suspected_gap:
- primary_offer_angle:
- likely_decision_maker_role:
- contact_name_if_known:
- call_reason:
- proof_or_observation_source:
- data_confidence:
- inspected_website:
- do_not_claim_as_fact_fields:
- allowed_personalization_fields:
- forbidden_personalization_claims:
- followup_preference_if_known:
- notes:

## Use Rules

If `business_name` is available, Emma must not ask "what is your business name?"

If `vertical` or `business_type` is available, Emma must not ask "what kind of business do you have?"

If confidence is low or medium, Emma should say "I had you down as..." or "I may be wrong, but..."

If the buyer corrects context, accept the correction and continue.

Do not invent missing lead details. Ask a concise question only when the detail is needed for the mockup.
