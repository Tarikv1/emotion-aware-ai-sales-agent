# VOICE-033 Private Speech Sample Readiness

VOICE-033 answers one practical question:

```text
Are there enough usable private speech samples to run VOICE-030D?
```

It reads only private metadata and directory entries. It does not read raw audio content.

## What It Counts

- WAV files available
- analyzed VOICE-030C feature JSON files
- WAV files that may still need analysis
- WhatsApp `.ogg` files waiting for VOICE-032 conversion
- WebM or other non-WAV files still needing conversion
- queue records by status
- conversion records by status
- language counts
- source counts

## Readiness Status

VOICE-033 reports one of:

- `not_enough_samples_yet`
- `enough_for_first_review`
- `enough_for_stronger_pattern_review`

Current thresholds:

- first review: `10` analyzed samples
- stronger pattern review: `100` analyzed samples
- best-case target: `150` samples

## Command

```powershell
python scripts\run_voice_033_private_sample_readiness.py --allow-private-metadata-read
```

The flag is required because file names, counts, and private manifests are still private metadata.

Private outputs are written to:

```text
data\private\tarik-speech-samples\derived\readiness\
```

## Boundary

- No raw audio content read.
- No transcription.
- No provider calls.
- No voice cloning.
- No runtime profile application.
- No public generated artifact.
- Aggregate counts only.
- Human review required before runtime use.

## Validation

```powershell
python scripts\validate_voice_033_private_sample_readiness.py
```
