# VOICE-023 Speech Realism Layer

## Purpose

VOICE-023 should make eligible freeform agent speech sound more human in English and German without corrupting campaign-protected text.

This is the product and engineering companion to `docs/thesis/SPEECH_REALISM_REFERENCES.md`.

## Product Rule

Model speech mechanics, not stereotypes.

The campaign controls persona, product category, formality, claims, disclosures, and escalation rules. The speech-realism layer only controls bounded timing, filler, pause, warmth, and rhythm behavior for eligible freeform segments.

## Eligible Text

Allowed segment types:

- freeform empathy
- freeform objection handling
- freeform clarification
- freeform transition
- freeform explanation
- bridge response when lookup or scheduling takes longer

Protected segment types:

- exact campaign qualification questions
- company-provided scripts
- required disclosures
- compliance statements
- legal, medical, coverage, payout, savings, or guarantee boundaries
- appointment date and time confirmations
- human handoff lines
- do-not-call confirmations
- hang-up lines

Protected text remains exact.

## English Speech Profile

Candidate markers:

- `uh`
- `um`
- `so`
- `well`
- `right`
- `okay`
- `I mean`

Recommended behavior:

- `uh`: rare minor planning delay
- `um`: rarer longer planning delay
- `well`: soft reframing or disagreement
- `so`: transition into next point
- `right` / `okay`: acknowledgment before answering
- contractions: normal spoken form when text is not protected

Avoid:

- too many fillers
- casualness that sounds unserious
- influencer, radio, or podcast style
- American or British stereotype unless a campaign explicitly asks for that accent/persona

## German Speech Profile

Candidate markers:

- `äh`
- `ähm`
- `hm`
- `ja`
- `genau`
- `also`
- `okay`

Implementation note:

- VOICE-025 now allows provider-facing `äh` and `ähm` in eligible freeform text, with validation coverage and a follow-up live-listening question for ElevenLabs rendering quality.

Recommended behavior:

- `äh`: rare minor planning delay
- `ähm`: rarer longer planning delay
- `hm`: consideration or soft acknowledgment
- `ja`: acknowledgment or alignment
- `genau`: confirmation or agreement
- `also`: turn-boundary transition or framing before explanation

Avoid:

- copying English `uh` / `um` behavior into German
- making German speech sound like a caricature
- overusing `ja` or `genau`
- adding fillers inside insurance or compliance boundaries

## Shared Human-Realism Cues

Candidate cues:

- variable short pauses
- occasional longer thinking pauses
- subtle breath marks before a new phrase
- slight end-of-phrase lengthening when thinking
- mild smile or warmth cue in friendly turns
- small self-repair only when safe
- no perfect metronomic pacing

## Combination Rules

Use bundled gestures, not isolated effects.

Good bundles:

- short filler plus slight upward pitch plus short pause
- empathy phrase plus softer tone plus slower phrase ending
- important keyword plus brief emphasis plus faster follow-through
- thinking pause plus small repair plus direct answer
- warm smile cue plus confident next step

Bad bundles:

- filler after every sentence
- pause plus filler plus pitch change every time
- dramatic emotional swings
- fake laughter in sales-sensitive contexts
- breath noises that sound unhealthy, seductive, or theatrical

## Frequency Limits

Default limits for a normal response:

- maximum one filler in a short response
- maximum two fillers in a long freeform response
- no filler in protected text
- no filler if the customer is angry or asked to stop
- no filler if the agent is stating a compliance boundary

Randomness must be bounded and seeded for repeatable tests.

## Evaluation Rubric

VOICE-023 should be rated on:

- naturalness
- trust
- professionalism
- emotional fit
- language fit
- protected-text clarity
- no-overacting risk
- sales usefulness
- latency impact

The output should not claim "human-like" as a success condition until listening review supports it.

## Reference Basis

Primary reference note:

- `docs/thesis/SPEECH_REALISM_REFERENCES.md`

Related voice checkpoints:

- `VOICE-012`: mid-utterance filler and protected-text lock
- `VOICE-015`: provider-neutral prosody cues
- `VOICE-016`: provider-specific rendering
- `VOICE-018`: sales-tuned voice behavior
- `VOICE-020`: ElevenLabs voice design and remixing
- `VOICE-021`: custom voice comparison
- `VOICE-022`: spoken text normalization

Implementation artifacts:

- `scripts/speech_realism.py`
- `scripts/run_voice_023_speech_realism.py`
- `scripts/validate_voice_023_speech_realism.py`
- `research/experiments/cases/voice-023-speech-realism.json`
- `research/experiments/generated/VOICE-023/VOICE-023-speech-realism.json`
- `research/experiments/generated/VOICE-023/VOICE-023-speech-realism-report.md`

Runtime position:

- `RESP-002` applies VOICE-023 after VOICE-022 spoken-text normalization and before VOICE-026 interaction prosody plus VOICE-015/016 prosody/provider rendering.
- `final_response`, call control, selected strategy, and protected segment text remain unchanged.
- VOICE-025 refines this layer with boundary-aware placement and allows German `äh`/`ähm` in eligible freeform text while keeping protected campaign text exact.
- VOICE-026 separates listener backchannels, lookup acknowledgements, and sales-pace cues from speaker fillers.

## Product Meaning

VOICE-023 should make the agent sound more live and responsive while preserving the core product architecture:

```text
reusable sales-agent core
  -> SalesCampaign profile
  -> guarded response
  -> protected/freeform segmentation
  -> speech realism only on eligible freeform segments
  -> interaction prosody only on eligible freeform segments
  -> TTS provider adapter
```
