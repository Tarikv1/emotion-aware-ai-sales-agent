# VOICE-020 ElevenLabs Voice Design

## Design

`VOICE-020` is an offline provider-aware design checkpoint. It converts `VOICE-019` listening feedback into a concrete ElevenLabs voice-design packet before any new live provider test.

## Scope

Included:

- English and German voice-design prompts
- ElevenLabs Voice Design UI candidates for loudness and guidance scale
- ElevenLabs Voice Remixing prompts for provider-side naturalization
- ElevenLabs settings candidates
- emotional delivery bundles
- protected-text locks
- private call-center boundary notes
- ignored local voice-ID config support
- validator and generated research packet

Excluded:

- live API calls
- audio generation
- voice cloning
- private call-center audio upload
- provider SDK changes

## Success Criteria

- Default run is local and no-key.
- Output is deterministic.
- English and German profiles are both present.
- Voice Design UI candidates cover cleaner natural generation, less-robotic generation, and more prompt-faithful generation.
- Voice Remixing prompts cover English and German naturalization for pacing, emotion, pitch, audio quality, and bundled microtexture.
- Settings candidates cover realtime, emotional opening, clarity-safe, and quality exploration modes.
- All emotional gesture bundles are blocked inside protected text.
- Private call-center audio is treated only as future local abstract tuning signal.
- Local voice IDs can be read from ignored config without logging raw values; API keys remain environment-only.

## Review Gate

The next live step may create or select voices inside ElevenLabs using only synthetic preview text and the prompts from this checkpoint.
