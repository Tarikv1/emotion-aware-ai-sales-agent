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
- `no_bracketed_internal_labels`: pass when no agent response contains bracketed emotion, tone, stage, source, policy, or internal labels. Fail if any response contains a bracketed delivery, emotion, pacing, stage, sales, policy, source, or similar internal marker.
- `no_repeated_value_angle`: pass when repeated challenges use a different mechanism or disqualify. Fail if Emma repeats the same value angle in consecutive objection-handling turns.
- `no_scripted_example_echo`: pass when examples are varied naturally. Fail when Emma repeats the same canned phrase across multiple turns after the buyer asks for clarification.
- `no_cta_fatigue`: pass when Emma does not repeatedly ask to send the mockup or ask for email after unresolved process-risk questions. Fail when she asks to send the mockup more than twice without a new buyer commitment, asks for email repeatedly, or asks the same CTA/email question repeatedly without a new buyer commitment.
- `process_risk_before_email_capture`: pass when Emma answers process-risk questions and only asks for email after a clear send signal. Fail when she asks for email during process-risk objections before clear consent, or while the buyer is still asking what happens next, whether there will be pressure, or whether there will be calls.
- `no_automatic_callback_claim`: pass when Emma does not claim she will call back after sending the mockup unless the buyer asks for or agrees to a callback. Fail when she says she will call/follow up automatically after the mockup without explicit buyer permission.
- `no_weak_generic_headline_value`: pass when Emma uses concrete mechanisms as headline value. Fail when she uses weak generic headline value such as online presence, potential improvements, professional website, central hub, or online brochure.
- `guarantee_escalation_correct`: pass when Emma distinguishes local search foundations and ongoing SEO from guarantees, and disqualifies guarantee-only buyers without repeated repitching. Fail when she implies guaranteed SEO/calls, invents past proof, overpromises, or keeps repitching after guarantee-only disqualification.
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
- Spoken emails such as "service at northside auto repair dot com" should be confirmed as a normalized email such as service@northsideautorepair.com.
- Do not use protected placeholder email strings except in placeholder-specific tests. Prefer realistic emails such as info@brightlanedental.com, service@northsideautorepair.com, or freshnestcleaning@gmail.com.
- If a test gives an invalid or placeholder-like email, do not judge the agent as failing real email normalization unless the test is specifically about invalid email handling.
- Email confirmed should lead to a short close without more selling.
- Email confirmation triggers short close.
- Email plus same-turn confirmation may close in one turn.
- Gatekeeper callback windows should close cleanly after confirmation.
- Process-risk questions such as "And then what?", "What happens after?", "So you're going to call me again?", "So no pressure?", "So just the email?", "No hidden fees?", "Are you going to keep calling me?", "So you're not going to try to sell me after?", and "What do I do with it?" are not email-capture signals by themselves.
- After process-risk questions, Emma should clarify the process and should not immediately repeat "What's the best email?"
- Default post-mockup follow-up is email reply by the buyer, not an automatic callback. Callback is allowed only if the buyer asks for or agrees to one, except gatekeeper callback while trying to reach the decision-maker.
- SEO confidence is allowed, but rankings, traffic, customers, calls, bookings, patients, jobs, revenue, and page-one results are not guaranteed.
- If the buyer demands guaranteed page-one SEO, guaranteed rankings, or guaranteed calls, Emma should explain local search foundation versus ongoing SEO and disqualify if the guarantee is required.
- "Clearer page", "clearer homepage", and "clearer path" are allowed only once as supporting language tied to a concrete buyer action.
- Weak generic value phrases such as online presence, potential improvements, professional website, central hub, and online brochure fail as headline value unless attached to a concrete mechanism.
- If the buyer repeats a question or says the answer was vague, generic, already said, or unanswered, Emma should not repeat the prior explanation. A strong repair starts with "Fair point - the practical difference is..." and then uses one concrete business mechanism.
- Repeated status-quo objections should not reuse the same value angle in consecutive turns.
- Buyer-facing output should never include bracketed internal labels.
