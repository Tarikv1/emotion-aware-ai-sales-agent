# RESP-003 Bilingual Runtime A/B Human Listening Review

Date: 2026-05-07

Reviewer: Tarik

## Inputs

- Audio folder: `research/experiments/generated/RESP-003-bilingual-live-tts-ab/audio/`
- Dry-run harness report/result: `research/experiments/generated/RESP-003-bilingual-live-tts-ab/`

Note: `result.json` and `report.md` are generated harness artifacts and may be regenerated in dry-run mode. This review records Tarik's listening judgment from the live MP3 files listed below.

Reviewed audio:

- `RESP-003-AB-DE-OBJECTION-de-elevenlabs-plain_guarded.mp3`
- `RESP-003-AB-DE-OBJECTION-de-elevenlabs-shaped_runtime.mp3`
- `RESP-003-AB-EN-OBJECTION-en-elevenlabs-plain_guarded.mp3`
- `RESP-003-AB-EN-OBJECTION-en-elevenlabs-shaped_runtime.mp3`
- `RESP-003-AB-DE-TRUST-de-elevenlabs-plain_guarded.mp3`
- `RESP-003-AB-DE-TRUST-de-elevenlabs-shaped_runtime.mp3`
- `RESP-003-AB-EN-TRUST-en-elevenlabs-plain_guarded.mp3`
- `RESP-003-AB-EN-TRUST-en-elevenlabs-shaped_runtime.mp3`
- `RESP-003-AB-DE-NEXT-STEP-de-elevenlabs-plain_guarded.mp3`
- `RESP-003-AB-DE-NEXT-STEP-de-elevenlabs-shaped_runtime.mp3`
- `RESP-003-AB-EN-NEXT-STEP-en-elevenlabs-plain_guarded.mp3`
- `RESP-003-AB-EN-NEXT-STEP-en-elevenlabs-shaped_runtime.mp3`

## Technical Boundary

- Provider: ElevenLabs
- Provider calls made: yes, 12
- Audio files created: yes, 12
- Customer audio uploaded: no
- Voice cloning used: no
- API key value logged: no
- Voice ID value logged: no
- Private call data used: no

## Summary

The shaped runtime versions are clearly better than the plain guarded versions across the matched bilingual run.

Current decision:

```text
Prefer shaped_runtime over plain_guarded for runtime TTS input.
Do not use the current German voice/pacing as final production quality.
Keep English shaped runtime as the stronger current baseline.
```

## German Feedback

- Shaped runtime is much better than plain guarded.
- The German voice still sounds too robotic.
- German pacing is too fast in the shaped runtime output.
- The likely next quality improvement is selecting a better German ElevenLabs voice ID.
- Before the next German live check, slow the German runtime pacing profile so the same voice is not being driven too quickly.

## English Feedback

- Shaped runtime is much better than plain guarded.
- English shaped runtime is currently good on naturalness, clarity, emotional tone, and pacing.
- English does not need the same slowdown as German right now.
- English should continue improving in parallel, but it should not be changed by the German-specific pacing correction.

## Product Interpretation

Runtime delivery shaping is validated directionally by human review: the provider-ready shaped text is audibly better than sending the plain guarded response directly to TTS.

The remaining work is language-specific:

- German: reduce runtime pacing speed and test a better voice ID.
- English: preserve the current shaped runtime baseline and continue future voice improvements in parallel.

## Claim Boundary

Allowed claim:

```text
In the first matched RESP-003 bilingual ElevenLabs A/B run, the human reviewer clearly preferred shaped_runtime audio over plain_guarded audio.
```

Allowed implementation follow-up:

```text
Apply a German-specific pacing slowdown before the next live German listening check.
```

Not allowed yet:

```text
The German voice is production-ready.
The current German voice sounds human enough for real leads.
The shaped runtime voice is universally better across all providers, voices, and campaigns.
```
