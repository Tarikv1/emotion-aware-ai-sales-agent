# 4N4A Actual Dataset Usage Audit Report

## Outcome

Created a repo-grounded correction package for dataset provenance and thesis alignment. The correction is necessary because the project contains external public datasets, inspected or partial datasets, source bundles, synthetic/sanitized generated datasets, evaluation case packs, and thesis placeholders.

## Main Correction

EASID is schema work, not proof that an external EASID corpus was used. MELD and Persuasion for Good are the public datasets with local downloaded/extracted evidence. IEMOCAP remains partial or unverified for official audio-corpus use.

## Counts

- Dataset inventory entries: 13
- Actual public datasets downloaded/extracted: 2
- Project-generated dataset/evaluation artifacts counted: 5
- Reference-only or claim-governance sources counted: 2
- EASID actual dataset used: false
- EASID schema defined: true
- Thesis data section ready: true

## Metric Boundary

Emotion detection accuracy/F1, website-sales effectiveness scores, human-likeness scores, and ElevenLabs website-sales latency are not computed in the inspected 4N3/4N4 evidence. Existing row/split/stat counts are recorded only where repo result files provide them.

## Safety Boundary

No fabricated results were added. No private transcripts/audio were used. No provider calls, ElevenLabs calls, OpenAI API calls, model calls, TTS calls, CRM/email/calendar/payment/account actions, live outbound calls, or live-readiness claims were introduced by this checkpoint.
