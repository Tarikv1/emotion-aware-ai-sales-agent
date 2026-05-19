from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit, urlunsplit


DEFAULT_REASONER_TEMPERATURE = 1.0


@dataclass(frozen=True)
class OpenAICompatibleReasonerConfig:
    base_url: str | None
    model: str | None
    api_key: str | None
    timeout_seconds: float = 12.0
    temperature: float = DEFAULT_REASONER_TEMPERATURE
    use_json_response_format: bool = True


def missing_provider_config(config: OpenAICompatibleReasonerConfig) -> list[str]:
    missing = []
    if not config.api_key:
        missing.append("api_key")
    if not config.base_url:
        missing.append("base_url")
    if not config.model:
        missing.append("model")
    return missing


def redacted_provider_config(config: OpenAICompatibleReasonerConfig) -> dict[str, Any]:
    return {
        "base_url_configured": bool(config.base_url),
        "model_configured": bool(config.model),
        "api_key_configured": bool(config.api_key),
        "api_key_value_logged": False,
        "timeout_seconds": config.timeout_seconds,
        "temperature": config.temperature,
        "use_json_response_format": config.use_json_response_format,
    }


def normalize_chat_completions_url(base_url: str) -> str:
    stripped = base_url.strip().rstrip("/")
    parsed = urlsplit(stripped)
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        normalized_path = path
    elif path.endswith("/v1"):
        normalized_path = path + "/chat/completions"
    elif not path:
        normalized_path = "/v1/chat/completions"
    else:
        normalized_path = path + "/chat/completions"
    return urlunsplit((parsed.scheme, parsed.netloc, normalized_path, "", ""))


def build_chat_completions_payload(config: OpenAICompatibleReasonerConfig, prompt: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Return only strict JSON. Do not include markdown. "
                    "Do not write customer-facing sales copy."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": config.temperature,
    }
    if config.use_json_response_format:
        payload["response_format"] = {"type": "json_object"}
    return payload


def parse_chat_completion_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise ValueError("Provider response had no choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Provider response content was empty")
    return content


def call_openai_compatible_reasoner(config: OpenAICompatibleReasonerConfig, prompt: str) -> dict[str, Any]:
    missing = missing_provider_config(config)
    if missing:
        raise ValueError(f"Missing provider config: {', '.join(missing)}")
    started = time.perf_counter()
    body = json.dumps(build_chat_completions_payload(config, prompt), ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        normalize_chat_completions_url(str(config.base_url)),
        data=body,
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
            response_payload = json.loads(response_body)
            content = parse_chat_completion_content(response_payload)
            return {
                "provider_calls_made": True,
                "text_sent_to_provider": True,
                "api_key_value_logged": False,
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "http_status": getattr(response, "status", None),
                "content": content,
                "usage": response_payload.get("usage") or {},
                "raw_response_stored": False,
            }
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")[:600]
        return {
            "provider_calls_made": True,
            "text_sent_to_provider": True,
            "api_key_value_logged": False,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "http_status": exc.code,
            "error": f"HTTP {exc.code}: {error_text}",
            "raw_response_stored": False,
        }
    except Exception as exc:
        return {
            "provider_calls_made": True,
            "text_sent_to_provider": True,
            "api_key_value_logged": False,
            "latency_ms": round((time.perf_counter() - started) * 1000, 3),
            "http_status": None,
            "error": str(exc),
            "raw_response_stored": False,
        }
