# VOICE-020 ElevenLabs Voice Design

## Purpose

VOICE-020 turns the latest listening feedback into an ElevenLabs-first voice design packet.

It does not create audio, call a provider, upload private audio, or clone any voice. It prepares the next ElevenLabs dashboard/API work by defining:

- English and German sales-agent voice prompts
- ElevenLabs Voice Design UI candidates for loudness and guidance scale
- ElevenLabs Voice Remixing prompts for provider-side naturalization
- settings candidates for realtime and quality tests
- bundled emotional delivery gestures
- protected-text rules for campaign questions, disclosures, handoff, and hang-up lines
- the private call-center boundary for future local-only tuning notes

## Source Basis

VOICE-020 uses:

- `VOICE-018` sales-tuned delivery metadata
- `VOICE-019` live ElevenLabs listening feedback
- official ElevenLabs docs on voices, Voice Design, TTS best practices, settings, privacy, and commercial use
- the project rule that private call-center audio may only inform local abstract tuning notes unless a later reviewed workflow says otherwise

## Current Design Decision

The next live voice step should not be "try random voices until one sounds nice."

The better path is:

1. Create/select English and German ElevenLabs voice candidates from explicit sales-agent prompts.
2. Use Voice Design UI candidates for loudness and guidance scale.
3. Avoid telephone-filtered, muffled, distant, compressed, or low-bandwidth voice quality.
4. Remix the selected English and German voices with the `VOICE-020` remix prompts.
5. Bias the voice and runtime settings faster than normal because slow speech is hurting sales usefulness.
6. Test four runtime settings candidates: `realtime-balanced`, `emotional-opening`, `clarity-safe`, and `expressive-quality`.
7. Listen separately for opening naturalness, objection handling, protected-text clarity, latency, and AI-obviousness.
8. Promote a voice only after both English and German samples pass human listening review.

## Voice Design Profiles

VOICE-020 defines:

- `elevenlabs-sales-agent-en-v1`
- `elevenlabs-sales-agent-de-v1`

Both target a trained professional sales consultant, not a narrator, announcer, generic assistant, or scripted telemarketer.

Both prompts now explicitly request clean full-band voice quality and avoid phone-filtered/muffled output.

## Voice Design UI Candidates

VOICE-020 records three UI candidates for ElevenLabs Voice Design:

- `clean-natural-medium-guidance`: default attempt, balanced prompt following and natural variation.
- `creative-less-robotic`: lower guidance scale when generated voices sound too robotic.
- `prompt-faithful-clean-sales`: higher guidance scale when generated voices drift away from the sales-agent persona.

The UI fields are separate from runtime TTS settings:

- `loudness` controls generated voice volume level.
- `guidance_scale` controls how tightly the generated voice follows the prompt.

## Voice Remixing Prompts

VOICE-020 includes two extensive remix prompts:

- `elevenlabs-remix-en-sales-naturalizer-v1`
- `elevenlabs-remix-de-sales-naturalizer-v1`

Use `Medium` prompt strength first. If the result is still too subtle, try `High`. Avoid `Max` unless we intentionally want a much different voice.

The prompts target:

- less robotic and less scripted delivery
- cleaner full-band audio instead of phone-filtered or muffled sound
- phrase-to-phrase pacing variation
- faster confident explanations
- slower empathy and important-point moments
- bundled microtexture, such as filler plus slight upward pitch plus short pause
- professional sales confidence without theatrical, pushy, seductive, or announcer-like tone

The prompts also include custom English and German remix scripts so the provider hears the exact kind of opening, objection handling, pause texture, and sales rhythm we care about.

## Settings Candidates

- `realtime-balanced`: first default for live sales-call testing.
- `emotional-opening`: stronger expressiveness for openings and objection handling.
- `clarity-safe`: steadier delivery for protected or compliance-adjacent speech.
- `expressive-quality`: quality exploration when latency is less important; not the default realtime path.

Runtime speed now biases faster than the previous `VOICE-020` draft because the Voice Design previews sounded too slow for sales use.

## Emotional Delivery Bundles

VOICE-020 treats human-like voice behavior as bundled gestures, not isolated toggles.

Examples:

- warm opening plus brief pause plus faster follow-through
- empathy acknowledgement plus short pause plus confident explanation
- rare thinking filler plus slight pitch lift plus resumed emphasis
- keyword emphasis plus spacing change plus return to faster sales pace
- respectful exit with no persuasion escalation

## Protected Text

Protected text remains locked:

- campaign qualification questions
- company-provided scripts
- required disclosures
- legal, medical, coverage, claim, or payout boundaries
- appointment confirmations
- do-not-call and hang-up lines
- sensitive escalation and human handoff scripts

No fillers, contractions, random spacing, or emotional overrides are allowed inside protected text by default.

## Private Call-Center Boundary

Private call-center audio may later inform local abstract tuning notes, such as:

- opening warmth
- objection rhythm
- common pause patterns
- pace preferences
- emotional contour

It must not be uploaded to ElevenLabs, copied into generated artifacts, used as a customer voice, or used for voice cloning.

## Commands

Run:

```powershell
python scripts\run_voice_020_elevenlabs_voice_design.py
```

Validate:

```powershell
python scripts\validate_voice_020_elevenlabs_voice_design.py
```

Optional local voice IDs for later live tests:

```powershell
Copy-Item runtime\config\local\voice_ids.example.json runtime\config\local\voice_ids.json
```

Then put the selected English and German ElevenLabs voice IDs into `config\local\voice_ids.json`. This file is ignored by Git.

## Generated Artifacts

- `research/experiments/cases/voice-020-elevenlabs-voice-design.json`
- `research/experiments/generated/VOICE-020/VOICE-020-elevenlabs-voice-design.json`
- `research/experiments/generated/VOICE-020/VOICE-020-elevenlabs-voice-design-report.md`

## Product Meaning

VOICE-020 makes voice quality part of the product architecture instead of a provider-side afterthought.

The reusable sales-agent core still controls what should be said and which text is protected. ElevenLabs only receives synthetic agent speech and voice-design prompts for controlled TTS delivery testing.
