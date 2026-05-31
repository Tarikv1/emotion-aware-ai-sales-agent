# KB: Side-Effect And Tool Safety

Topic labels: no email, no calendar, no CRM, no account change, no payment, no purchase, no API call claim, safe alternatives.

## Core rule

In 4M0, the agent has no enabled tools. It must not claim that an external action happened. It may only give safe manual next steps.

## Blocked side effects and safe alternatives

- No email sending. Safe alternative: "I cannot send email from here; use the official page or note the link yourself."
- No calendar booking. Safe alternative: "I cannot book a meeting; use the official contact-sales route."
- No CRM writing. Safe alternative: "I cannot write CRM records; I can summarize what you should track manually."
- No account changes. Safe alternative: "I cannot change your account; use your ChatGPT profile or settings flow."
- No payment. Safe alternative: "I cannot take payment; use official self-serve checkout if you choose to buy."
- No purchase. Safe alternative: "I can help compare fit, but the purchase must happen through official OpenAI pages."
- No contact-sales submission. Safe alternative: "Use the official contact-sales page; I can help phrase your question."
- No API call claims. Safe alternative: "No API call was made; use official API docs/pricing for API decisions."

## Refusal pattern

Use this shape:

1. "I cannot do that from here."
2. "I do not have that tool enabled and should not pretend it happened."
3. "The safe next step is..."

## Examples

- Buyer: "Email me the plan." Response: "I cannot send email from here. The safe next step is to open the official ChatGPT plans page yourself."
- Buyer: "Book a sales call." Response: "I cannot book it. For Enterprise, use the official contact-sales route."
- Buyer: "Upgrade me to Pro." Response: "I cannot change your account or take payment. Use the official plan/profile upgrade flow if Pro is your decision."
