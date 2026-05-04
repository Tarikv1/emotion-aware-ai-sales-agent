#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCAL_VOICE_IDS_PATH = ROOT / "config" / "local" / "voice_ids.json"


def normalize_language(language: str | None) -> str:
    if not language:
        return "en"
    lowered = language.lower()
    if lowered.startswith("de"):
        return "de"
    return "en"


def provider_key_from_provider(provider: dict[str, Any]) -> str:
    provider_id = str(provider.get("provider_id", "")).lower()
    api_key_env = str(provider.get("api_key_env_var", "")).lower()
    provider_name = str(provider.get("provider_name", "")).lower()
    combined = " ".join([provider_id, api_key_env, provider_name])
    if "eleven" in combined:
        return "elevenlabs"
    if "cartesia" in combined:
        return "cartesia"
    return provider_id or "unknown"


def load_local_voice_ids(config_path: Path = LOCAL_VOICE_IDS_PATH) -> dict[str, Any]:
    if not config_path.is_file():
        return {}
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Local voice ID config must be a JSON object.")
    return payload


def value_if_present(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or stripped.startswith("paste-"):
        return None
    return stripped


def local_voice_id_for_provider(
    provider: dict[str, Any],
    language: str,
    config_path: Path = LOCAL_VOICE_IDS_PATH,
) -> tuple[str | None, str | None]:
    config = load_local_voice_ids(config_path)
    provider_key = provider_key_from_provider(provider)
    provider_config = config.get(provider_key)
    if not isinstance(provider_config, dict):
        return None, None

    normalized_language = normalize_language(language)
    direct_value = value_if_present(provider_config.get(normalized_language))
    if direct_value:
        return direct_value, f"local_voice_ids:{provider_key}.{normalized_language}"

    aliases = provider_config.get("aliases")
    if isinstance(aliases, dict):
        alias_key = "german_sales_voice_v1" if normalized_language == "de" else "english_sales_voice_v1"
        alias_value = value_if_present(aliases.get(alias_key))
        if alias_value:
            return alias_value, f"local_voice_ids:{provider_key}.aliases.{alias_key}"

    default_value = value_if_present(provider_config.get("default"))
    if default_value:
        return default_value, f"local_voice_ids:{provider_key}.default"

    return None, None


def local_voice_candidate_for_provider(
    provider: dict[str, Any],
    candidate_id: str,
    language: str | None = None,
    config_path: Path = LOCAL_VOICE_IDS_PATH,
) -> tuple[str | None, str | None]:
    config = load_local_voice_ids(config_path)
    provider_key = provider_key_from_provider(provider)
    provider_config = config.get(provider_key)
    if not isinstance(provider_config, dict):
        return None, None

    candidates = provider_config.get("candidates")
    if not isinstance(candidates, dict):
        return None, None

    candidate = candidates.get(candidate_id)
    voice_id = None
    candidate_language = None
    if isinstance(candidate, dict):
        voice_id = value_if_present(candidate.get("voice_id"))
        candidate_language = candidate.get("language")
    else:
        voice_id = value_if_present(candidate)

    if not voice_id:
        return None, None

    if language and candidate_language:
        if normalize_language(candidate_language) != normalize_language(language):
            return None, None

    return voice_id, f"local_voice_ids:{provider_key}.candidates.{candidate_id}"
