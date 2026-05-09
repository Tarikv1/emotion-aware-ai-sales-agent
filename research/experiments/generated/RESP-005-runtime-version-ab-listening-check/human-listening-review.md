# RESP-005 Runtime Version A/B Human Listening Review

Date: 2026-05-08

Reviewer: Tarik

## Input

- Question: Can you send me something first? I do not know your company, I do not want a sales pitch, and I need to understand what would actually happen next before I involve my boss.
- Purpose: compare old runtime versus newer shaped runtime on the same longer answer.
- Score each variant from `1` to `5` before deciding.

## old_plain_guarded

- Label: `Old runtime: plain guarded response`
- Source checkpoint: `RESP-001 guarded final_response`
- Audio path: `not created in current dry-run`

Text:

```text
Good question. I am not asking you to decide on this call. The practical version is this: I can send a short summary that explains why we called, what the workflow review would check, and what a specialist would confirm before anything moves forward. If it is not relevant after that, you can ignore it or say no.
```

Scores:

- Naturalness:
- More complex speaking flow:
- Sales-call pacing:
- Clarity:
- AI-obviousness:
- Trustworthiness:
- Overall preference:

Notes:

```text
TODO
```

## new_shaped_runtime

- Label: `New runtime: shaped provider-ready response`
- Source checkpoint: `RESP-002/VOICE-044 shaped runtime`
- Audio path: `not created in current dry-run`

Text:

```text
Good question. <break time="0.233s" /> Um, I'm not asking you to decide on this call. The practical version is this: I can send a short summary that explains why we called, what the workflow review would check, and what a specialist would confirm before anything moves forward. If it's not relevant after that, you can ignore it or say no.
```

Scores:

- Naturalness:
- More complex speaking flow:
- Sales-call pacing:
- Clarity:
- AI-obviousness:
- Trustworthiness:
- Overall preference:

Notes:

```text
TODO
```

## Decision

```text
TODO: choose old_plain_guarded, new_shaped_runtime, revise both, or run live audio again.
```

Not allowed yet:

```text
The selected voice is production-ready for all campaigns, providers, voices, or real leads.
```