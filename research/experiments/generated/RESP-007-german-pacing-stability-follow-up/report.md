# RESP-007 German Pacing-Stability Follow-Up

This is a German pacing-stability follow-up to RESP-006. It keeps the same answer content and changes only provider-facing delivery surfaces.

## Summary

- Cases: `1`
- German cases: `1`
- Variants: `2`
- Same question for all variants: `True`
- Same answer content for all variants: `True`
- Only delivery surface changed: `True`
- Voice-personality selector unblocked: `False`
- Provider: `elevenlabs`
- Live call requested: `True`
- API calls made: `2`
- Audio files created: `2`
- Customer audio uploaded: `False`
- Voice cloning used: `False`
- Quality claim allowed: `False`

## Variants

### RESP-007-DE-PACING-STABILITY-COMPLEX

Question: Können Sie mir zuerst etwas schicken? Ich kenne Ihr Unternehmen nicht, ich möchte kein Verkaufsgespräch, und ich muss verstehen, was danach konkret passieren würde, bevor ich meinen Chef einbeziehe.

Pacing problem:

- `old_plain_guarded`: starts a bit too fast and then becomes a bit too slow
- `new_shaped_runtime`: starts strong but becomes a bit too fast later

#### old_plain_pacing_stabilized

- Label: `Old runtime stabilized: less rushed opening, less late drag`
- Source variant: `old_plain_guarded`
- Source checkpoint: `RESP-006 old_plain_guarded`
- Pacing targets: `opening_rush_guard, late_drag_prevention`
- Content changed: `False`
- Voice settings: `{"similarity_boost": 0.75, "speed": 1.02, "stability": 0.48, "style": 0.0, "use_speaker_boost": true}`
- Audio created: `True`
- Audio path: `research\experiments\generated\RESP-007-german-pacing-stability-follow-up\audio\RESP-007-DE-PACING-STABILITY-COMPLEX-de-elevenlabs-old_plain_pacing_stabilized.mp3`
- Fallback reason: `not needed`

TTS input:

Gute Frage. <break time="165ms"/> Ich erwarte nicht, dass Sie in diesem Gespräch eine Entscheidung treffen. <break time="125ms"/> Die praktische Variante wäre: Ich kann Ihnen eine kurze Zusammenfassung schicken, warum wir angerufen haben, was in der Workflow-Prüfung angeschaut würde und was ein Spezialist bestätigt, bevor irgendetwas weitergeht. <break time="95ms"/> Wenn es danach nicht relevant ist, können Sie es ignorieren oder einfach Nein sagen.


#### new_shaped_pacing_stabilized

- Label: `New runtime stabilized: strong opening with late speed cap`
- Source variant: `new_shaped_runtime`
- Source checkpoint: `RESP-006 new_shaped_runtime`
- Pacing targets: `late_speed_cap, late_answer_spacing`
- Content changed: `False`
- Voice settings: `{"similarity_boost": 0.75, "speed": 1.02, "stability": 0.56, "style": 0.0, "use_speaker_boost": true}`
- Audio created: `True`
- Audio path: `research\experiments\generated\RESP-007-german-pacing-stability-follow-up\audio\RESP-007-DE-PACING-STABILITY-COMPLEX-de-elevenlabs-new_shaped_pacing_stabilized.mp3`
- Fallback reason: `not needed`

TTS input:

Gute Frage. <break time="145ms"/> Ich erwarte nicht, dass Sie in diesem Gespräch eine Entscheidung treffen. <break time="165ms"/> Die praktische Variante wäre: Ich kann Ihnen eine kurze Zusammenfassung schicken, warum wir angerufen haben, was in der Workflow-Prüfung angeschaut würde und was ein Spezialist bestätigt, bevor irgendetwas weitergeht. <break time="210ms"/> Wenn es danach nicht relevant ist, können Sie es ignorieren oder einfach Nein sagen.

## Boundary

- Dry-run by default.
- Live provider calls require `--live`, provider API key, selected German voice ID, and bounded timeout.
- No customer audio upload.
- No private raw audio read.
- No transcription.
- No voice cloning.
- API keys and raw voice IDs are never written to artifacts.
- The voice-personality selector remains blocked until Tarik records the listening review.
