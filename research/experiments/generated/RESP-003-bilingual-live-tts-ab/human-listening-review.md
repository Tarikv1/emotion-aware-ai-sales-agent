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

## Follow-Up Listening Notes

Date: 2026-05-08

Reviewer: Tarik

- Shaped runtime remains much better than plain guarded across the bilingual A/B set.
- English objection shaped runtime is a strong current baseline and should be preserved.
- English next-step shaped runtime is also good and should be preserved.
- English trust shaped runtime has a swallowed transition that sounded like an unclear filler; inspection showed no filler word in the TTS text.
- Follow-up correction: lowering English trust speed too far increased roboticness, so the better fix is to keep trust repair lively and smooth the provider-facing transition text.
- German roboticness is almost completely gone after switching to the newer German voice ID, suggesting the earlier roboticness was mostly voice-identity related rather than only pacing-rule related.
- German objection shaped runtime has pauses that feel only slightly too long, and the German pace can be nudged a tiny bit faster without returning to the earlier too-fast profile.

Follow-up tuning decision:

```text
Keep English objection and next-step speeds in the faster sales-call range.
Keep English trust-repair reassurance in a lively bounded speed band.
Replace the brittle English trust transition with "I'm not asking you to decide now, so I'll keep it brief."
Raise the German VOICE-034 lower speed bound only slightly, from 0.97 to 0.975.
Do not add or remove German pause tags from this objection case yet.
```

## Corrected Live Pass Acceptance

Date: 2026-05-08

Reviewer: Tarik

Run boundary:

- Provider: ElevenLabs
- Provider calls made: yes, 12
- Audio files created: yes, 12
- Customer audio uploaded: no
- Voice cloning used: no
- API key value logged: no
- Voice ID value logged: no
- Private call data used: no

Reviewed corrected shaped runtime samples:

- `RESP-003-AB-EN-TRUST-en-elevenlabs-shaped_runtime.mp3`
- `RESP-003-AB-EN-OBJECTION-en-elevenlabs-shaped_runtime.mp3`
- `RESP-003-AB-EN-NEXT-STEP-en-elevenlabs-shaped_runtime.mp3`
- `RESP-003-AB-DE-OBJECTION-de-elevenlabs-shaped_runtime.mp3`

Accepted correction:

```text
The corrected English trust, English objection, English next-step, and German objection shaped runtime samples sound good enough to keep as the current checkpoint.
```

Claim boundary:

```text
Allowed: in this corrected RESP-003 bilingual ElevenLabs live pass, Tarik accepted the reviewed shaped-runtime samples listed above.
Not allowed: the voice is production-ready for all campaigns, providers, voices, or real leads.
```
