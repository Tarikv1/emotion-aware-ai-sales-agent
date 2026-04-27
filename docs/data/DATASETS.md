# Dataset Manifest

This file tracks the public datasets currently stored under `data/public/` and how they should be used in the thesis project.

## Current local datasets

### IEMOCAP

- Local path: `data/public/iemocap/`
- Current local file: `archive.zip`
- Current local contents: `iemocap_full_dataset.csv`
- Current status: partial or unofficial local export, not the official corpus layout
- Planned role: early inspection of emotion labels and schema only, until the official dataset status is confirmed
- Risks:
  - may not include the full original audio corpus
  - may reflect a repackaged derivative rather than the canonical release
  - may not be suitable for audio-based experiments

### MELD

- Local path: `data/public/meld/`
- Current local files:
  - `MELD-master.zip`
  - extracted `MELD-master/`
- Current status: downloaded and extracted
- Notable local training file: `data/MELD/train_sent_emo.csv`
- Notable label situation:
  - column set includes `Utterance`, `Speaker`, `Emotion`, `Sentiment`, dialogue ids, and timing fields
  - local train split has 9,989 rows
  - emotion distribution is heavily skewed toward `neutral`
- Planned role:
  - conversation-level emotion analysis
  - label mapping experiments
  - text-aware and multimodal baseline work

### Persuasion for Good

- Local path: `data/public/persuasion-for-good/`
- Current local files:
  - `persuasionforgood-master.zip`
  - extracted `persuasionforgood-master/`
- Current status: downloaded and extracted
- Notable local contents:
  - `data/FullData/full_dialog.csv`
  - `data/FullData/full_info.csv`
  - annotated subset metadata in `data/AnnotatedData/`
- Notable label situation:
  - full dataset has dialogue, role, turn, and utterance-unit structure
  - annotated subset documentation indicates persuasion labels and sentiment fields exist for 300 annotated dialogs
- Planned role:
  - persuasion strategy taxonomy
  - success/failure dialogue analysis
  - first-pass mapping from emotion to strategy

## Working decision

For now:

- treat `MELD` and `Persuasion for Good` as ready for structured inspection
- treat `IEMOCAP` as pending verification before relying on it for audio experiments

## Next checks

For each dataset, confirm:

- source URL or repository
- license and access conditions
- actual files available locally
- core labels
- whether it supports training, analysis, or only schema design

## Storage rule

Keep raw downloaded archives and extracted raw dataset folders under `data/public/`.
Keep cleaned subsets, remapped labels, and derived tables under `data/processed/`.
