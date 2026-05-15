# English Review Import

`PROD-053D` imports Tarik's `PROD-053C` English review export and turns it into a decision summary plus rework plan.

It does not change runtime behavior or response text.

## Summary

- Import items: `29`
- Approved statuses: `16`
- Needs rework statuses: `13`
- Pending statuses: `0`
- Approved as-written: `15`
- Approved with edit note: `1`
- Runtime patch candidates: `14`
- Runtime behavior changed: `false`
- Response text behavior changed: `false`

## Key Corrections

- Do not speak to voicemail; log follow-up and retry later.
- Prefer contractions and less formal acknowledgement words where safe.
- Keep support, cancellation, and callback routes shorter.
- Treat coverage facts from an approved policy document differently from advice.
- Use context-sensitive autonomy wording around `no rush`.

## Patch Candidates

### prod-053c-voicemail - voicemail

- Candidate type: `action_only_no_spoken_response`
- Owner note: if we reach a voicemail the agent should log this for another time and try again. The agent doesn't need to say anything to the voicemail
- Candidate: Do not speak to voicemail. Log follow-up and try again later according to campaign rules.
- Requires design decision: `true`
- Context sensitive: `false`

### prod-053c-identity-repair - identity-repair

- Candidate type: `wording`
- Owner note: Instead of that response the agent should say something like: This is Maya(or whatever the agent's name is) from RouteSignal(or whatever the company is). And briefly explain the reason for the call and whatnot
- Candidate: This is Maya from RouteSignal. I'm calling because we're checking whether missed callbacks and follow-up work are still an issue.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-support-route - support-route

- Candidate type: `wording`
- Owner note: this is a bit of a long response to an issue which does not need that much explanation. Maybe just say like: of course I'll send this to support right away. And then maybe wish them good or something
- Candidate: Of course. I'll send this to support right away. Have a good day.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-cancellation-route - cancellation-route

- Candidate type: `wording`
- Owner note: we talked about this for the voice work but we should use I'll instead of I will. And again there are too many words that are unnecessary. The agent could just say: Sure, I'll stop and connect you to the cancellation team.
- Candidate: Sure, I'll stop and connect you to the cancellation team.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-security-review-route - security-review-route

- Candidate type: `wording`
- Owner note: agent is using words that are creating too much certainty so instead of 'I will' agent should use 'I should'
- Candidate: Security review needs verified material or a specialist. I should not make broad compliance claims here.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-coverage-boundary-route - coverage-boundary-route

- Candidate type: `design_decision`
- Owner note: if the agent has the policy document it should be able to tell the person what is covered and what is not this is not advice, it's just knowledge
- Candidate: If approved coverage facts exist, answer from the policy document. If not, send it to a qualified reviewer.
- Requires design decision: `true`
- Context sensitive: `true`

### prod-053c-healthcare-boundary-route - healthcare-boundary-route

- Candidate type: `wording`
- Owner note: Instead of saying I should not give health or medical advice, I can send this to a qualified reviewer. The agent should probably say, or it could probably be better if the agent say I cannot instead of I should not, because I should, if the agent says I should, that kind of states that the agent is capable, but it can't, or it should not because it's not legal or something like that. But instead of that, so these small words are important. So instead of I should, the agent says I cannot give any medical advice, but I can send you to a qualified specialist or qualified reviewer or someone. I can send you to someone, you know what I mean?
- Candidate: I can't give medical advice, but I can send you to someone qualified.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-claim-boundary - claim-boundary

- Candidate type: `wording`
- Owner note: All right, again, this is like we talked about this before, too. So instead of saying, I do not, the agent can say, I don't want to, or I can't. It's shorter versions. We should use the shorter versions of words instead of separating I do not, we should say, I don't. Also, instead of this response, the agent should say, I can't guarantee something that depends on the details, ......
- Candidate: I can't guarantee something that depends on the details. A specialist can check that.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-scheduling-confirmation - scheduling-confirmation

- Candidate type: `wording`
- Owner note: Confirmed sounds too formal and too, it kind of makes it obvious that the answer is AI or the speaker is AI because not a lot of people talk like that if you're not in the military or something like that. So instead of confirmed, the agent can say, all right, or sure, or something like that
- Candidate: All right. I'll note that time for the specialist callback. Goodbye.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-sale-ready-commitment - sale-ready-commitment

- Candidate type: `wording`
- Owner note: I told this in prod-053c-scheduling-confirmation 'confirmed' is too formal
- Candidate: All right. I'll mark that you want the next step. No payment is handled on this call.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-procurement-review - procurement-review

- Candidate type: `wording`
- Owner note: Understood is also too formal. So maybe something like 'sure, of course' so assurance words
- Candidate: Sure. I can keep this to written review information. Nothing firm today.
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-callback-request - callback-request

- Candidate type: `wording`
- Owner note: The customer is asking if we can call back, and we should answer as shortly as possible because if the customer is asking for us to call back, that means that you probably don't have time. So we should keep it short and say, of course, do you have a time in mind or something like that. Or, sure, I can set a call or I can set an appointment for this date if you want to, or you can tell me a date, or something like that
- Candidate: Of course. Do you have a time in mind?
- Requires design decision: `false`
- Context sensitive: `false`

### prod-053c-autonomy-check - autonomy-check

- Candidate type: `context_sensitive_wording`
- Owner note: This is one of those places where we can actually use the customer's last two words, two or three words, to our advantage. We can just start with, okay, no rush. Of course, there's no rush. We can keep this low pressure and only clarify what you need, or we can keep this low pressure and see what you think. Or we can say, I can explain what it is, and this is no commitment call, or something like that. This is one of those places where a bit of a lengthy answer could be all right. but it all depends on the context as well. So the previous context, if the agent already explained what everything is, the response to I need time to think should be a little shorter. If the agent didn't talk to the customer before about what is the product and whatnot, the response could be a little longer.
- Candidate: Okay, no rush. We can keep this low-pressure and only clarify what you need.
- Requires design decision: `false`
- Context sensitive: `true`

### prod-053c-existing-provider-gap - existing-provider-gap

- Candidate type: `approved_with_edit_note`
- Owner note: use won't instead of will not
- Candidate: I won't claim this replaces your provider. The useful check is whether there is a gap it does not cover.
- Requires design decision: `false`
- Context sensitive: `false`

## Boundaries

- No runtime behavior change.
- No response text behavior change.
- No German exact phrase promotion.
- No LLM calls, LLM judging, provider calls, retrieval enablement, private data reads, voice playback, public demo use, payment collection, contract signing, or production promotion.

## Next Gate

Create a narrow English runtime patch checkpoint only for accepted as-written items and owner-corrected rework candidates. Do not bundle voicemail action-only behavior or coverage knowledge-policy design without separate targeted checks.
