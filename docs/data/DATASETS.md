# Dataset Manifest

This file tracks the public datasets currently stored under `data/public/` and how they should be used in the thesis project.

## Current local datasets

### IEMOCAP

- Local path: `data/public/iemocap/`
- Source candidates:
  - official IEMOCAP information: https://sail.usc.edu/iemocap/iemocap_info.htm
  - USC SAIL database page: https://sail.usc.edu/software/databases/
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
- Source candidates:
  - project page: https://affective-meld.github.io/
  - GitHub: https://github.com/declare-lab/MELD
  - paper summary: https://huggingface.co/papers/1810.02508
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
- Source candidates:
  - ACL Anthology paper: https://aclanthology.org/P19-1566/
  - ConvoKit corpus page: https://convokit.cornell.edu/documentation/persuasionforgood.html
  - GitHub: https://github.com/ohyj1002/persuasionforgood
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

## Candidate Speech-Realism References

These are not local training datasets yet. They are reference sources for future English/German speech-naturalness design and thesis related work.

### Spoken BNC2014

- Source: https://corpora.lancs.ac.uk/bnc2014/
- Role: contemporary spoken English reference for discourse markers, contractions, informal rhythm, and spoken conversation patterns
- Status: candidate reference only; access and usage terms must be reviewed before local use

### DGD / FOLK

- Source: https://dgd.ids-mannheim.de/DGD2Web/jsp/Welcome.jsp
- Role: spoken German reference for spontaneous interaction, fillers, backchannels, and turn-taking patterns
- Status: candidate reference only; DGD registration and usage terms must be reviewed before local use

### Speech-realism literature notes

- Local thesis note: `docs/thesis/SPEECH_REALISM_REFERENCES.md`
- Role: bibliography and engineering implications for `VOICE-023`

## Central Reference Registry

Use `docs/thesis/THESIS_REFERENCE_REGISTRY.md` as the broader source map for:

- public datasets
- speech-realism literature
- privacy/data-governance sources
- TTS provider documentation
- sales-objection product sources
- open-source inspiration and attribution notes

## Storage rule

Keep raw downloaded archives and extracted raw dataset folders under `data/public/`.
Keep cleaned subsets, remapped labels, and derived tables under `data/processed/`.
