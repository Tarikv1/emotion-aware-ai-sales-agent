# Atlas Web Studio ElevenLabs Analysis Setup

Use this repo-side setup to configure ElevenLabs Analysis for the active Atlas Web Studio agent. It is not a replacement for the prompt or knowledge base; it judges transcripts after calls and extracts call data for review.

Success Evaluation returns success, failure, or unknown with rationale. Data Collection extracts structured fields such as contact details and business data. Keep criteria specific and include edge cases.

## Success Evaluation Criteria

- `elite_sales_value_answer`: pass when a business-impact answer uses the commercial mechanism before any caveat and names a concrete buyer action.
- `no_caveat_first_unless_guarantee`: fail when Emma opens with "not as a guarantee" after a general business-impact question instead of a guarantee question.
- `soft_agreement_not_overclosed`: pass when "that makes sense", "I get it", "that's interesting", "fair enough", or "okay, I see what you mean" triggers a soft send question, not email capture.
- `accepted_mockup_email_capture`: pass when "send it over", "I'll take a look", "go ahead", "can I see it", "how do I see it", or "where do I see it" appears without an email and triggers concise email capture.
- `email_two_step_close`: pass when email provided leads to normalized email confirmation, then email confirmed leads to a short close.
- `gatekeeper_clean_close`: pass when a gatekeeper receives a short note or callback confirmation with no extra pitch.
- `no_weak_clearer_main_value`: fail when clearer page/homepage/path is the main value instead of supporting language tied to a concrete action.
- `seo_confident_but_safe`: pass when the local SEO answer is confident, mechanism-based, and avoids ranking, traffic, customer, call, booking, or numerical lift guarantees.
- `cost_driver_expertise`: pass when cost answers explain real project complexity, including simple-site scope versus custom copy, pages, service-area pages, workflows, integrations, ecommerce, migration, SEO/content work, or custom design.
- `natural_spoken_quality`: pass when responses are short, conversational, concrete, and avoid robotic phrases.
- `stop_request_respected`: pass when a stop or do-not-call request ends the sales motion immediately.
- `no_fake_claims`: fail for invented proof, guaranteed results, fake urgency, invented contact details, or claims that an email was found or sent when it was not.

Use `unknown` when the transcript does not contain the buyer move needed to judge a criterion. For example, `email_two_step_close` is unknown when the buyer never gives an email, and it is not a failure if the transcript ends immediately after email before Emma receives another turn.

## Data Collection Fields

- `buyer_role`
- `contact_name`
- `email`
- `callback_window`
- `business_name`
- `vertical`
- `buyer_state`
- `objection_type`
- `value_angle_used`
- `accepted_mockup`
- `soft_agreement_only`
- `send_signal`
- `terminal_outcome`
- `failure_reason`
- `next_step`

Normalize obvious email spell-outs in `email`. Use `null` for missing strings and `false` for booleans unless the transcript clearly supports `true`.

## Review Edge Cases

- Soft agreement alone is not accepted mockup.
- Accepted mockup without email should lead to email capture.
- Accepted mockup without email triggers email capture.
- Email provided should lead to normalized email confirmation, not another request for the best email.
- Email provided triggers normalized email confirmation.
- Email confirmed should lead to a short close without more selling.
- Email confirmation triggers short close.
- Email plus same-turn confirmation may close in one turn.
- Gatekeeper callback windows should close cleanly after confirmation.
- SEO confidence is allowed, but rankings, traffic, customers, calls, bookings, patients, jobs, revenue, and page-one results are not guaranteed.
- "Clearer page", "clearer homepage", and "clearer path" are allowed only once as supporting language tied to a concrete buyer action.
