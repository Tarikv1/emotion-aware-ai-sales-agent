# PROD-083 English Guided Option Selection Review Import

`PROD-083` imports Tarik's `PROD-082` guided option selection review feedback.

This is import-only. It does not patch runtime behavior, response text, classifier reachability, retrieval, payment handling, or spoken naturalness behavior.

## Imported Decision

- Decision: needs rewrite before probe
- Narrow policy probe approved: `false`
- Existing examples approved: `false`
- Rewrite required: `true`
- Review HTML created: `false`
- Recommended next checkpoint: `PROD-084-english-guided-option-selection-rewrite-design`

## Rewrite Rules

- Leave obvious facts out.
- Do not repeat what the customer already said unless explicitly needed.
- Answer the actual fit or difference question.
- Use approved plan feature facts, not invented differences.
- Steer toward the better option when known customer facts support it.
- Keep wording shorter and more human.
- Preserve autonomy without repeatedly saying neither or not now.
- Use light persuasion when the customer is uncertain but still engaged.
- Separate option selection from payment handling.

## Plan Facts

- Plan feature matrix required: `true`
- Invent plan features allowed: `false`
- Example placeholders: `$29` -> `feature_x/feature_y/feature_z`; `$59` -> `$29` features plus additional approved features

## Payment Workflow

- No payment on the call by default: `true`
- Approved campaign payment path can be explained: `true`
- Future agent payment handling deferred: `true`
- Campaign payment path examples: human callback, approved company-domain email link, approved registration link/form, or paperwork outside the call.

## Spoken Naturalness

- Sparse contextual discourse markers candidate: `true`
- Random fillers allowed: `false`
- Example markers: `I mean, like, you know`

## Imported Notes

- The current examples are too defensive and overuse opt-out language.
- When a customer asks whether to choose the $29 or $59 option, the agent should explain fit and plan contents instead of repeating the two prices.
- The agent may steer toward one option when customer facts and approved plan facts support that recommendation.
- The agent should not repeat obvious facts, such as that $29 is lower than $59.
- The agent should explain actual differences using an approved plan feature matrix, such as $29 has X features and $59 adds Y features.
- If the customer asks for a recommendation, the agent can recommend a better fit without pretending to choose for the customer.
- The agent can suggest starting with the cheaper plan and upgrading later when that is an approved product path.
- If the customer asks to decide later, keep the answer short and do not say the same thing twice.
- If the customer says neither option feels right, treat that as uncertainty and use light persuasion plus acknowledgement instead of ending the opportunity too quickly.
- For payment, no payment on the call by default for now, but the agent may explain the approved campaign payment path if one exists.
- Future payment handling by the agent may be reopened later, but it is not approved now.
- Add a future spoken-naturalness rule for sparse human discourse markers like I mean or like, but do not randomly add fillers every few sentences.

## Boundary Status

- Runtime behavior changed: `false`
- Response text behavior changed: `false`
- Classifier behavior changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- LLM judging used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Real customer use unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- German exact-phrase promotion allowed: `false`
- German naturalness claimed: `false`
- Legal compliance claimed: `false`
