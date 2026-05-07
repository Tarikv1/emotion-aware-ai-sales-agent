# VOICE-032 Local Audio Conversion

VOICE-032 converts selected local WhatsApp `.ogg` voice notes to WAV so the existing private VOICE-030C queue can analyze them.

This is local-only. It does not upload audio, transcribe audio, clone a voice, call a provider, or change runtime voice behavior.

## WhatsApp Drop Folder

Put exported WhatsApp `.ogg` voice notes here:

```text
data\private\tarik-speech-samples\whatsapp-voice-notes\
```

That folder is ignored by Git because it lives under `data/private/`.

Converted WAV files are written here:

```text
data\private\tarik-speech-samples\converted-audio\
```

The private conversion manifest/report live under:

```text
data\private\tarik-speech-samples\derived\
```

## Why OGG First

Tarik checked WhatsApp exports and confirmed voice recordings are saved as `.ogg`.

VOICE-032 therefore treats `.ogg` as the first-class conversion source. Other formats are deferred so the pipeline stays simple, reviewable, and aligned with the immediate need.

## Command

```powershell
python scripts\run_voice_032_local_audio_conversion.py
```

If `ffmpeg` is not available, the script records:

```text
converter_missing_needs_local_ffmpeg
```

It does not fail silently.

## After Conversion

Successful `.ogg` conversions are written as mono 16 kHz WAV files and passed into VOICE-030C.

VOICE-030C then writes private feature files under:

```text
data\private\tarik-speech-samples\derived\audio-features\
```

No runtime voice setting is applied automatically.

## Boundary

- Input directory must stay under `data/private/`.
- Converted WAV directory must stay under `data/private/`.
- No provider calls.
- No transcription.
- No voice cloning.
- No runtime profile application.
- No public generated artifact from private audio.
- Human review is required before anything influences runtime behavior.

## Validation

```powershell
python scripts\validate_voice_032_local_audio_conversion.py
```
