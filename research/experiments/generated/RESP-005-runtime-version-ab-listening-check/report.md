# RESP-005 Runtime Version A/B Listening Check

This report compares one old runtime version and one newer runtime version answering the same question.

The answer is intentionally longer for more complex speaking, so pacing, transitions, contractions, and AI-obviousness are easier to judge.

## Summary

- Cases: `1`
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

### RESP-005-SAME-Q-EN-COMPLEX

Question: Can you send me something first? I do not know your company, I do not want a sales pitch, and I need to understand what would actually happen next before I involve my boss.

#### old_plain_guarded

- Label: `Old runtime: plain guarded response`
- Source checkpoint: `RESP-001 guarded final_response`
- Provider rendering used: `False`
- Audio created: `False`
- Audio path: `not created`
- Fallback reason: `dry-run-mode`

TTS input:

Good question. I am not asking you to decide on this call. The practical version is this: I can send a short summary that explains why we called, what the workflow review would check, and what a specialist would confirm before anything moves forward. If it is not relevant after that, you can ignore it or say no.

#### new_shaped_runtime

- Label: `New runtime: shaped provider-ready response`
- Source checkpoint: `RESP-002/VOICE-044 shaped runtime`
- Provider rendering used: `True`
- Audio created: `False`
- Audio path: `not created`
- Fallback reason: `dry-run-mode`

TTS input:

Good question. <break time="0.233s" /> Um, I'm not asking you to decide on this call. The practical version is this: I can send a short summary that explains why we called, what the workflow review would check, and what a specialist would confirm before anything moves forward. If it's not relevant after that, you can ignore it or say no.

## Boundary

- Dry-run by default.
- Live provider calls require `--live`, provider API key, selected voice ID, and bounded timeout.
- No customer audio upload.
- No private raw audio read.
- No transcription.
- No voice cloning.
- API keys and raw voice IDs are never written to artifacts.
- No quality claim is allowed until Tarik records the listening review.
