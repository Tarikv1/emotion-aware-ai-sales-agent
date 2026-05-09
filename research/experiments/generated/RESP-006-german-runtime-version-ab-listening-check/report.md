# RESP-006 German Runtime Version A/B Listening Check

This report compares one old runtime version and one newer runtime version answering the same German question.

The answer is intentionally longer for more complex speaking, so pacing, transitions, formality, and AI-obviousness are easier to judge in Deutsch.

## Summary

- Cases: `1`
- German cases: `1`
- Variants: `2`
- Same question for all variants: `True`
- Provider: `elevenlabs`
- Live call requested: `False`
- API calls made: `0`
- Audio files created: `0`
- Fallback count: `2`
- Customer audio uploaded: `False`
- Voice cloning used: `False`
- Quality claim allowed: `False`

## Variants

### RESP-006-SAME-Q-DE-COMPLEX

Question: Können Sie mir zuerst etwas schicken? Ich kenne Ihr Unternehmen nicht, ich möchte kein Verkaufsgespräch, und ich muss verstehen, was danach konkret passieren würde, bevor ich meinen Chef einbeziehe.

#### old_plain_guarded

- Label: `Old runtime: plain guarded German response`
- Source checkpoint: `RESP-001 guarded final_response`
- Provider rendering used: `False`
- Audio created: `False`
- Audio path: `not created`
- Fallback reason: `dry-run-mode`

TTS input:

Gute Frage. Ich erwarte nicht, dass Sie in diesem Gespräch eine Entscheidung treffen. Die praktische Variante wäre: Ich kann Ihnen eine kurze Zusammenfassung schicken, warum wir angerufen haben, was in der Workflow-Prüfung angeschaut würde und was ein Spezialist bestätigt, bevor irgendetwas weitergeht. Wenn es danach nicht relevant ist, können Sie es ignorieren oder einfach Nein sagen.

#### new_shaped_runtime

- Label: `New runtime: shaped provider-ready German response`
- Source checkpoint: `RESP-002/VOICE-044 shaped runtime`
- Provider rendering used: `True`
- Audio created: `False`
- Audio path: `not created`
- Fallback reason: `dry-run-mode`

TTS input:

Gute Frage. Um, ich erwarte nicht, dass Sie in diesem Gespräch eine Entscheidung treffen. <break time="0.185s" /> Die praktische Variante wäre: Ich kann Ihnen eine kurze Zusammenfassung schicken, warum wir angerufen haben, was in der Workflow-Prüfung angeschaut würde und was ein Spezialist bestätigt, bevor irgendetwas weitergeht. Wenn es danach nicht relevant ist, können Sie es ignorieren oder einfach Nein sagen.

## Boundary

- Dry-run by default.
- Live provider calls require `--live`, provider API key, selected German voice ID, and bounded timeout.
- No customer audio upload.
- No private raw audio read.
- No transcription.
- No voice cloning.
- API keys and raw voice IDs are never written to artifacts.
- No German voice-personality claim is allowed until Tarik records the listening review.
