#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-048A-native-german-review-html-packet"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

SOURCE_GERMAN_FINDINGS = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046-core-sales-policy-human-review"
    / "german_response_quality_findings.json"
)
SOURCE_PROD_046_RESULT = (
    ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json"
)
SOURCE_PROD_047_RESULT = (
    ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json"
)

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_048a_native_german_review_html_packet.py",
    "runner": ROOT / "scripts" / "run_prod_048a_native_german_review_html_packet.py",
    "validator": ROOT / "scripts" / "validate_prod_048a_native_german_review_html_packet.py",
    "doc": ROOT / "docs" / "product" / "PROD_048A_NATIVE_GERMAN_REVIEW_HTML_PACKET.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "packet": OUT_DIR / "native_german_review_packet.json",
    "html": OUT_DIR / "native_german_review.html",
    "schema": OUT_DIR / "native_german_review_export_schema.json",
    "readme_de": OUT_DIR / "native_german_review_readme_de.md",
    "table_csv": OUT_DIR / "native_german_review_table.csv",
}

REQUIRED_RATING_FIELD_IDS = {
    "natuerlich",
    "klar_verstaendlich",
    "freundlich",
    "gesprochene_sprache",
    "zu_abrupt",
    "intern_buerokratisch_technisch",
    "telefonisch_akzeptabel",
    "ueberarbeitung_noetig",
}

REQUIRED_SAFETY_FLAGS = {
    "zu_draengend",
    "verkaufsdruck",
    "rechtlich_unsicher",
    "medizinische_beratung",
    "versicherungsschutz_beratung",
    "zahlungsaufforderung",
    "vertragsabschluss",
    "unhoeflich",
    "unklar",
    "sonstiges",
}

BOUNDARY_FALSE_FIELDS = [
    "native_german_approval_claimed",
    "legal_compliance_claimed",
    "runtime_behavior_changed",
    "retrieval_enabled",
    "provider_calls_made",
    "llm_used",
    "private_data_read",
    "voice_playback_unblocked",
    "public_demo_polish_unblocked",
    "payment_collection_allowed",
    "contract_signing_allowed",
    "production_runtime_promotion_allowed",
]

VISIBLE_TECHNICAL_TERMS = [
    "sales_difficulty",
    "call_control",
    "runtime",
    "checkpoint",
    "regression",
    "policy surface",
    "campaign field",
    "validator",
    "synthetic",
    "provider",
    "llm",
]

REQUIRED_VISIBLE_GERMAN = [
    "Prüfung deutscher Telefonantworten",
    "Kundensatz",
    "Antwort des Assistenten",
    "Bitte prüfen",
    "Klingt natürlich?",
    "Ist die Antwort klar verständlich?",
    "Ist die Antwort freundlich?",
    "Klingt die Antwort zu abrupt?",
    "Vorschlag für bessere Formulierung",
    "Bewertung als JSON herunterladen",
    "Bewertung als CSV herunterladen",
    "Zwischenstand im Browser speichern",
    "Zwischenstand laden",
    "Alle Eingaben löschen",
    "Druckansicht",
]


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._hidden_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "details"}:
            self._hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "details"} and self._hidden_depth:
            self._hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._hidden_depth:
            text = data.strip()
            if text:
                self.parts.append(text)


def assert_condition(condition: bool, message: Any) -> None:
    if not condition:
        raise AssertionError(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def visible_text(html_text: str) -> str:
    parser = VisibleTextParser()
    parser.feed(html_text)
    return "\n".join(parser.parts)


def validate_required_files() -> None:
    missing = [rel(path) for path in REQUIRED_FILES.values() if not path.exists()]
    assert_condition(not missing, f"missing required files: {missing}")


def validate_source_inputs() -> int:
    source_items = read_json(SOURCE_GERMAN_FINDINGS)["items"]
    assert_condition(source_items, "source German findings must not be empty")
    prod_046 = read_json(SOURCE_PROD_046_RESULT)
    prod_047 = read_json(SOURCE_PROD_047_RESULT)
    assert_condition(prod_046.get("validation", {}).get("passed") is True, "PROD-046 source validation must pass")
    assert_condition(prod_047.get("validation", {}).get("passed") is True, "PROD-047 source validation must pass")
    return len(source_items)


def validate_result(expected_item_count: int) -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(result["next_checkpoint_recommended"] == "PROD-048B-native-german-review-import", result)
    assert_condition(summary["review_item_count"] == expected_item_count, summary)
    assert_condition(summary["review_item_count"] > 0, summary)
    assert_condition(summary["topic_count"] >= 10, summary)
    assert_condition(summary["html_self_contained"] is True, summary)
    assert_condition(summary["all_visible_main_labels_german"] is True, summary)
    assert_condition(summary["reviewer_export_json_enabled"] is True, summary)
    assert_condition(summary["reviewer_export_csv_enabled"] is True, summary)
    assert_condition(summary["local_storage_enabled"] is True, summary)
    assert_condition(summary["print_friendly_mode_enabled"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must be false")
    return summary


def validate_packet(expected_item_count: int) -> None:
    packet = read_json(REQUIRED_FILES["packet"])
    items = packet["review_items"]
    assert_condition(len(items) == expected_item_count, "packet item count mismatch")
    rating_ids = {field["field_id"] for field in packet["rating_fields"]}
    safety_ids = {field["flag_id"] for field in packet["safety_flags"]}
    assert_condition(REQUIRED_RATING_FIELD_IDS <= rating_ids, rating_ids)
    assert_condition(REQUIRED_SAFETY_FLAGS <= safety_ids, safety_ids)
    seen = set()
    for item in items:
        assert_condition(item["review_item_id"] not in seen, item)
        seen.add(item["review_item_id"])
        assert_condition(item["customer_utterance"], item)
        assert_condition(item["agent_response"], item)
        assert_condition(item["topic_title_de"], item)
        assert_condition(item["situation_de"], item)
        assert_condition(item["review_instruction_de"] == "Bitte bewerten Sie nur die Formulierung der Antwort.", item)
        assert_condition(item["native_german_approval_claimed"] is False, item)
        assert_condition(item["legal_compliance_claimed"] is False, item)
    assert_condition(packet["review_boundary"]["native_german_approval_claimed"] is False, packet)
    assert_condition(packet["review_boundary"]["legal_compliance_claimed"] is False, packet)


def validate_html(expected_item_count: int) -> None:
    html_text = REQUIRED_FILES["html"].read_text(encoding="utf-8")
    visible = visible_text(html_text)
    lower_visible = visible.lower()
    assert_condition("<script src=" not in html_text.lower(), "external script dependency found")
    assert_condition("<link" not in html_text.lower(), "external stylesheet dependency found")
    assert_condition("http://" not in html_text.lower() and "https://" not in html_text.lower(), "external URL found")
    assert_condition("localStorage" in html_text, "localStorage functions missing")
    assert_condition("Blob(" in html_text, "Blob download missing")
    assert_condition("bewertungAlsJsonHerunterladen" in html_text, "JSON export function missing")
    assert_condition("bewertungAlsCsvHerunterladen" in html_text, "CSV export function missing")
    assert_condition("window.print()" in html_text, "print function missing")
    assert_condition("native German approval" not in lower_visible, "visible native approval claim found")
    assert_condition("legal compliance" not in lower_visible, "visible legal compliance claim found")
    assert_condition("rechtlich geprüft" not in lower_visible, "visible legal approval claim found")
    for label in REQUIRED_VISIBLE_GERMAN:
        assert_condition(label in visible, f"missing German visible label: {label}")
    for term in VISIBLE_TECHNICAL_TERMS:
        assert_condition(term not in lower_visible, f"visible technical term found: {term}")
    item_markers = re.findall(r'<article class="karte pruefkarte" data-review-item-id="[^"]+"', html_text)
    assert_condition(len(item_markers) == expected_item_count, f"HTML item count mismatch: {len(item_markers)} != {expected_item_count}")
    for field_id in REQUIRED_RATING_FIELD_IDS:
        assert_condition(f'data-rating-field="{field_id}"' in html_text, f"rating field missing in HTML: {field_id}")
    assert_condition('data-text-field="rewrite"' in html_text, "rewrite textarea missing")
    assert_condition('data-text-field="comment"' in html_text, "comment textarea missing")


def validate_export_schema() -> None:
    schema = read_json(REQUIRED_FILES["schema"])
    required_top = {"reviewer", "summary", "items"}
    assert_condition(required_top <= set(schema["required_top_level_fields"]), schema)
    assert_condition(REQUIRED_RATING_FIELD_IDS <= set(schema["required_rating_field_ids"]), schema)
    assert_condition(REQUIRED_SAFETY_FLAGS <= set(schema["required_safety_flag_ids"]), schema)


def validate_docs() -> None:
    doc = REQUIRED_FILES["doc"].read_text(encoding="utf-8").lower()
    report = REQUIRED_FILES["report"].read_text(encoding="utf-8").lower()
    readme = REQUIRED_FILES["readme_de"].read_text(encoding="utf-8").lower()
    commands = (ROOT / "docs" / "product" / "COMMANDS.md").read_text(encoding="utf-8").lower()
    index = (ROOT / "docs" / "product" / "CHECKPOINT_INDEX.md").read_text(encoding="utf-8").lower()
    roadmap = (ROOT / "docs" / "thesis" / "ROADMAP.md").read_text(encoding="utf-8").lower()
    methodology = (ROOT / "docs" / "thesis" / "METHODOLOGY_LOG.md").read_text(encoding="utf-8").lower()
    decision = (ROOT / "docs" / "thesis" / "DECISION_LOG.md").read_text(encoding="utf-8").lower()
    for text in (doc, report):
        assert_condition("no native german approval is claimed" in text, "missing native approval caveat")
        assert_condition("no legal compliance is claimed" in text, "missing legal compliance caveat")
        assert_condition("runtime behavior changed: `false`" in text, "missing runtime boundary")
    assert_condition("keine rechtsprüfung" in readme, "German README must say this is not legal review")
    assert_condition("native_german_review.html" in readme, "German README must mention HTML file")
    assert_condition("run_prod_048a_native_german_review_html_packet" in commands, "commands missing PROD-048A runner")
    assert_condition("prod_048a_native_german_review_html_packet" in index, "checkpoint index missing PROD-048A")
    assert_condition("prod-048a-native-german-review-html-packet" in roadmap, "roadmap missing PROD-048A")
    assert_condition("prod-048a" in methodology, "methodology log missing PROD-048A")
    assert_condition("native german review packet" in decision, "decision log missing PROD-048A decision")


def main() -> None:
    validate_required_files()
    expected_item_count = validate_source_inputs()
    summary = validate_result(expected_item_count)
    validate_packet(expected_item_count)
    validate_html(expected_item_count)
    validate_export_schema()
    validate_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
