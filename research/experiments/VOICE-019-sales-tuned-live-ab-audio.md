# VOICE-019 Sales-Tuned Live A/B Audio

## Question

Does the VOICE-018 professional-sales tuned input create better live audio than the previous VOICE-017-style prosody input?

VOICE-019 does not answer that yet. It creates the dry-run/live-capable A/B harness safely so the answer can be gathered through a later listening run.

## Method

The harness compares:

```text
prosody
sales_tuned
```

across:

- 2 German cases
- 2 English cases
- ElevenLabs
- Cartesia

Default execution is dry-run and no-key.

## Dry-Run Result

```text
cases: 4
German cases: 2
English cases: 2
providers: elevenlabs, cartesia
A/B variants: 16
prosody variants: 8
sales-tuned variants: 8
API calls made: 0
audio files created: 0
fallback count: 16
customer audio uploaded: false
voice cloning used: false
human ratings recorded: false
quality claim allowed: false
```

## Interpretation

The structure is ready for a live provider run, but no audio-quality claim is allowed yet.

The live listening review should compare:

- naturalness
- sales-call pacing
- pitch variation
- emotional appropriateness
- clarity
- language pronunciation
- AI-obviousness
- artifacts or muffling
- trustworthiness
- prosody vs sales-tuned preference

## Safety

The harness uses environment-only keys, redacted request previews, bounded timeouts, no customer audio upload, and no voice cloning.

Generated live audio files are ignored by Git.

## First Live ElevenLabs Run

Run date: 2026-05-04

Scope:

- provider: ElevenLabs
- cases: 2
- languages: English and German
- variants: prosody and sales-tuned
- API calls made: 4
- audio files created: 4
- fallbacks: 0
- customer audio uploaded: false
- voice cloning used: false

Latency:

- max time to first audio: 1875.891 ms
- max total provider latency: 2058.027 ms
- English sales-tuned total latency: 366.039 ms
- German sales-tuned total latency: 432.612 ms

Generated audio:

- `research/experiments/generated/VOICE-019-C01-en-elevenlabs-prosody.mp3`
- `research/experiments/generated/VOICE-019-C01-en-elevenlabs-sales_tuned.mp3`
- `research/experiments/generated/VOICE-019-C02-de-elevenlabs-prosody.mp3`
- `research/experiments/generated/VOICE-019-C02-de-elevenlabs-sales_tuned.mp3`

## Human Listening Review

Reviewer: project owner

Result:

- English preferred variant: sales-tuned
- German preferred variant: sales-tuned
- Overall preference: sales-tuned recordings are clearly better than the previous prosody variant in both languages

Positive finding:

- the sales-tuned versions sound much better for both English and German
- after the phrase "the important thing is" the English sample becomes more natural than the beginning
- the sales-tuned variants also showed much lower total provider latency in this run

Remaining problems:

- the beginning still feels rigid and can trigger an immediate "this is a robot" reaction
- spacing and word voicing still need more controlled randomness
- the agent still sounds like it is reading from prepared text
- emotional expressiveness is not strong enough yet
- the speech still needs some controlled filler words, abbreviations, pauses, contractions, and more human conversational texture

Interpretation:

Sales-tuned is the preferred direction, but the voice layer is not production-ready. The next checkpoint should not go back to generic provider comparison yet. It should focus on emotional delivery, less rigid openings, controlled randomness, and campaign-safe natural speech features while preserving protected campaign questions, compliance statements, and guardrails.

Quality claim:

- allowed claim: in this two-case owner review, sales-tuned was preferred over prosody for both English and German
- not allowed yet: the agent voice sounds human enough for real leads
- not allowed yet: the voice quality is production-ready
- not allowed yet: sales-tuned is universally better across providers, voices, or campaigns
