# RESP-006 German Runtime Version A/B Human Listening Review

Date: 2026-05-08

Reviewer: Tarik

## Input

- Question: Können Sie mir zuerst etwas schicken? Ich kenne Ihr Unternehmen nicht, ich möchte kein Verkaufsgespräch, und ich muss verstehen, was danach konkret passieren würde, bevor ich meinen Chef einbeziehe.
- Purpose: compare old runtime versus newer shaped runtime on the same longer German answer.
- Score each variant from `1` to `5` before deciding whether the English personality lanes survive in Deutsch.

## old_plain_guarded

- Label: `Old runtime: plain guarded German response`
- Source checkpoint: `RESP-001 guarded final_response`
- Audio path: `not created in current dry-run`

Text:

```text
Gute Frage. Ich erwarte nicht, dass Sie in diesem Gespräch eine Entscheidung treffen. Die praktische Variante wäre: Ich kann Ihnen eine kurze Zusammenfassung schicken, warum wir angerufen haben, was in der Workflow-Prüfung angeschaut würde und was ein Spezialist bestätigt, bevor irgendetwas weitergeht. Wenn es danach nicht relevant ist, können Sie es ignorieren oder einfach Nein sagen.
```

Scores:

- German naturalness:
- German formality:
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

- Label: `New runtime: shaped provider-ready German response`
- Source checkpoint: `RESP-002/VOICE-044 shaped runtime`
- Audio path: `not created in current dry-run`

Text:

```text
Gute Frage. Um, ich erwarte nicht, dass Sie in diesem Gespräch eine Entscheidung treffen. <break time="0.185s" /> Die praktische Variante wäre: Ich kann Ihnen eine kurze Zusammenfassung schicken, warum wir angerufen haben, was in der Workflow-Prüfung angeschaut würde und was ein Spezialist bestätigt, bevor irgendetwas weitergeht. Wenn es danach nicht relevant ist, können Sie es ignorieren oder einfach Nein sagen.
```

Scores:

- German naturalness:
- German formality:
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
TODO: choose old_plain_guarded, new_shaped_runtime, accept both as German personalities, revise both, or run live audio again.
```

Not allowed yet:

```text
Either German voice style is production-ready for all campaigns, providers, voices, or real leads.
```