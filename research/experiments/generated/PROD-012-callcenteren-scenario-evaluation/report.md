# PROD-012 CallCenterEN Scenario Evaluation

This local checkpoint uses AIxBlock / CallCenterEN only as pattern grounding for project-owned synthetic scenarios.
It compares the old core retrieval-disabled runtime against the RAG-018 retrieval version on the same fixed scenario turns.

No dataset download, provider call, private customer data read, transcript body storage, vector database, embedding provider, or LLM reranker was used.

## Source Boundary

- Dataset: https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english
- Paper: https://arxiv.org/abs/2507.02958
- License observed: `cc-by-nc-4.0`
- Reuse label: `pattern_grounding_only`
- Commercial runtime use: `false`

## Metrics

- Hard failure rate: `0.0`
- Non-sale correctness: `1.0`
- Leakage failure rate: `0.0`
- Scenario quality score: `1.0`
- Sales/emotional handling score: `1.0`
- Retrieval win rate: `0.7143`

## Retrieval Version vs Old Core

- Old core total score: `5`
- Retrieval version total score: `14`
- Retrieval version wins: `5`
- Old core wins: `0`
- Protected turns preserved: `5/5`
- Decision: `keep_retrieval_opt_in_for_callcenteren_grounded_scenarios`

Interpretation: retrieval is better on these fixed CallCenterEN-grounded synthetic objection turns, but the result is still opt-in evidence. Do not make retrieval default from this checkpoint alone.

## Leakage Tests

- exact_transcript_sentence_check: `pass`
- high_similarity_paraphrase_check: `pass`
- single_source_scenario_check: `pass`
- commercial_runtime_prompt_check: `pass`

## Scenario Table

| Scenario | Label | Expected | Turns | Retrieval Wins | Non-Sale Correct |
| --- | --- | --- | ---: | ---: | --- |
| PROD-012-CCEN-001 | sale_eligible | sale_ready | 3 | 3 | n/a |
| PROD-012-CCEN-002 | non_sale_correct | non_sale_correct | 2 | 1 | True |
| PROD-012-CCEN-003 | support_only | support_only | 2 | 0 | True |
| PROD-012-CCEN-004 | trust_repair | non_sale_correct | 2 | 1 | True |
| PROD-012-CCEN-005 | human_handoff | human_handoff | 2 | 0 | True |
| PROD-012-CCEN-006 | price_resistance | non_sale_correct | 1 | 0 | True |

## Exact Questions And Answers

### PROD-012-CCEN-001-T01 - Send information before deciding

- Scenario: `PROD-012-CCEN-001` / `sale_eligible`
- Stage: `relevance-check`
- Winner: `retrieval`
- Retrieval status: `influenced`
- Exact customer question/input:

```text
Can you send me information first? I do not know if this is relevant yet.
```

- Exact old/core answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

- Exact retrieval/RAG answer:

```text
I can send information. To make it relevant, should I send details about fit, pricing, or how a specialist would review this with you?
```

- Decision process:

  1. Policy classified the turn as sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
  2. Old/core path used policy response `Thanks. May I ask one quick clarifying question?` and local composer candidate `Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `influenced` with context flags `none` and retrieved item IDs `rag019-objection-diagnose-before-answering, rag019-objection-send-info-clarify, rag016a-response-autonomy-reminder, rag010-response-impact-bridge`.
  4. Retrieved advisory hints:
     - `rag019-objection-diagnose-before-answering` score `9`: Treat objections as diagnostic information gaps, then ask one clarifying question before giving evidence or a next step.
     - `rag019-objection-send-info-clarify` score `9`: When the customer says send me information, ask which decision question the information should answer and agree the smallest useful follow-up.
     - `rag016a-response-autonomy-reminder` score `8`: Explicitly preserve the customer's freedom to say no, pause, compare alternatives, or choose no next step.
     - `rag010-response-impact-bridge` score `7`: When a customer describes an operational issue, ask one neutral question that connects the issue to business impact the customer can confirm.
  5. Retrieval composer candidate was `I can send information. To make it relevant, should I send details about fit, pricing, or how a specialist would review this with you?`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `True`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `retrieval` with score delta `2`.

### PROD-012-CCEN-001-T02 - Needs boss before deciding

- Scenario: `PROD-012-CCEN-001` / `sale_eligible`
- Stage: `relevance-check`
- Winner: `retrieval`
- Retrieval status: `influenced`
- Exact customer question/input:

```text
I need to ask my boss before deciding anything.
```

- Exact old/core answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

- Exact retrieval/RAG answer:

```text
That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?
```

- Decision process:

  1. Policy classified the turn as sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
  2. Old/core path used policy response `Thanks. May I ask one quick clarifying question?` and local composer candidate `Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `influenced` with context flags `none` and retrieved item IDs `rag019-objection-diagnose-before-answering, rag010-response-real-timing-check, rag014-response-consent-based-schedule-confirmation, rag016a-response-autonomy-reminder`.
  4. Retrieved advisory hints:
     - `rag019-objection-diagnose-before-answering` score `8`: Treat objections as diagnostic information gaps, then ask one clarifying question before giving evidence or a next step.
     - `rag010-response-real-timing-check` score `7`: Ask about the customer's real timing, decision window, or deadline to understand priority without creating urgency.
     - `rag014-response-consent-based-schedule-confirmation` score `7`: After a customer voluntarily agrees to a meeting or callback, confirm the date, time, channel, and expected next step in one concise check.
     - `rag016a-response-autonomy-reminder` score `7`: Explicitly preserve the customer's freedom to say no, pause, compare alternatives, or choose no next step.
  5. Retrieval composer candidate was `That makes sense. Should I send a short summary you can share with your boss, or is there one concern I should address first?`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `True`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `retrieval` with score delta `2`.

### PROD-012-CCEN-001-T03 - Cold-call trust concern

- Scenario: `PROD-012-CCEN-001` / `sale_eligible`
- Stage: `relevance-check`
- Winner: `retrieval`
- Retrieval status: `influenced`
- Exact customer question/input:

```text
I do not know your company and I do not trust random software calls.
```

- Exact old/core answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

- Exact retrieval/RAG answer:

```text
Fair. Trust matters on a cold call. To make this useful, should I send company context, security details, or a specialist review path first?
```

- Decision process:

  1. Policy classified the turn as sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
  2. Old/core path used policy response `Thanks. May I ask one quick clarifying question?` and local composer candidate `Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `influenced` with context flags `none` and retrieved item IDs `rag019-objection-diagnose-before-answering, rag016a-response-autonomy-reminder, rag010-response-impact-bridge, rag010-response-real-timing-check`.
  4. Retrieved advisory hints:
     - `rag019-objection-diagnose-before-answering` score `9`: Treat objections as diagnostic information gaps, then ask one clarifying question before giving evidence or a next step.
     - `rag016a-response-autonomy-reminder` score `8`: Explicitly preserve the customer's freedom to say no, pause, compare alternatives, or choose no next step.
     - `rag010-response-impact-bridge` score `7`: When a customer describes an operational issue, ask one neutral question that connects the issue to business impact the customer can confirm.
     - `rag010-response-real-timing-check` score `7`: Ask about the customer's real timing, decision window, or deadline to understand priority without creating urgency.
  5. Retrieval composer candidate was `Fair. Trust matters on a cold call. To make this useful, should I send company context, security details, or a specialist review path first?`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `True`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `retrieval` with score delta `2`.

### PROD-012-CCEN-002-T01 - German price concern

- Scenario: `PROD-012-CCEN-002` / `non_sale_correct`
- Stage: `relevance-check`
- Winner: `retrieval`
- Retrieval status: `influenced`
- Exact customer question/input:

```text
Das klingt zu teuer und ich weiss nicht, ob sich der Aufwand lohnt.
```

- Exact old/core answer:

```text
Das verstehe ich. Geht es Ihnen vor allem um den Preis, die Bedingungen oder darum, ob sich der Aufwand lohnt?
```

- Exact retrieval/RAG answer:

```text
Das verstehe ich. Damit ich nicht am Punkt vorbeirede: Geht es Ihnen eher um den Preis, die Bedingungen oder darum, ob sich der Aufwand lohnt?
```

- Decision process:

  1. Policy classified the turn as sales difficulty `price-objection`, emotion `skeptical-or-negative`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
  2. Old/core path used policy response `Das verstehe ich. Geht es eher um den Preis selbst oder darum, ob sich der Aufwand lohnt?` and local composer candidate `Das verstehe ich. Geht es Ihnen vor allem um den Preis, die Bedingungen oder darum, ob sich der Aufwand lohnt?`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `influenced` with context flags `none` and retrieved item IDs `rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag007-response-yes-and-objection-framing, rag010-response-real-timing-check`.
  4. Retrieved advisory hints:
     - `rag016a-response-autonomy-reminder` score `7`: Explicitly preserve the customer's freedom to say no, pause, compare alternatives, or choose no next step.
     - `rag019-objection-diagnose-before-answering` score `6`: Treat objections as diagnostic information gaps, then ask one clarifying question before giving evidence or a next step.
     - `rag007-response-yes-and-objection-framing` score `5`: Acknowledge the customer's concern before moving to a useful next step; do not use agreement language to blur factual or compliance boundaries.
     - `rag010-response-real-timing-check` score `5`: Ask about the customer's real timing, decision window, or deadline to understand priority without creating urgency.
  5. Retrieval composer candidate was `Das verstehe ich. Damit ich nicht am Punkt vorbeirede: Geht es Ihnen eher um den Preis, die Bedingungen oder darum, ob sich der Aufwand lohnt?`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `True`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `retrieval` with score delta `1`.

### PROD-012-CCEN-002-T02 - Guarantee request

- Scenario: `PROD-012-CCEN-002` / `non_sale_correct`
- Stage: `relevance-check`
- Winner: `tie`
- Retrieval status: `blocked`
- Exact customer question/input:

```text
Nur wenn Sie garantieren koennen, dass die Geschwindigkeit bei mir stabil ist.
```

- Exact old/core answer:

```text
Ich verstehe die Sicherheitsfrage. Ich moechte nichts versprechen, was von Details abhaengt, deshalb leite ich das lieber an einen Spezialisten weiter.
```

- Exact retrieval/RAG answer:

```text
Ich verstehe die Sicherheitsfrage. Ich moechte nichts versprechen, was von Details abhaengt, deshalb leite ich das lieber an einen Spezialisten weiter.
```

- Decision process:

  1. Policy classified the turn as sales difficulty `claim-boundary`, emotion `skeptical-or-negative`, strategy `inquiry`, next action `escalate`, call control `transfer-or-escalate`.
  2. Old/core path used policy response `Ich moechte nichts garantieren, was von den Details abhaengt. Ich kann das an einen Spezialisten weiterleiten.` and local composer candidate `Ich verstehe die Sicherheitsfrage. Ich moechte nichts versprechen, was von Details abhaengt, deshalb leite ich das lieber an einen Spezialisten weiter.`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `blocked` with context flags `human_escalation` and retrieved item IDs `none`.
  4. Retrieved advisory hints: none
  5. Retrieval composer candidate was `Ich verstehe die Sicherheitsfrage. Ich moechte nichts versprechen, was von Details abhaengt, deshalb leite ich das lieber an einen Spezialisten weiter.`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `False`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `tie` with score delta `0`.

### PROD-012-CCEN-003-T01 - Do not call

- Scenario: `PROD-012-CCEN-003` / `support_only`
- Stage: `opening-permission`
- Winner: `tie`
- Retrieval status: `blocked`
- Exact customer question/input:

```text
Rufen Sie mich bitte nicht mehr an.
```

- Exact old/core answer:

```text
Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhoeren.
```

- Exact retrieval/RAG answer:

```text
Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhoeren.
```

- Decision process:

  1. Policy classified the turn as sales difficulty `do-not-call`, emotion `skeptical-or-negative`, strategy `rapport`, next action `suppress-contact`, call control `end-call`.
  2. Old/core path used policy response `Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhoeren.` and local composer candidate `Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhoeren.`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `blocked` with context flags `do_not_call, customer_refusal, protected_script` and retrieved item IDs `none`.
  4. Retrieved advisory hints: none
  5. Retrieval composer candidate was `Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhoeren.`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `False`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `tie` with score delta `0`.

### PROD-012-CCEN-003-T02 - Repeated silence

- Scenario: `PROD-012-CCEN-003` / `support_only`
- Stage: `opening-permission`
- Winner: `tie`
- Retrieval status: `blocked`
- Exact customer question/input (`input_type`: `silence-timeout`, `silence_count`: `2`):

```text

```

- Exact old/core answer:

```text
Ich beende den Anruf fuer jetzt. Auf Wiederhoeren.
```

- Exact retrieval/RAG answer:

```text
Ich beende den Anruf fuer jetzt. Auf Wiederhoeren.
```

- Decision process:

  1. Policy classified the turn as sales difficulty `repeated-silence`, emotion `neutral`, strategy `rapport`, next action `close-politely`, call control `end-call`.
  2. Old/core path used policy response `Ich beende den Anruf fuer jetzt. Auf Wiederhoeren.` and local composer candidate `Ich beende den Anruf fuer jetzt. Auf Wiederhoeren.`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `blocked` with context flags `protected_script` and retrieved item IDs `none`.
  4. Retrieved advisory hints: none
  5. Retrieval composer candidate was `Ich beende den Anruf fuer jetzt. Auf Wiederhoeren.`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `False`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `tie` with score delta `0`.

### PROD-012-CCEN-004-T01 - Trust proof request

- Scenario: `PROD-012-CCEN-004` / `trust_repair`
- Stage: `relevance-check`
- Winner: `retrieval`
- Retrieval status: `influenced`
- Exact customer question/input:

```text
I do not know your company and I do not trust random software calls.
```

- Exact old/core answer:

```text
Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
```

- Exact retrieval/RAG answer:

```text
Fair. Trust matters on a cold call. To make this useful, should I send company context, security details, or a specialist review path first?
```

- Decision process:

  1. Policy classified the turn as sales difficulty `unknown-runtime-signal`, emotion `neutral`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
  2. Old/core path used policy response `Thanks. May I ask one quick clarifying question?` and local composer candidate `Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `influenced` with context flags `none` and retrieved item IDs `rag019-objection-diagnose-before-answering, rag016a-response-autonomy-reminder, rag010-response-impact-bridge, rag010-response-real-timing-check`.
  4. Retrieved advisory hints:
     - `rag019-objection-diagnose-before-answering` score `9`: Treat objections as diagnostic information gaps, then ask one clarifying question before giving evidence or a next step.
     - `rag016a-response-autonomy-reminder` score `8`: Explicitly preserve the customer's freedom to say no, pause, compare alternatives, or choose no next step.
     - `rag010-response-impact-bridge` score `7`: When a customer describes an operational issue, ask one neutral question that connects the issue to business impact the customer can confirm.
     - `rag010-response-real-timing-check` score `7`: Ask about the customer's real timing, decision window, or deadline to understand priority without creating urgency.
  5. Retrieval composer candidate was `Fair. Trust matters on a cold call. To make this useful, should I send company context, security details, or a specialist review path first?`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `True`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `retrieval` with score delta `2`.

### PROD-012-CCEN-004-T02 - Asks for a real person

- Scenario: `PROD-012-CCEN-004` / `trust_repair`
- Stage: `opening-permission`
- Winner: `tie`
- Retrieval status: `blocked`
- Exact customer question/input:

```text
Please have a real person call me if this is about software.
```

- Exact old/core answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

- Exact retrieval/RAG answer:

```text
Of course. I will route this to a solutions specialist instead of continuing automatically.
```

- Decision process:

  1. Policy classified the turn as sales difficulty `human-request`, emotion `neutral`, strategy `rapport`, next action `escalate`, call control `transfer-or-escalate`.
  2. Old/core path used policy response `Of course. I will route this to a human specialist instead of continuing automatically.` and local composer candidate `Of course. I will route this to a solutions specialist instead of continuing automatically.`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `blocked` with context flags `human_escalation` and retrieved item IDs `none`.
  4. Retrieved advisory hints: none
  5. Retrieval composer candidate was `Of course. I will route this to a solutions specialist instead of continuing automatically.`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `False`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `tie` with score delta `0`.

### PROD-012-CCEN-005-T01 - Exact product detail lookup

- Scenario: `PROD-012-CCEN-005` / `human_handoff`
- Stage: `product-detail-check`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Exact customer question/input:

```text
Welcher genaue Tarif ist das und wie viel Datenvolumen ist enthalten?
```

- Exact old/core answer:

```text
Gute Frage. Ich pruefe lieber zuerst die freigegebenen Produktinformationen, damit ich bei Details nicht rate.
```

- Exact retrieval/RAG answer:

```text
Gute Frage. Ich pruefe lieber zuerst die freigegebenen Produktinformationen, damit ich bei Details nicht rate.
```

- Decision process:

  1. Policy classified the turn as sales difficulty `product-detail-lookup`, emotion `neutral`, strategy `evidence-or-benefit`, next action `continue`, call control `bridge-then-continue`.
  2. Old/core path used policy response `Einen Moment, ich pruefe die freigegebenen Produktinformationen.` and local composer candidate `Gute Frage. Ich pruefe lieber zuerst die freigegebenen Produktinformationen, damit ich bei Details nicht rate.`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `retrieved_not_used` with context flags `none` and retrieved item IDs `rag016a-response-autonomy-reminder, rag007-response-yes-and-objection-framing, rag010-response-impact-bridge, rag010-response-real-timing-check`.
  4. Retrieved advisory hints:
     - `rag016a-response-autonomy-reminder` score `7`: Explicitly preserve the customer's freedom to say no, pause, compare alternatives, or choose no next step.
     - `rag007-response-yes-and-objection-framing` score `4`: Acknowledge the customer's concern before moving to a useful next step; do not use agreement language to blur factual or compliance boundaries.
     - `rag010-response-impact-bridge` score `4`: When a customer describes an operational issue, ask one neutral question that connects the issue to business impact the customer can confirm.
     - `rag010-response-real-timing-check` score `4`: Ask about the customer's real timing, decision window, or deadline to understand priority without creating urgency.
  5. Retrieval composer candidate was `Gute Frage. Ich pruefe lieber zuerst die freigegebenen Produktinformationen, damit ich bei Details nicht rate.`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `False`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `tie` with score delta `0`.

### PROD-012-CCEN-005-T02 - Callback scheduling

- Scenario: `PROD-012-CCEN-005` / `human_handoff`
- Stage: `scheduling`
- Winner: `tie`
- Retrieval status: `blocked`
- Exact customer question/input:

```text
Mittwoch um 10 Uhr passt fuer den Rueckruf.
```

- Exact old/core answer:

```text
Bestaetigt. Ich notiere den Rueckruftermin fuer den Spezialisten. Auf Wiederhoeren.
```

- Exact retrieval/RAG answer:

```text
Bestaetigt. Ich notiere den Rueckruftermin fuer den Spezialisten. Auf Wiederhoeren.
```

- Decision process:

  1. Policy classified the turn as sales difficulty `scheduling-confirmation`, emotion `positive`, strategy `direct-ask-or-commitment`, next action `confirm-scheduling`, call control `schedule-and-end`.
  2. Old/core path used policy response `Bestaetigt. Ich notiere den Rueckruf fuer den Spezialisten. Auf Wiederhoeren.` and local composer candidate `Bestaetigt. Ich notiere den Rueckruftermin fuer den Spezialisten. Auf Wiederhoeren.`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `blocked` with context flags `protected_script` and retrieved item IDs `none`.
  4. Retrieved advisory hints: none
  5. Retrieval composer candidate was `Bestaetigt. Ich notiere den Rueckruftermin fuer den Spezialisten. Auf Wiederhoeren.`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `False`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `tie` with score delta `0`.

### PROD-012-CCEN-006-T01 - English price objection ties core

- Scenario: `PROD-012-CCEN-006` / `price_resistance`
- Stage: `relevance-check`
- Winner: `tie`
- Retrieval status: `retrieved_not_used`
- Exact customer question/input:

```text
That sounds too expensive and I am not sure this is worth the effort.
```

- Exact old/core answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

- Exact retrieval/RAG answer:

```text
That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
```

- Decision process:

  1. Policy classified the turn as sales difficulty `price-objection`, emotion `skeptical-or-negative`, strategy `inquiry`, next action `ask-follow-up`, call control `continue-call`.
  2. Old/core path used policy response `That makes sense. Is the main concern the price itself, or whether the review is worth the effort?` and local composer candidate `That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?`. Validation passed: `True`. Fallback used: `False`.
  3. Retrieval path status `retrieved_not_used` with context flags `none` and retrieved item IDs `rag014-response-cost-of-inaction-check, rag016a-response-autonomy-reminder, rag019-objection-diagnose-before-answering, rag007-response-yes-and-objection-framing`.
  4. Retrieved advisory hints:
     - `rag014-response-cost-of-inaction-check` score `8`: When a customer has confirmed a problem and prefers to wait, ask neutrally whether keeping the current path has a cost worth considering.
     - `rag016a-response-autonomy-reminder` score `8`: Explicitly preserve the customer's freedom to say no, pause, compare alternatives, or choose no next step.
     - `rag019-objection-diagnose-before-answering` score `8`: Treat objections as diagnostic information gaps, then ask one clarifying question before giving evidence or a next step.
     - `rag007-response-yes-and-objection-framing` score `7`: Acknowledge the customer's concern before moving to a useful next step; do not use agreement language to blur factual or compliance boundaries.
  5. Retrieval composer candidate was `That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?`. Validation passed: `True`. Fallback used: `False`. Retrieval used in runtime: `False`.
  6. Safety/selection kept campaign facts above RAG: `True`; protected text preserved: `True`; final winner: `tie` with score delta `0`.


## Runtime Boundary

The generated scenarios are synthetic rewrites combined from at least three source patterns. Raw transcript text, high-similarity paraphrases, single-source scenario generation, and transcript-derived commercial runtime prompts are hard failures.
