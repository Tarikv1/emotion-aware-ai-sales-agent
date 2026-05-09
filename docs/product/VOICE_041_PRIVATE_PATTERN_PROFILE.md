# VOICE-041 Private Pattern Profile

VOICE-041 is the guarded runtime bridge from reviewed private speech-pattern summaries to provider delivery settings.

It does not read raw private audio, transcribe speech, upload audio, clone a voice, or rewrite the guarded response.

## Purpose

- Consume only human-accepted abstract private speech-pattern hints.
- Apply bounded provider-setting adjustments for eligible freeform voice delivery.
- Keep protected campaign, disclosure, handoff, hangup, and do-not-call text untouched.
- Prevent low vocal-presence measurements from making the sales agent weaker.

## Input

VOICE-041 reads campaign configuration only:

```json
{
  "voice_private_pattern_profile": {
    "enabled": true,
    "review_status": "accepted",
    "source_review_milestone": "VOICE-031",
    "source_kind": "abstract_private_speech_patterns",
    "rhythm_density_hint": "higher_turn_density_candidate",
    "expressiveness_variation_hint": "higher_expressiveness_variation_candidate",
    "presence_level_hint": "lower_presence_candidate"
  }
}
```

The profile must be abstract. It must not contain raw audio paths, transcripts, sample IDs, customer data, or provider secrets.

## Runtime Behavior

If the profile is accepted and the segment is eligible freeform text:

- `higher_expressiveness_variation_candidate` can raise ElevenLabs `style` to a bounded target and slightly lower `stability`.
- `higher_turn_density_candidate` is metadata-only for now; it does not change accepted pacing.
- `lower_presence_candidate` is blocked from direct copying, so the agent does not become quieter or weaker.

If the segment is protected or ineligible, VOICE-041 is a no-op.

Current ElevenLabs bounds are intentionally subtle after VOICE-042 listening feedback:

- target `style`: `0.06`
- maximum `style`: `0.08`
- stability delta: `-0.01`

The first stronger profile was directionally useful but too loud, which made synthetic artifacts more obvious. After the softer profile was tested, baseline shaped runtime was still preferred.

Current status: experimental only. Do not enable VOICE-041 as a runtime improvement unless a later A/B listening review beats the baseline shaped runtime.

## Boundary

- No provider calls.
- No API key required.
- No customer audio upload.
- No raw private audio read.
- No transcription.
- No voice cloning.
- No generated audio.
- No `final_response` rewrite.
- No protected text rewrite.
- No accepted speed/pacing change.

## Validation

```powershell
python scripts\validate_voice_041_private_pattern_profile.py
```
