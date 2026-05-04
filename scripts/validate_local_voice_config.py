#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

from local_voice_config import local_voice_candidate_for_provider, local_voice_id_for_provider


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / ".tmp" / "local-voice-config-validation" / f"run-{uuid.uuid4().hex}"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    provider = {
        "provider_id": "elevenlabs-tts-stream",
        "provider_name": "ElevenLabs",
        "api_key_env_var": "ELEVENLABS_API_KEY",
    }
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        path = TMP_DIR / "voice_ids.json"
        path.write_text(
            json.dumps(
                {
                    "elevenlabs": {
                        "en": "en-local-voice-id",
                        "de": "de-local-voice-id",
                        "default": "default-local-voice-id",
                        "aliases": {
                            "english_sales_voice_v1": "en-alias-voice-id",
                            "german_sales_voice_v1": "de-alias-voice-id",
                        },
                        "candidates": {
                            "english_v1": {
                                "language": "en",
                                "label": "English v1 original",
                                "voice_id": "en-v1-candidate-voice-id",
                            },
                            "german_v2_improved": {
                                "language": "de",
                                "label": "German v2 improved",
                                "voice_id": "de-v2-candidate-voice-id",
                            },
                        },
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        en_voice, en_source = local_voice_id_for_provider(provider, "en", path)
        de_voice, de_source = local_voice_id_for_provider(provider, "de", path)
        assert_condition(en_voice == "en-local-voice-id", "English voice ID should resolve from local config.")
        assert_condition(de_voice == "de-local-voice-id", "German voice ID should resolve from local config.")
        assert_condition(en_source == "local_voice_ids:elevenlabs.en", en_source or "missing source")
        assert_condition(de_source == "local_voice_ids:elevenlabs.de", de_source or "missing source")

        candidate_voice, candidate_source = local_voice_candidate_for_provider(provider, "english_v1", "en", path)
        assert_condition(candidate_voice == "en-v1-candidate-voice-id", "Candidate voice ID should resolve from local config.")
        assert_condition(candidate_source == "local_voice_ids:elevenlabs.candidates.english_v1", candidate_source or "missing source")

        wrong_language_voice, wrong_language_source = local_voice_candidate_for_provider(provider, "english_v1", "de", path)
        assert_condition(wrong_language_voice is None, "Wrong-language candidate should not resolve.")
        assert_condition(wrong_language_source is None, "Wrong-language candidate should not report a source.")

        path.write_text(
            json.dumps({"elevenlabs": {"aliases": {"english_sales_voice_v1": "en-alias-voice-id"}}}),
            encoding="utf-8",
        )
        alias_voice, alias_source = local_voice_id_for_provider(provider, "en", path)
        assert_condition(alias_voice == "en-alias-voice-id", "Alias voice ID should resolve from local config.")
        assert_condition(alias_source == "local_voice_ids:elevenlabs.aliases.english_sales_voice_v1", alias_source or "missing source")
    finally:
        shutil.rmtree(TMP_DIR, ignore_errors=True)

    output = "Local voice config validation passed."
    assert_condition(SECRET_PATTERN.search(output) is None, "Validator output should not contain secret-like values.")
    print(output)


if __name__ == "__main__":
    main()
