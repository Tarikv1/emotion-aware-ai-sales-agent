# Collaboration Note

## Purpose

Document the planned academic collaboration between this thesis and Shehzeb Iftakhar's thesis on modular multi-modal creative expression analysis.

## Collaboration Context

The thesis supervisor has allowed the students to use compatible ideas from each other's thesis work where those ideas are relevant, with appropriate co-author credit and attribution.

This project may incorporate the concept of a modular voice-analysis layer inspired by Shehzeb Iftakhar's thesis proposal:

`Design and Development of a Modular Analytical Engine and Dataset Schema for Multi-Modal Creative Expression Analysis in Lyrics and Vocal Performance`

## What Is Being Reused Conceptually

The shared idea is not the full thesis, dataset schema, or music-analysis pipeline.

The useful transferable concept is:

- modular voice-feature extraction
- interpretable vocal/audio features
- a registry-like approach for organizing analysis modules
- structured feature outputs that can support downstream reasoning

## How This Thesis Adapts The Idea

In this sales-agent thesis, the voice-analysis concept is adapted for a different goal:

- infer customer emotional or conversational state from speech signals
- combine voice features with text and dialogue context
- support emotion-aware persuasion strategy selection
- improve response generation in sales conversations

This thesis does not analyze lyrical creativity, artist style, genre, rhyme structure, or CLVAD-style creative expression.

## Attribution Position

Shehzeb Iftakhar should be credited as a collaborator/co-author where appropriate for the shared conceptual influence around modular voice analytics.

The final thesis should clearly state that:

- the sales-agent system and research questions are distinct
- the voice-analysis concept was informed by collaborative thesis work
- the idea was adapted to the sales-dialogue and emotion-aware persuasion domain

## Development Collaboration Process

The post-May-22 development workflow also used iterative human/AI collaboration:

- Tarik supplied live-call feedback, sales-quality judgments, direction changes, and acceptance boundaries.
- Codex helped convert that feedback into scoped phase prompts, local code/doc changes, validators, and generated evidence.
- The assistant was expected to challenge assumptions, preserve provider/private-data boundaries, and avoid broad repo audits when targeted reads were enough.
- Live feedback was not copied into public thesis files as raw private transcript material; only sanitized findings and generated public-safe evidence should be cited.
- Deterministic validation is treated as engineering evidence, not a substitute for Tarik's live listening review, sales-expert review, or compliance review.
- Tarik clarified that sales-ready means active selling, objection handling, fit-based recommendation/disqualification, decision movement, and loop resistance, not only product explanation.
- Tarik made the manual qualitative judgment that Liquid TTS output was unintelligible/gibberish, which caused Liquid's retirement as a voice backend despite successful setup and synthetic smoke generation.
- Tarik made the manual qualitative judgment that Ultravox audio quality was promising for thesis/demo and fallback exploration, while latency evidence kept it out of live runtime and prevented any final ElevenLabs replacement claim.
- AI-assisted development supported prompt design, implementation planning, debugging, validator design, evidence interpretation, and documentation updates, but final project decisions and thesis claims remain Tarik's responsibility.

## Draft Wording For Thesis

`The voice-feature analysis component was informed by collaborative work with Shehzeb Iftakhar, whose thesis explores modular analysis of vocal performance and lyrical expression. In this thesis, the concept is adapted to customer speech analysis for emotion-aware sales dialogue strategy selection.`

Optional process wording:

`The implementation workflow used supervised AI-assisted development. The author provided project direction, live-call observations, review judgments, and acceptance boundaries; AI tooling assisted with local implementation, validator design, documentation planning, and evidence organization. Final interpretation and thesis claims remain the author's responsibility.`

Additional current-process wording:

`Manual live tests and listening reviews were treated as qualitative ground truth for sales and speech quality. Automated validators were used as regression and evidence-integrity tools, not as substitutes for independent evaluation or production-readiness proof.`
