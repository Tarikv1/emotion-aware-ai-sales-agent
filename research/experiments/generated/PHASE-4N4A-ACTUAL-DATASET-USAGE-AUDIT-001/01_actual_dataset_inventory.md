# Actual Dataset Inventory

| Source | Classification | Repo evidence | What can be claimed | What cannot be claimed |
| --- | --- | --- | --- | --- |
| MELD | actual_public_dataset_downloaded_extracted | `docs/data/DATASETS.md`, `docs/data/MELD_LABEL_MAPPING.md`, `data/public/meld/` | Downloaded/extracted locally; train file inspected with 9,989 train rows; observed `Emotion` labels are neutral, joy, surprise, anger, sadness, disgust, fear; observed `Sentiment` labels are positive, neutral, negative. | It supports emotion/sentiment grounding, not proof of real sales-call emotion performance. |
| Persuasion for Good | actual_public_dataset_downloaded_extracted | `docs/data/DATASETS.md`, `data/public/persuasion-for-good/`, `docs/thesis/THESIS_REFERENCE_REGISTRY.md` | Downloaded/extracted locally; supports persuasion strategy grounding and success/failure pattern analysis; annotated subset documentation indicates persuasion labels and sentiment fields for 300 annotated dialogs. | It is charity persuasion, not commercial outbound sales; do not claim direct website-sales effectiveness from it. |
| IEMOCAP | actual_public_dataset_partial_or_unverified | `docs/data/DATASETS.md`, `docs/data/DATA_READINESS.md`, `docs/thesis/THESIS_REFERENCE_REGISTRY.md`, `data/public/iemocap/archive.zip` | A local CSV-style export/archive exists and may support schema/label inspection after provenance review. | Do not claim official IEMOCAP audio-corpus experiments or full official corpus use without provenance verification. |
| Official IEMOCAP full audio-corpus experiments | planned_not_used | Same IEMOCAP evidence as above | Future candidate if official corpus layout/access is verified. | Not relied on for current official audio-emotion results. |

## Evidence Notes

MELD and Persuasion for Good are the only inspected public sources that the repo currently documents as downloaded and extracted. IEMOCAP has a local artifact, but the repo explicitly warns that it appears to be a partial or unofficial CSV-style export rather than the official corpus layout.
