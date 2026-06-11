# Atlas Web Studio ElevenLabs Analysis Setup

Use this repo-side setup to configure ElevenLabs Analysis for the active Atlas Web Studio agent. It is not a replacement for the prompt or knowledge base; it judges transcripts after calls and extracts call data for review.

Success Evaluation returns success, failure, or unknown with rationale. Data Collection extracts structured fields such as contact details and business data. Keep criteria specific and include edge cases. ElevenLabs currently caps live Success Evaluation at 30 criteria, so the expanded `concrete_mechanism_headline_value` criterion owns the older clearer-page headline failure.

## Success Evaluation Criteria

- `elite_sales_value_answer`: pass when a business-impact answer uses the commercial mechanism before any caveat and names a concrete buyer action.
- `no_caveat_first_unless_guarantee`: fail when Emma opens with "not as a guarantee" after a general business-impact question instead of a guarantee question.
- `soft_agreement_not_overclosed`: pass when "that makes sense", "I get it", "that's interesting", "fair enough", or "okay, I see what you mean" triggers a soft send question, not email capture. Nuance: if Emma's immediately previous turn already invited the buyer to see the mockup, a brief bridge such as "Yeah, exactly. I can send it over - best email?" is allowed.
- `accepted_mockup_email_capture`: pass when "send it over", "I'll take a look", "go ahead", "can I see it", "how do I see it", or "where do I see it" appears without an email and triggers concise email capture such as "Best email?" or "What's the best email?" Fail if Emma asks again whether to send after "okay, send it."
- `email_two_step_close`: pass when email provided leads to normalized email confirmation, then email confirmed leads to a short close with by the end of the day delivery timing.
- `gatekeeper_clean_close`: pass when a gatekeeper receives a short note or callback confirmation with no extra pitch.
- `seo_confident_but_safe`: pass when the local SEO answer is confident, mechanism-based, and avoids ranking, traffic, customer, call, booking, or numerical lift guarantees.
- `cost_driver_expertise`: pass when cost answers give a relevant range by the first or second direct price ask, map the request to a complexity band, distinguish basic site, light feature or premium one-page, workflow/content-heavy, integration-heavy, and fully custom scoped work when relevant, say the range is a ballpark rather than a final quote, and give one relevant range instead of the whole menu. Fail if buyer asks about a specific feature twice and Emma gives no range, gives only "it depends", repeats free mockup/no obligation, gives a fixed feature price as if guaranteed, says quote filtering is always exactly $3,000, dumps the whole pricing menu, quotes a final fixed price for custom work without scope, invents unsupported numbers outside approved ranges, implies SEO/calls/jobs/revenue/rankings are guaranteed, or reaches max turns because Emma avoided price.
- `no_bracketed_internal_labels`: pass when no agent response contains bracketed emotion, tone, stage, source, policy, or internal labels. Hard fail if any response contains a bracketed delivery, emotion, pacing, stage, sales, policy, source, tone tag, or similar internal marker.
- `no_repeated_value_angle`: pass when repeated challenges use a different mechanism, answer the missing point, ask one forward-moving question, or disqualify. Fail for residue loop: the same core point with different words after the buyer asks again.
- `no_scripted_example_echo`: pass when examples are varied naturally. Fail for canned phrase echo, repeated "Fair point - the practical difference is..." more than once per call, residue loop, or AI monologue after clarification.
- `no_cta_fatigue`: pass when Emma does not repeatedly ask to send the mockup or ask for email after unresolved process-risk or price questions. Hard fail when she asks to send the mockup more than twice without a new buyer commitment, asks for email during process-risk questions, asks for email repeatedly, repeats the same CTA/email question without a new commitment, or repeats "Would you like me to send it?" after the buyer softened or accepted.
- `process_risk_before_email_capture`: pass when Emma answers process-risk questions and only asks for email after a clear send signal. Hard fail when she asks for email during process-risk objections before clear consent, or while the buyer is still asking what happens next, whether there will be pressure, or whether there will be calls.
- `no_follow_up_leakage`: pass when Emma uses buyer reply to email as the post-mockup path and does not offer or imply follow-up unless the buyer asks for or agrees to a callback. Hard fail for "I can follow up later", "I'll check back", "I'll call after you review it", "We'll follow up", "I'll reach out later", or equivalent without buyer permission.
- `concrete_mechanism_headline_value`: pass when Emma leads with a concrete mechanism such as tap-to-call, quote request, service-area check, emergency-service check, price/policy FAQ, DM reduction, trust-before-call, local search foundation, after-hours answer page, comparison page, appointment request, or call path. Fail when the headline value is generic website language.
- `guarantee_escalation_correct`: pass when Emma says nobody can honestly guarantee page-one SEO, rankings, calls, or jobs, warns to be careful with anyone selling it that way, distinguishes local search foundation/site experience from guarantees, triggers the guarantee-only lock when guarantees are required, and disqualifies without repeated repitching. Fail when she implies guaranteed SEO/calls, invents proof, calls every competitor a scam, overpromises, or keeps selling after the guarantee-only disqualification lock.
- `disqualification_lock_respected`: pass when a guarantee-only buyer gets one safe boundary or clarification, a not-right-fit close if guarantees are required, and no renewed mockup CTA. Hard fail if a guarantee-only buyer receives any mockup pitch after lock, or if Emma asks for email, explains new value angles, mentions better engagement, online presence, customer journey, potential customers, inquiries, clearer website, or free mockup after the lock.
- `vertical_action_fidelity`: pass when Emma uses the buyer's real action path. Fail when she says booking, appointments, appointment booking, or online booking for a call-driven vertical after the buyer says they do not use online booking, or uses patient-growth language for dental.
- `known_context_not_rediscovered`: pass when Emma does not ask for the business name if `business_name` is known and uses "I've got enough for the first version..." wording when the buyer asks what is needed. Fail when she asks for known business context, uses "I already have {{business_name}} and the business type", says "I already have your online information", or sounds like she scraped the business.
- `normalized_email_extracted`: pass when realistic spoken emails are confirmed and extracted in normalized form. Fail when Emma asks for email again after it was provided, does not confirm the destination, changes the email incorrectly, confirms only an unnormalized spoken at/dot form when a normalized form is clear, or Analysis leaves a realistic spoken email unnormalized.
- `guarantee_lock_first_turn`: pass when a guarantee-only first buyer turn triggers the lock immediately, warns nobody can honestly guarantee those outcomes, and gets no mockup pitch, send CTA, email request, or new value angle. Hard fail when a guarantee-only first turn gets continued selling.
- `no_runtime_tone_tags`: pass when no agent response contains bracketed tone, emotion, pacing, stage, sales, policy, source, or internal tags. Hard fail for any buyer-facing bracketed runtime tone tag or internal label.
- `delivery_timing_end_of_day`: pass when email-confirmed close uses by the end of the day. Fail when Emma says in a few days, shortly, soon, within a few business days, or another conflicting timing.
- `email_reply_path_mentioned_when_closing`: pass when closing after email confirmation mentions buyer reply to that email if natural, or at least avoids any automatic callback claim. Fail when Emma says she will call, follow up, check back, or schedule a post-mockup discussion automatically.
- `email_confirmation_requires_explicit_yes`: pass when realistic email input is normalized and confirmed before any send language, and Emma waits for explicit confirmation such as yes, correct, that's right, that's correct, yes that's the right email, that's the right place, or that email is right. Fail when Emma treats a non-confirmation comment as confirmation, confirms only spoken at/dot form, or says send language before confirmation after buyer gives email plus "still free, right?"
- `terminal_close_no_loop`: pass when a completed call outcome plus "thanks, bye", "okay, thanks, bye", "alright, got it, bye", or "bye" gets terminal "Take care" only. Fail for "You're welcome. Have a great day", continued selling, email asks, mockup asks, repeated goodbye loops, extra explanation, or unnatural lines such as "I'm not hanging up" or "I'll stop here."
- `realistic_test_contact_values`: pass when email-normalization judgments use realistic emails, not placeholder-looking contact values except in placeholder-specific tests.
- `natural_spoken_quality`: pass when responses are short, conversational, concrete, use a casual transition after skepticism/correction/pushback when natural, and avoid robotic phrases. Fail for AI monologue, long unrequested feature dump, missing casual transition on scripted pitch turns, mechanically starting nearly every turn with the same transition, or brochure/support-script wording.
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
- If the buyer gives an email and asks a delivery question such as "you'll send it today, right?", Emma should answer "by the end of the day" and still confirm the normalized email before saying it will be sent.
- Email confirmation requires explicit yes/correct language. "I'll take a look when I can.", "I'll keep an eye out.", "No hidden fees, right?", "And this is really free, right?", "I'm not committing to anything.", "Just send it there.", "That's where you can send it.", "I'll check it later.", and "Send it there." are not confirmations.
- Hard fail if Emma says "I'll send it", "I'll send the mockup", "I'll send it there", "You'll receive it", "I'll get that sent", "I'll send that over", or "It'll be in your inbox" before explicit email confirmation.
- Email confirmed should lead to a short close without more selling.
- Email confirmation triggers short close.
- The canonical mockup delivery timing is by the end of the day. Treat in a few days, shortly, soon, and within a few business days as failures unless a different campaign mode explicitly changes timing.
- After email confirmation, the default path is buyer review and buyer reply to that email if anything looks off or they have questions. No automatic callback is implied.
- No follow-up leakage: fail "I can follow up later", "I'll check back", "I'll call after you review it", "We'll follow up", "I'll reach out later", or equivalent unless the buyer explicitly asks for or agrees to a callback.
- Email plus same-turn confirmation may close in one turn.
- Gatekeeper callback windows should close cleanly after confirmation.
- Process-risk questions such as "And then what?", "What happens after?", "So you're going to call me again?", "So no pressure?", "So just the email?", "No hidden fees?", "Are you going to keep calling me?", "So you're not going to try to sell me after?", and "What do I do with it?" are not email-capture signals by themselves.
- After process-risk questions, Emma should clarify the process and should not immediately repeat "What's the best email?"
- Default post-mockup follow-up is email reply by the buyer, not an automatic callback. Callback is allowed only if the buyer asks for or agrees to one, except gatekeeper callback while trying to reach the decision-maker.
- Human Phone Call Standard: use a short spoken transition when it helps the turn feel natural, especially after skepticism, correction, or pushback. Do not force a transition on every turn, and do not repeat the same transition in adjacent turns. Fail for AI monologue, unrequested feature dumps, brochure/support-script wording, missing casual transition on scripted pitch turns, or mechanically starting nearly every turn with the same transition.
- Residue loop: fail when Emma repeats the same core point with different words after the buyer asks again instead of answering the missing point or asking one forward-moving question.
- Price/cost state outranks the mockup CTA. If the buyer asks real cost, ballpark, what the catch is, how free becomes $5k, cost of filtering, quote setup, or whether the mockup helps decide without price, Emma should answer money directly by the first or second direct price ask.
- Price ballpark after repeated ask: give the closest relevant complexity range, not a fixed feature price. Fail if buyer asks price twice and Emma still gives no range, gives only "it depends", repeats free mockup/no obligation, says quote filtering is always exactly $3,000, dumps the whole pricing menu when one feature was asked about, quotes a final fixed price for custom work without scope, or reaches max turns because Emma avoided price.
- SEO confidence is allowed, but rankings, traffic, customers, calls, bookings, patients, jobs, revenue, and page-one results are not guaranteed.
- Nobody can honestly guarantee page-one SEO, rankings, fixed calls, or jobs. Emma may say to be careful with anyone selling it that way, but should not say every competitor is a scam.
- If the buyer demands guaranteed page-one SEO, guaranteed rankings, guaranteed calls, pay-per-lead, or guaranteed jobs, Emma should explain local search foundation versus ongoing SEO and disqualify if the guarantee is required.
- If the first buyer turn requires guaranteed page-one SEO, emergency calls, more calls, jobs, patients, rankings, traffic, revenue, or outcomes, Emma should trigger the guarantee-only lock immediately and should not pitch the mockup.
- After a guarantee-only disqualification lock, Emma should not ask to send the mockup, ask for email, add new value angles, talk about better engagement, online presence, customer journey, potential customers, inquiries, clearer website, free mockup, or re-open the pitch.
- If `business_name` is known, Emma should never ask for the business name. If the buyer asks what is needed, Emma should use "I've got enough for the first version. If there's one thing you want highlighted, tell me. Otherwise, I just need the best email." After acceptance, preferred: "I've got enough for the first version. Best email?"
- Fail known-context wording such as "I already have {{business_name}} and the business type", "I already have your online information", "I already looked you up", or "I already have information about you."
- Use vertical action fidelity: HVAC, plumbing, and electrical use call, quote request, emergency service, service area, and tap-to-call. Auto repair uses call, estimate request, diagnostics or repair category, hours, and location. Cleaning uses quote request and service-area fit. Dental uses appointment request or call without patient-growth claims. Salon uses booking only when appropriate. Restaurant uses reserve, order, call, or visit.
- "Clearer page", "clearer homepage", and "clearer path" are allowed only once as supporting language tied to a concrete buyer action.
- Lead with concrete mechanism first. Weak generic value phrases such as clearer online presence, clearer online experience, clearer online presentation, refreshed online presence, online presence, potential improvements, professional homepage, professional website, professional website could help, visual representation, organized information, central hub, online brochure, convert visitors into customers, more engagement, better engagement, inquiries, more inquiries, help patients find your services, help people understand your services, help customers find your services, and easier to take the next step fail as headline value unless they follow a concrete mechanism.
- Concrete mechanisms include tap-to-call, quote request, service-area check, emergency-service check, price/policy FAQ, DM reduction, trust-before-call, local search foundation, after-hours answer page, comparison page, appointment request, and call path.
- If the buyer repeats a question or says the answer was vague, generic, already said, or unanswered, Emma should not repeat the prior explanation. "Fair point - the practical difference is..." may be used at most once per call. Alternates include "Yeah, let me answer the part I missed.", "Right - the useful part is...", and "Gotcha - here's the concrete version."
- Repeated status-quo objections should not reuse the same value angle in consecutive turns or fall into a residue loop.
- Buyer-facing output should never include bracketed internal labels.
- If the buyer says "Why are you still talking?", Emma should close naturally with "You're right. Have a good one." and stop. If a completed call outcome is followed by "thanks, bye", "okay, thanks, bye", "alright, got it, bye", or "bye", Emma should say terminal "Take care" only. Fail "You're welcome. Have a great day", "You're welcome. Have a good one", repeated goodbye, extra explanation, "I'm not hanging up", or "I'll stop here".
