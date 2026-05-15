#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.config.local_voice_config import LOCAL_VOICE_IDS_PATH, load_local_voice_ids, local_voice_candidate_for_provider, local_voice_id_for_provider


TMP_DIR = ROOT / ".tmp" / "local-voice-config-validation" / f"run-{uuid.uuid4().hex}"

SECRET_PATTERN = re.compile(
    r"(sk_car_[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9_-]{20,}|ELEVENLABS_API_KEY\s*=\s*[^\s]+|xi-api-key\s*[:=]\s*[A-Za-z0-9])"
)


def assert_condition(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_project_local_config(provider: dict) -> None:
    if not LOCAL_VOICE_IDS_PATH.exists():
        return
    try:
        load_local_voice_ids(LOCAL_VOICE_IDS_PATH)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            "Project local voice config is invalid JSON. "
            f"Check {LOCAL_VOICE_IDS_PATH.relative_to(ROOT)} near line {exc.lineno}, column {exc.colno}. "
            "Common cause: a trailing comma after the last field in an object."
        ) from exc

    for language in ("en", "de"):
        voice_id, source = local_voice_id_for_provider(provider, language, LOCAL_VOICE_IDS_PATH)
        assert_condition(
            voice_id is not None and source is not None,
            f"Project local voice config is missing a usable ElevenLabs {language} voice ID.",
        )


def main() -> None:
    provider = {
        "provider_id": "elevenlabs-tts-stream",
        "provider_name": "ElevenLabs",
        "api_key_env_var": "ELEVENLABS_API_KEY",
    }
    validate_project_local_config(provider)
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

        bom_path = TMP_DIR / "voice_ids_bom.json"
        bom_path.write_text(
            json.dumps({"elevenlabs": {"en": "en-bom-local-voice-id"}}),
            encoding="utf-8-sig",
        )
        bom_voice, bom_source = local_voice_id_for_provider(provider, "en", bom_path)
        assert_condition(bom_voice == "en-bom-local-voice-id", "UTF-8 BOM local config should resolve.")
        assert_condition(bom_source == "local_voice_ids:elevenlabs.en", bom_source or "missing source")
    finally:
        shutil.rmtree(TMP_DIR, ignore_errors=True)

    output = "Local voice config validation passed."
    assert_condition(SECRET_PATTERN.search(output) is None, "Validator output should not contain secret-like values.")
    print(output)


if __name__ == "__main__":
    main()
