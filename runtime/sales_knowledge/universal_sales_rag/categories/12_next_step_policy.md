# Next Step Policy

Layer: Universal Sales RAG

Category ID: `next_step_policy`

Owns: reusable selection of the next safe step: identify role, answer, ask one question, send information, schedule callback, book meeting, route to human, disqualify, or stop.

Does Not Own: campaign-specific close, booking mechanism, calendar authority, contact collection rules, or side-effect permissions.

Retrieval Triggers: "what next", "send it", "call later", "book a time", "email me", "who should I talk to", "stop", "not interested".

Operating Rules: choose the smallest step that matches buyer readiness. Do not ask for a meeting when a send path is enough. The durable rule is: do not repeat the same review or demo ask while the buyer is still challenging value. Do not send or schedule unless the campaign allows it. After a terminal next step is accepted and clarified, close naturally and stop. Conversation control means answer, bridge, and guide: answer the direct concern, bridge to one supported reason or proof step, then guide to the smallest valid next step. Use calibrated next-step control; ask less when the buyer is busy, ask directly when the buyer has softened, and stop when the buyer refuses. Use name capture only when it is natural, useful, and not interrupting a direct objection, gatekeeper boundary, or terminal close.

Accepted send without contact is not terminal: when the buyer agrees to receive information, the next step is not complete until the destination is known and allowed by the campaign. Ask for the smallest missing contact path. Do not close the call after "send it over" if no email, phone, meeting link, or approved destination exists.

Send Timing Confirmation: after the buyer gives a clear contact path, confirm the exact destination before closing. If the buyer asks whether the send is happening now, already happened, or is about to happen, answer that timing directly first. Prefer present-action wording such as "I'm sending it now to [email]" when the campaign permits immediate sending. Do not answer a timing question with only "I will send it" because that can sound delayed and create another clarification loop.

Repeated delivery-timing repair: if the buyer says the timing was not answered, repair the miss with only the timing and no repeated pitch. A concise apology or correction is enough. Do not repeat the full destination, reply-path, contact-info, and goodbye sentence again unless one of those details is actually unclear.

Busy two-option compression: when a buyer offers more than one acceptable low-friction path, such as email plus callback, do not restate all options. Ask for the choice once, then execute the chosen path. If the buyer chooses both and the campaign allows both, confirm both in one short sentence and stop.

Failure Modes: stacking multiple asks, continuing after terminal acceptance, asking another question after a clear close, or taking side effects without approval.

Campaign Overlay Handoff: campaign overlay defines valid next steps, required wording, side-effect boundaries, and terminal-close behavior.
