#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-048A-german-review-html-and-brevity-packet"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

SOURCE_GERMAN_FINDINGS = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046-core-sales-policy-human-review"
    / "german_response_quality_findings.json"
)

REQUIRED_FILES = {
    "module": ROOT / "scripts" / "prod_048a_german_review_html_and_brevity_packet.py",
    "runner": ROOT / "scripts" / "run_prod_048a_german_review_html_and_brevity_packet.py",
    "validator": ROOT / "scripts" / "validate_prod_048a_german_review_html_and_brevity_packet.py",
    "doc": ROOT / "docs" / "product" / "PROD_048A_GERMAN_REVIEW_HTML_AND_BREVITY_PACKET.md",
    "result": OUT_DIR / "result.json",
    "report": OUT_DIR / "report.md",
    "packet": OUT_DIR / "native_german_grouped_review_packet.json",
    "html": OUT_DIR / "native_german_review.html",
    "schema": OUT_DIR / "native_german_review_export_schema.json",
    "readme_de": OUT_DIR / "native_german_review_readme_de.md",
    "table_csv": OUT_DIR / "native_german_review_table.csv",
    "brevity": OUT_DIR / "german_brevity_before_after.json",
    "duplicate_groups": OUT_DIR / "german_duplicate_answer_groups.json",
}

SOURCE_RESULT_FILES = {
    "prod_045": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
    "prod_046a": ROOT / "research" / "experiments" / "generated" / "PROD-046A-german-naturalized-policy-regression" / "result.json",
    "prod_046b": ROOT / "research" / "experiments" / "generated" / "PROD-046B-german-response-wording-quality-pass" / "result.json",
    "prod_046c": ROOT / "research" / "experiments" / "generated" / "PROD-046C-german-campaign-field-interpolation-guard" / "result.json",
    "prod_046d": ROOT / "research" / "experiments" / "generated" / "PROD-046D-german-source-informed-wording-quality-guard" / "result.json",
    "prod_046": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
    "prod_047": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
}

REQUIRED_RATING_FIELD_IDS = {
    "passt_zu_allen",
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
    "passt_nicht_zu_allen",
    "sonstiges",
}

BOUNDARY_FALSE_FIELDS = [
    "native_german_approval_claimed",
    "legal_compliance_claimed",
    "runtime_policy_changed",
    "call_control_behavior_changed",
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
    "Thema",
    "Kundensatz",
    "Antwort des Assistenten",
    "Diese Antwort wird für mehrere Kundensätze verwendet",
    "Passt diese Antwort zu allen Kundensätzen?",
    "Klingt natürlich?",
    "Ist die Antwort klar verständlich?",
    "Ist die Antwort freundlich?",
    "Klingt die Antwort zu abrupt?",
    "Klingt die Antwort intern, bürokratisch oder technisch?",
    "Vorschlag für bessere Formulierung",
    "Falls die Antwort nicht zu allen Kundensätzen passt",
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
        self.hidden_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth and data.strip():
            self.parts.append(data.strip())


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


def validate_source_results() -> None:
    for key, path in SOURCE_RESULT_FILES.items():
        payload = read_json(path)
        assert_condition(payload.get("validation", {}).get("passed") is True, f"{key} validation must pass")


def validate_result_summary(original_case_count: int) -> dict[str, Any]:
    result = read_json(REQUIRED_FILES["result"])
    summary = result["summary"]
    assert_condition(result["checkpoint_id"] == CHECKPOINT_ID, result)
    assert_condition(result["validation"]["passed"] is True, result)
    assert_condition(summary["original_german_case_count"] == original_case_count, summary)
    assert_condition(summary["grouped_review_card_count"] < original_case_count, summary)
    assert_condition(summary["repeated_answer_group_count"] > 0, summary)
    assert_condition(summary["average_german_response_character_count_after"] < summary["average_german_response_character_count_before"], summary)
    assert_condition(summary["html_self_contained"] is True, summary)
    assert_condition(summary["all_visible_main_labels_german"] is True, summary)
    assert_condition(summary["reviewer_export_json_enabled"] is True, summary)
    assert_condition(summary["reviewer_export_csv_enabled"] is True, summary)
    assert_condition(summary["local_storage_enabled"] is True, summary)
    for field in BOUNDARY_FALSE_FIELDS:
        assert_condition(summary[field] is False, f"{field} must remain false")
    return summary


def validate_packet(original_case_count: int) -> None:
    packet = read_json(REQUIRED_FILES["packet"])
    groups = packet["review_groups"]
    assert_condition(groups, "review groups required")
    rating_ids = {field["field_id"] for field in packet["rating_fields"]}
    safety_ids = {field["flag_id"] for field in packet["safety_flags"]}
    assert_condition(REQUIRED_RATING_FIELD_IDS <= rating_ids, rating_ids)
    assert_condition(REQUIRED_SAFETY_FLAGS <= safety_ids, safety_ids)
    case_to_group: dict[str, str] = {}
    duplicate_groups = 0
    for group in groups:
        assert_condition(group["group_id"], group)
        assert_condition(group["topic_title_de"], group)
        assert_condition(group["short_agent_response"], group)
        assert_condition(group["customer_utterances"], group)
        assert_condition(group["original_case_ids"], group)
        assert_condition(len(group["customer_utterances"]) == len(group["original_case_ids"]), group)
        assert_condition(group["native_german_approval_claimed"] is False, group)
        assert_condition(group["legal_compliance_claimed"] is False, group)
        if len(group["original_case_ids"]) > 1:
            duplicate_groups += 1
        for case_id in group["original_case_ids"]:
            assert_condition(case_id not in case_to_group, f"case appears twice: {case_id}")
            case_to_group[case_id] = group["group_id"]
    assert_condition(len(case_to_group) == original_case_count, f"represented case count mismatch: {len(case_to_group)}")
    assert_condition(duplicate_groups > 0, "no duplicate answer groups found")
    assert_condition(packet["review_boundary"]["native_german_approval_claimed"] is False, packet)
    assert_condition(packet["review_boundary"]["legal_compliance_claimed"] is False, packet)


def validate_brevity_and_groups(original_case_count: int) -> None:
    brevity_items = read_json(REQUIRED_FILES["brevity"])["items"]
    duplicate_groups = read_json(REQUIRED_FILES["duplicate_groups"])["items"]
    assert_condition(len(brevity_items) == original_case_count, "brevity item count mismatch")
    assert_condition(duplicate_groups, "duplicate group evidence required")
    assert_condition(any(item["changed"] for item in brevity_items), "shortened answers required")
    before_avg = sum(item["before_character_count"] for item in brevity_items) / len(brevity_items)
    after_avg = sum(item["after_character_count"] for item in brevity_items) / len(brevity_items)
    assert_condition(after_avg < before_avg, f"average not shorter: {before_avg} -> {after_avg}")
    assert_condition(any(item["case_count"] > 1 for item in duplicate_groups), "duplicate group with multiple cases required")


def validate_html(expected_group_count: int) -> None:
    html_text = REQUIRED_FILES["html"].read_text(encoding="utf-8")
    visible = visible_text(html_text)
    lower_visible = visible.lower()
    lower_html = html_text.lower()
    assert_condition("<script src=" not in lower_html, "external script dependency found")
    assert_condition("<link" not in lower_html, "external stylesheet dependency found")
    assert_condition("http://" not in lower_html and "https://" not in lower_html, "external URL found")
    assert_condition("localStorage" in html_text, "localStorage functions missing")
    assert_condition("Blob(" in html_text, "Blob download missing")
    assert_condition("bewertungAlsJsonHerunterladen" in html_text, "JSON export function missing")
    assert_condition("bewertungAlsCsvHerunterladen" in html_text, "CSV export function missing")
    assert_condition("window.print()" in html_text, "print function missing")
    for label in REQUIRED_VISIBLE_GERMAN:
        assert_condition(label in visible, f"missing German visible label: {label}")
    for term in VISIBLE_TECHNICAL_TERMS:
        assert_condition(term not in lower_visible, f"visible technical term found: {term}")
    assert_condition("native german approval" not in lower_visible, "visible native approval claim found")
    assert_condition("legal compliance" not in lower_visible, "visible legal compliance claim found")
    assert_condition("rechtlich geprüft" not in lower_visible, "visible legal approval claim found")
    group_markers = re.findall(r'<article class="karte pruefgruppe" data-review-group-id="[^"]+"', html_text)
    assert_condition(len(group_markers) == expected_group_count, f"HTML group count mismatch: {len(group_markers)} != {expected_group_count}")
    for field_id in REQUIRED_RATING_FIELD_IDS:
        assert_condition(f'data-rating-field="{field_id}"' in html_text, f"missing rating field: {field_id}")
    assert_condition('data-text-field="different_cases"' in html_text, "different-cases textarea missing")
    assert_condition('data-text-field="rewrite"' in html_text, "rewrite textarea missing")
    assert_condition('data-text-field="comment"' in html_text, "comment textarea missing")


def validate_export_schema() -> None:
    schema = read_json(REQUIRED_FILES["schema"])
    assert_condition({"reviewer", "summary", "groups"} <= set(schema["required_top_level_fields"]), schema)
    assert_condition(REQUIRED_RATING_FIELD_IDS <= set(schema["required_rating_field_ids"]), schema)
    assert_condition(REQUIRED_SAFETY_FLAGS <= set(schema["required_safety_flag_ids"]), schema)
    assert_condition("case_ids" in schema["required_group_fields"], schema)


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
        assert_condition("runtime policy changed: `false`" in text, "missing runtime policy boundary")
    assert_condition("keine rechtsprüfung" in readme, "German README must say this is not legal review")
    assert_condition("kundensätze zusammengefasst" in readme, "German README must explain grouping")
    assert_condition("run_prod_048a_german_review_html_and_brevity_packet" in commands, "commands missing runner")
    assert_condition("prod_048a_german_review_html_and_brevity_packet" in index, "checkpoint index missing doc")
    assert_condition("prod-048a-german-review-html-and-brevity-packet" in roadmap, "roadmap missing checkpoint")
    assert_condition("prod-048a" in methodology and "brevity" in methodology, "methodology missing checkpoint")
    assert_condition("group repeated german answers" in decision, "decision log missing grouping decision")


def main() -> None:
    validate_required_files()
    source_items = read_json(SOURCE_GERMAN_FINDINGS)["items"]
    original_case_count = len(source_items)
    validate_source_results()
    summary = validate_result_summary(original_case_count)
    validate_packet(original_case_count)
    validate_brevity_and_groups(original_case_count)
    validate_html(summary["grouped_review_card_count"])
    validate_export_schema()
    validate_docs()
    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": {"passed": True}, "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
