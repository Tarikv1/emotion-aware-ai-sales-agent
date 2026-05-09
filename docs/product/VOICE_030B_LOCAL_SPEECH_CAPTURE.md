# VOICE-030B Local Speech Capture

VOICE-030B creates an explicit local-only place for Tarik speech samples instead of relying on hidden Codex, ChatGPT, browser, or Windows app caches.

## Purpose

- Capture new microphone samples through a localhost browser page.
- Encode browser microphone samples to WAV locally before upload.
- Import existing audio files into the same private raw-audio folder.
- Trigger the VOICE-030C private learning queue after each save.
- Store only under `data/private/tarik-speech-samples/raw-audio`.
- Keep a private manifest under `data/private/tarik-speech-samples/derived/local-speech-capture-manifest.jsonl`.

## Commands

Start the local browser recorder:

```powershell
python scripts\run_voice_030b_local_speech_capture.py --serve
```

Then open:

```text
http://127.0.0.1:8791/
```

Import an existing audio file:

```powershell
python scripts\run_voice_030b_local_speech_capture.py `
  --import-file "<local-speech-sample.wav>" `
  --language en `
  --label "tarik local speech sample"
```

Validate the capture/import boundary:

```powershell
python scripts\validate_voice_030b_local_speech_capture.py
```

## Privacy Boundary

- No provider calls.
- No transcription.
- No voice cloning.
- No runtime profile application.
- No public generated artifact.
- Recorder binds to `127.0.0.1`.
- Audio bytes and manifest records stay under `data/private/`, which is ignored by Git.
- Browser recordings are saved as WAV by default.
- The automatic learning hook writes only private derived queue/features under `data/private/`.

## Relationship To VOICE-030A

VOICE-030B stores private samples. VOICE-030A can then analyze WAV samples locally:

```powershell
python scripts\run_voice_030_raw_audio_reader.py `
  --input-dir data\private\tarik-speech-samples\raw-audio `
  --allow-private-read
```

VOICE-030A is currently WAV-only. New browser recordings are encoded as WAV before upload so they can be analyzed by VOICE-030A. Manually imported MP3, M4A, AAC, OGG, FLAC, or WebM files still need a later reviewed local conversion or local ASR step before acoustic feature extraction.

VOICE-030C is the automatic private hook that queues each saved sample and analyzes WAV files locally without changing runtime settings.
