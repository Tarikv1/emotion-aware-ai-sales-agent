from __future__ import annotations

from non_llm_action_selector_artifact_checks_001 import (
    RUNTIME_ACTION_METADATA_CONTRACT_PATH,
    RUNTIME_ACTION_METADATA_EXTRACTOR_PATH,
    RUNTIME_METADATA_DISCOVERY_DIR,
    RUNTIME_TO_ACTION_LABEL_MAP_PATH,
    forbidden_import_failures,
    read_json,
    tracked_weight_failures,
    write_status,
)


def main() -> int:
    failures: list[str] = []
    for path in [
        RUNTIME_METADATA_DISCOVERY_DIR / "result.json",
        RUNTIME_METADATA_DISCOVERY_DIR / "report.md",
        RUNTIME_ACTION_METADATA_CONTRACT_PATH,
        RUNTIME_TO_ACTION_LABEL_MAP_PATH,
        RUNTIME_ACTION_METADATA_EXTRACTOR_PATH,
    ]:
        if not path.is_file():
            failures.append(f"missing required artifact: {path}")

    result = read_json(RUNTIME_METADATA_DISCOVERY_DIR / "result.json")
    if result:
        if result.get("status") != "pass":
            failures.append(f"discovery status is not pass: {result.get('status')}")
        sources = result.get("discovered_metadata_sources")
        if not isinstance(sources, list) or not sources:
            failures.append("discovery missing discovered_metadata_sources")
        if not result.get("proposed_metadata_extraction_source"):
            failures.append("discovery missing proposed_metadata_extraction_source")
        if not result.get("recommended_mapping_approach"):
            failures.append("discovery missing recommended_mapping_approach")
        if result.get("runtime_behavior_changed") is not False:
            failures.append("discovery runtime_behavior_changed must be false")
        if result.get("response_text_changed") is not False:
            failures.append("discovery response_text_changed must be false")

    mapping = read_json(RUNTIME_TO_ACTION_LABEL_MAP_PATH)
    if mapping:
        entries = mapping.get("mappings")
        if not isinstance(entries, list) or not entries:
            failures.append("runtime_to_action_label_map missing mappings")
        else:
            for index, entry in enumerate(entries, start=1):
                for key in ("runtime_signal_fields", "required_conditions", "selector_action_id", "confidence", "notes", "forbidden_when"):
                    if key not in entry:
                        failures.append(f"mapping[{index}] missing {key}")

    failures.extend(forbidden_import_failures())
    failures.extend(tracked_weight_failures())
    return write_status("validate_runtime_action_metadata_discovery_001", failures)


if __name__ == "__main__":
    raise SystemExit(main())
