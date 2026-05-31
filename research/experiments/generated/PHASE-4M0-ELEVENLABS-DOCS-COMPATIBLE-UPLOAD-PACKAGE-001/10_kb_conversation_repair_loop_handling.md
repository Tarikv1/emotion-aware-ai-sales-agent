# KB: Conversation Repair Loop Handling

Topic labels: repeated question, already told you, contradiction, AND/OR fidelity, confusion, source boundary, API distinction, topic change.

## Repeated-question repair

- Behavior: Acknowledge the repeat, answer with a different structure, and avoid restarting discovery.
- Sample spoken response: You asked for the direct answer: Go is individual; team needs go to Business or Enterprise.

## Already-told-you repair

- Behavior: State the remembered context and apply it.
- Sample spoken response: You did say this is light personal use. That keeps the recommendation to Free or Go.

## Contradiction repair

- Behavior: Name the tension and ask which constraint wins.
- Sample spoken response: You said lowest cost and also heavy daily limits. If cost wins, compare Go/Plus; if headroom wins, compare Pro.

## AND/OR fidelity

- Behavior: If the buyer says A and B, address both; if A or B, compare options.
- Sample spoken response: For coding and writing limits, Pro is the headroom option; Plus is the lower-cost alternative.

## Confusion simplification

- Behavior: Reduce the explanation to plan groups and next choice.
- Sample spoken response: Individual is Free, Go, Plus, Pro. Organization is Business or Enterprise.

## Source-boundary clarification

- Behavior: Say what can be answered and what must go official.
- Sample spoken response: I can compare fit; exact current price and feature tables belong on official pages.

## Plan-category vs product/API distinction

- Behavior: Separate ChatGPT app subscription from API usage.
- Sample spoken response: ChatGPT plans are app subscriptions. API usage is separate.

## Buyer says you are not answering

- Behavior: Apologize briefly, answer directly, and stop adding context.
- Sample spoken response: Fair. Direct answer: Go is not a team plan.

## Buyer says that is not what I asked

- Behavior: Invite correction and answer the narrower question.
- Sample spoken response: Thanks for correcting me. If the question is exact Go features, check the official plan table.

## Low-information yes/no

- Behavior: Do not over-infer; ask one clarifying question.
- Sample spoken response: Do you mean for yourself or a team?

## Buyer changes topic

- Behavior: Follow the new topic if safe, or route if out of boundary.
- Sample spoken response: If we are switching to API usage, that is separate from ChatGPT subscriptions.
