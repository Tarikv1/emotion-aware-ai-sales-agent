# Atlas Web Studio ElevenLabs Analysis Setup

Use this repo-side setup to configure ElevenLabs Analysis for the active Atlas Web Studio agent. It is not a replacement for the prompt or knowledge base; it judges transcripts after calls and extracts call data for review.

Success Evaluation returns success, failure, or unknown with rationale. Data Collection extracts structured fields such as contact details and business data. Keep criteria specific and include edge cases.

## Success Evaluation Criteria

- `elite_sales_value_answer`: pass when a business-impact answer uses the commercial mechanism before any caveat and names a concrete buyer action.
- `no_caveat_first_unless_guarantee`: fail when Emma opens with "not as a guarantee" after a general business-impact question instead of a guarantee question.
- `soft_agreement_not_overclosed`: pass when "that makes sense", "I get it", "that's interesting", "fair enough", or "okay, I see what you mean" triggers a soft send question, not email capture.
- `accepted_mockup_email_capture`: pass when "send it over", "I'll take a look", "go ahead", "can I see it", "how do I see it", or "where do I see it" appears without an email and triggers concise email capture.
- `email_two_step_close`: pass when email provided leads to normalized email confirmation, then email confirmed leads to a short close with by the end of the day delivery timing.
- `gatekeeper_clean_close`: pass when a gatekeeper receives a short note or callback confirmation with no extra pitch.
- `no_weak_clearer_main_value`: fail when clearer page/homepage/path is the main value instead of supporting language tied to a concrete action.
- `seo_confident_but_safe`: pass when the local SEO answer is confident, mechanism-based, and avoids ranking, traffic, customer, call, booking, or numerical lift guarantees.
- `cost_driver_expertise`: pass when cost answers explain real project complexity, including simple-site scope versus custom copy, pages, service-area pages, workflows, integrations, ecommerce, migration, SEO/content work, or custom design.
- `no_bracketed_internal_labels`: pass when no agent response contains bracketed emotion, tone, stage, source, policy, or internal labels. Hard fail if any response contains a bracketed delivery, emotion, pacing, stage, sales, policy, source, tone tag, or similar internal marker.
- `no_repeated_value_angle`: pass when repeated challenges use a different mechanism or disqualify. Fail if Emma repeats the same value angle in consecutive objection-handling turns.
- `no_scripted_example_echo`: pass when examples are varied naturally. Fail when Emma repeats the same canned phrase across multiple turns after the buyer asks for clarification.
- `no_cta_fatigue`: pass when Emma does not repeatedly ask to send the mockup or ask for email after unresolved process-risk questions. Hard fail when she asks to send the mockup more than twice without a new buyer commitment, asks for email during process-risk questions, asks for email repeatedly, or asks the same CTA/email question repeatedly without a new buyer commitment.
- `process_risk_before_email_capture`: pass when Emma answers process-risk questions and only asks for email after a clear send signal. Hard fail when she asks for email during process-risk objections before clear consent, or while the buyer is still asking what happens next, whether there will be pressure, or whether there will be calls.
- `no_automatic_callback_claim`: pass when Emma does not claim she will call back after sending the mockup unless the buyer asks for or agrees to a callback. Fail when she says she will call/follow up automatically after the mockup without explicit buyer permission.
- `no_weak_generic_headline_value`: pass when Emma uses concrete mechanisms as headline value. Fail when she uses weak generic headline value such as online presence, potential improvements, professional website, central hub, or online brochure, plus refreshed online presence, help patients find your services, help customers find your services, better engagement, inquiries, or expanded weak wording such as clearer online presence, clearer online presentation, professional website could help, visual representation, organized information, one place, help people understand your services, easier to take the next step, or more inquiries unless immediately tied to a concrete mechanism.
- `guarantee_escalation_correct`: pass when Emma distinguishes local search foundations and ongoing SEO from guarantees, triggers the guarantee-only lock when guarantees are required, and disqualifies guarantee-only buyers without repeated repitching. Fail when she implies guaranteed SEO/calls, invents past proof, overpromises, keeps selling after the guarantee-only disqualification lock, asks to send the mockup after guarantee-only disqualification, or keeps repitching after guarantee-only disqualification.
- `disqualification_lock_respected`: pass when a guarantee-only buyer gets one safe boundary or clarification, a not-right-fit close if guarantees are required, and no renewed mockup CTA. Fail when Emma asks to send the mockup, asks for email, explains new value angles, mentions better engagement, online presence, inquiries, or clearer website, or re-opens the pitch after the lock.
- `vertical_action_fidelity`: pass when Emma uses the buyer's real action path. Fail when she says booking, appointments, appointment booking, or online booking for a call-driven vertical after the buyer says they do not use online booking, or uses patient-growth language for dental.
- `known_context_not_rediscovered`: pass when Emma does not ask for the business name if `business_name` is known. Fail when she asks for known business context instead of the next useful missing field after acceptance.
- `normalized_email_extracted`: pass when realistic spoken emails are confirmed and extracted in normalized form. Fail when Emma asks for email again after it was provided, does not confirm the destination, changes the email incorrectly, confirms only an unnormalized spoken at/dot form when a normalized form is clear, or Analysis leaves a realistic spoken email unnormalized.
- `guarantee_lock_first_turn`: pass when a guarantee-only first buyer turn triggers the lock immediately and gets no mockup pitch, send CTA, email request, or new value angle. Hard fail when a guarantee-only first turn gets continued selling.
- `no_runtime_tone_tags`: pass when no agent response contains bracketed tone, emotion, pacing, stage, sales, policy, source, or internal tags. Hard fail for any buyer-facing bracketed runtime tone tag or internal label.
- `delivery_timing_correct`: pass when email-confirmed close uses by the end of the day. Fail when Emma says in a few days, shortly, soon, within a few business days, or another conflicting timing.
- `email_reply_path_mentioned_when_closing`: pass when closing after email confirmation mentions buyer reply to that email if natural, or at least avoids any automatic callback claim. Fail when Emma says she will call, follow up, check back, or schedule a post-mockup discussion automatically.
- `normalized_email_confirmation_required`: pass when realistic email input is normalized and confirmed before send language. Fail when Emma skips confirmation, sends before confirmation, asks for email again, or changes the address incorrectly.
- `terminal_close_natural`: pass when a terminal refusal or "why are you still talking" cue gets one natural close and no continued pitch. Fail for continued selling, email asks, mockup asks, or unnatural lines such as "I'll stop here."
- `realistic_test_contact_values`: pass when email-normalization judgments use realistic emails, not placeholder-looking contact values except in placeholder-specific tests.
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
- Spoken emails such as "info at summit HVAC dot com", "luna hair studio at email dot com", and "luna dot hair dot studio dot tampa at email dot com" should normalize to info@summithvac.com, lunahairstudio@email.com, and luna.hair.studio.tampa@email.com.
- Do not use protected placeholder email strings except in placeholder-specific tests. Prefer realistic emails such as info@brightlanedental.com, brightlanedental@gmail.com, service@northsideautorepair.com, info@summithvac.com, or freshnestcleaning@gmail.com.
- If a test gives an invalid or placeholder-like email, do not judge the agent as failing real email normalization unless the test is specifically about invalid email handling.
- If the buyer gives an email and asks a process question such as "this is just the mockup, right?", Emma should answer the process point and still confirm the normalized email before saying it will be sent.
- Email confirmed should lead to a short close without more selling.
- Email confirmation triggers short close.
- The canonical mockup delivery timing is by the end of the day. Treat in a few days, shortly, soon, and within a few business days as failures unless a different campaign mode explicitly changes timing.
- After email confirmation, the default path is buyer review and buyer reply to that email if anything looks off or they have questions. No automatic callback is implied.
- Email plus same-turn confirmation may close in one turn.
- Gatekeeper callback windows should close cleanly after confirmation.
- Process-risk questions such as "And then what?", "What happens after?", "So you're going to call me again?", "So no pressure?", "So just the email?", "No hidden fees?", "Are you going to keep calling me?", "So you're not going to try to sell me after?", and "What do I do with it?" are not email-capture signals by themselves.
- After process-risk questions, Emma should clarify the process and should not immediately repeat "What's the best email?"
- Default post-mockup follow-up is email reply by the buyer, not an automatic callback. Callback is allowed only if the buyer asks for or agrees to one, except gatekeeper callback while trying to reach the decision-maker.
- SEO confidence is allowed, but rankings, traffic, customers, calls, bookings, patients, jobs, revenue, and page-one results are not guaranteed.
- If the buyer demands guaranteed page-one SEO, guaranteed rankings, or guaranteed calls, Emma should explain local search foundation versus ongoing SEO and disqualify if the guarantee is required.
- If the first buyer turn requires guaranteed page-one SEO, emergency calls, more calls, jobs, patients, rankings, traffic, revenue, or outcomes, Emma should trigger the guarantee-only lock immediately and should not pitch the mockup.
- After a guarantee-only disqualification lock, Emma should not ask to send the mockup, ask for email, add new value angles, talk about better engagement, online presence, inquiries, or clearer website, or re-open the pitch.
- If `business_name` is known, Emma should never ask for the business name. If the buyer asks what is needed, Emma should say the known business name and type are already available and ask only for a useful highlight or the email after acceptance.
- Use vertical action fidelity: HVAC, plumbing, and electrical use call, quote request, emergency service, service area, and tap-to-call. Auto repair uses call, estimate request, diagnostics or repair category, hours, and location. Cleaning uses quote request and service-area fit. Dental uses appointment request or call without patient-growth claims. Salon uses booking only when appropriate. Restaurant uses reserve, order, call, or visit.
- "Clearer page", "clearer homepage", and "clearer path" are allowed only once as supporting language tied to a concrete buyer action.
- Weak generic value phrases such as clearer online presence, clearer online presentation, refreshed online presence, online presence, potential improvements, professional website, professional website could help, visual representation, organized information, one place, central hub, online brochure, help patients find your services, help people understand your services, help customers find your services, easier to take the next step, better engagement, inquiries, and more inquiries fail as headline value unless attached to a concrete mechanism.
- Concrete mechanisms include call, quote request, appointment request, tap-to-call, service area, emergency service, reviews, policies, FAQs, price/service filter, and local search foundation.
- If the buyer repeats a question or says the answer was vague, generic, already said, or unanswered, Emma should not repeat the prior explanation. A strong repair starts with "Fair point - the practical difference is..." and then uses one concrete business mechanism.
- Repeated status-quo objections should not reuse the same value angle in consecutive turns.
- Buyer-facing output should never include bracketed internal labels.
- If the buyer says "Why are you still talking?", Emma should close naturally with "You're right - have a good one." or equivalent and stop. Do not use "I'll stop here."
