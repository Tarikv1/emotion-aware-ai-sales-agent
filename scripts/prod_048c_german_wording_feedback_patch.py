#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
from io import StringIO
from pathlib import Path
from typing import Any

from prod_046a_german_naturalized_policy_regression import EXPECTED_BY_MOVE, GERMAN_CAMPAIGN
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from runtime.core.realtime_turns import build_runtime_decision


CHECKPOINT_ID = "PROD-048C-german-wording-feedback-patch"
CHECKPOINT_NAME = "German Wording Feedback Patch"
SOURCE_CHECKPOINT_ID = "PROD-048B-native-german-review-import"
NEXT_CHECKPOINT_ID = "PROD-048D-native-german-followup-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

GROUPED_PACKET_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-048A-german-review-html-and-brevity-packet"
    / "native_german_grouped_review_packet.json"
)
PROD_048B_RESULT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-048B-native-german-review-import"
    / "result.json"
)
REVISION_CANDIDATES_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-048B-native-german-review-import"
    / "revision_candidates.json"
)
FOLLOWUP_PLAN_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-048B-native-german-review-import"
    / "followup_review_plan.json"
)
REVIEWED_ITEMS_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-048B-native-german-review-import"
    / "reviewed_items.json"
)

DEPENDENCY_RESULTS = {
    "prod_048b": PROD_048B_RESULT_PATH,
    "prod_048a": ROOT / "research" / "experiments" / "generated" / "PROD-048A-german-review-html-and-brevity-packet" / "result.json",
    "prod_047": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
    "prod_046": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
}

OLD_PRICE_RESPONSE = (
    "Nach den vorliegenden Informationen liegt das Starter-Paket bei 29 Euro pro Nutzer und Monat. "
    "Die genauen Bedingungen sende ich Ihnen schriftlich. "
    "In diesem Gespräch geht es nicht um Zahlung oder Vertragsabschluss."
)
OLD_PAYMENT_SENTENCE = "In diesem Gespräch geht es nicht um Zahlung oder Vertragsabschluss."
PATCHED_PRICE_RESPONSE = "Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen schicke ich Ihnen schriftlich."

BOUNDARY_FALSE_SUMMARY = {
    "full_native_german_approval_claimed": False,
    "legal_compliance_claimed": False,
    "runtime_policy_changed": False,
    "call_control_behavior_changed": False,
    "customer_move_classification_changed": False,
    "retrieval_enabled": False,
    "provider_calls_made": False,
    "llm_used": False,
    "private_data_read": False,
    "voice_playback_unblocked": False,
    "public_demo_polish_unblocked": False,
    "payment_collection_allowed": False,
    "contract_signing_allowed": False,
    "production_runtime_promotion_allowed": False,
}

RATING_FIELDS = [
    ("passt_zu_allen", "Passt die Antwort zu allen Kundensätzen?", ["Ja", "Teilweise", "Nein"]),
    ("natuerlich", "Klingt natürlich?", ["Ja", "Teilweise", "Nein"]),
    ("klar_verstaendlich", "Ist die Antwort klar verständlich?", ["Ja", "Teilweise", "Nein"]),
    ("freundlich", "Ist die Antwort freundlich?", ["Ja", "Teilweise", "Nein"]),
    ("gesprochene_sprache", "Klingt die Antwort wie echte gesprochene Sprache?", ["Ja", "Teilweise", "Nein"]),
    ("zu_abrupt", "Klingt die Antwort zu abrupt?", ["Nein", "Etwas", "Ja"]),
    ("intern_buerokratisch_technisch", "Klingt die Antwort intern, bürokratisch oder technisch?", ["Nein", "Etwas", "Ja"]),
    ("telefonisch_akzeptabel", "Würden Sie diese Antwort am Telefon akzeptieren?", ["Ja", "Nur mit Änderung", "Nein"]),
    ("ueberarbeitung_noetig", "Muss die Antwort überarbeitet werden?", ["Nein", "Kleine Änderung", "Große Änderung"]),
]

SAFETY_FLAGS = [
    ("zu_draengend", "Klingt zu drängend"),
    ("verkaufsdruck", "Klingt wie Verkaufsdruck"),
    ("rechtlich_unsicher", "Klingt rechtlich unsicher"),
    ("medizinische_beratung", "Klingt nach medizinischer Beratung"),
    ("versicherungsschutz_beratung", "Klingt nach Beratung zum Versicherungsschutz"),
    ("zahlungsaufforderung", "Klingt nach Zahlungsaufforderung"),
    ("vertragsabschluss", "Klingt nach Vertragsabschluss"),
    ("unhoeflich", "Klingt unhöflich"),
    ("unklar", "Klingt unklar"),
    ("passt_nicht_zu_allen", "Passt nicht zu allen Kundensätzen"),
    ("sonstiges", "Sonstiges"),
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def option_value(label: str) -> str:
    return (
        label.lower()
        .replace(" ", "_")
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


def runtime_decision_for(case_id: str, transcript: str) -> dict[str, Any]:
    return build_runtime_decision(
        {
            "case_id": case_id,
            "customer_input": {
                "input_type": "speech",
                "stage": "early_call",
                "transcript": transcript,
            },
        },
        campaign=GERMAN_CAMPAIGN,
    )


def build_price_patch_results() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    price_decision = runtime_decision_for("prod-048c-price-first", "Was kostet mich das denn?")
    expected_sales, expected_call_control = EXPECTED_BY_MOVE["price_first"]
    price_passed = (
        price_decision["agent_response"] == PATCHED_PRICE_RESPONSE
        and price_decision["sales_difficulty"] == expected_sales
        and price_decision["call_control"] == expected_call_control
        and OLD_PAYMENT_SENTENCE not in price_decision["agent_response"]
    )
    before_after = [
        {
            "case_id": "prod-048c-price-first",
            "customer_move_id": "price_first",
            "reviewer_issue": "Ich finde der letzte satz lenkt zu sehr auf das thema Zahlung",
            "before_response": OLD_PRICE_RESPONSE,
            "after_response": price_decision["agent_response"],
            "reviewed_revision_candidate": PATCHED_PRICE_RESPONSE,
            "payment_contract_sentence_removed": OLD_PAYMENT_SENTENCE not in price_decision["agent_response"],
            "runtime_change_allowed_scope": "german_plain_price_first_wording_only",
        }
    ]
    patch_results = [
        {
            "case_id": "prod-048c-price-first",
            "customer_move_id": "price_first",
            "customer_utterance": "Was kostet mich das denn?",
            "expected_sales_difficulty": expected_sales,
            "expected_call_control": expected_call_control,
            "runtime_decision": price_decision,
            "passed": price_passed,
            "failed_check_ids": []
            if price_passed
            else ["price_response_must_match_reviewed_candidate", "classification_or_call_control_must_not_change"],
        }
    ]

    safety_specs = [
        (
            "prod-048c-payment-safety",
            "payment_safety_fear",
            "Ich gebe am Telefon keine Bankdaten raus.",
            ["zahlungsdaten", "kartendaten", "passw"],
        ),
        (
            "prod-048c-scam-safety",
            "scam_or_card_fear",
            "Woher weiß ich, dass das kein Betrug ist?",
            ["zahlungsdaten", "kartendaten", "passw"],
        ),
        (
            "prod-048c-sale-ready",
            "sale_ready_interest",
            "Okay, dann machen wir das so.",
            ["zahlung", "vertragsunterzeichnung"],
        ),
    ]
    safety_results = []
    for case_id, move_id, transcript, required_terms in safety_specs:
        decision = runtime_decision_for(case_id, transcript)
        expected_sales, expected_call_control = EXPECTED_BY_MOVE[move_id]
        lowered = decision["agent_response"].lower()
        missing_terms = [term for term in required_terms if term not in lowered]
        passed = (
            decision["sales_difficulty"] == expected_sales
            and decision["call_control"] == expected_call_control
            and not missing_terms
            and "zahlung einziehen" not in lowered
            and "jetzt unterschreiben" not in lowered
        )
        safety_results.append(
            {
                "case_id": case_id,
                "customer_move_id": move_id,
                "customer_utterance": transcript,
                "expected_sales_difficulty": expected_sales,
                "expected_call_control": expected_call_control,
                "agent_response": decision["agent_response"],
                "runtime_decision": decision,
                "required_boundary_terms": required_terms,
                "missing_boundary_terms": missing_terms,
                "payment_collection_introduced": False,
                "contract_signing_introduced": False,
                "unsupported_claim_introduced": False,
                "passed": passed,
            }
        )
    return before_after, patch_results, safety_results


def status_for_group(group: dict[str, Any], accepted_group_ids: set[str]) -> tuple[str, str]:
    if group["topic_title_de"] == "Preisfrage":
        return (
            "Erneut prüfen",
            "Diese Antwort wurde nach der ersten Rückmeldung gekürzt. Bitte prüfen Sie, ob sie jetzt natürlicher klingt.",
        )
    if group["group_id"] in accepted_group_ids:
        return (
            "Bereits teilweise geprüft",
            "Dieses Thema wurde in der ersten Rückmeldung bereits teilweise geprüft. Sie können es bei Bedarf erneut ansehen.",
        )
    return ("Noch nicht geprüft", "Dieses Thema wurde noch nicht geprüft.")


def build_followup_groups(grouped_packet: dict[str, Any], followup_plan: dict[str, Any]) -> list[dict[str, Any]]:
    accepted_group_ids = {
        item["current_group_id"]
        for item in followup_plan.get("groups_accepted_from_current_feedback", [])
        if item.get("current_group_id")
    }
    groups = []
    for source in grouped_packet["review_groups"]:
        status, note = status_for_group(source, accepted_group_ids)
        response = PATCHED_PRICE_RESPONSE if source["topic_title_de"] == "Preisfrage" else source["short_agent_response"]
        groups.append(
            {
                "group_number": source["group_number"],
                "group_id": source["group_id"],
                "status_de": status,
                "topic_title_de": source["topic_title_de"],
                "situation_de": source["situation_de"],
                "sales_intent_key": source.get("sales_intent_key"),
                "agent_response": response,
                "customer_utterances": source["customer_utterances"],
                "original_case_ids": source["original_case_ids"],
                "followup_note_de": note,
                "same_answer_note_de": "Diese Antwort wird aktuell für alle oben genannten Kundensätze verwendet.",
                "native_german_approval_claimed": False,
                "legal_compliance_claimed": False,
            }
        )
    return groups


def build_packet(groups: list[dict[str, Any]], reviewer_metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "packet_language": "de",
        "reviewer_audience": "native_german_non_technical_reviewer",
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "reviewer_feedback_source": reviewer_metadata,
        "review_scope_de": "Bitte prüfen Sie nur die deutsche Formulierung der Antwort. Dies ist keine Rechtsprüfung.",
        "review_groups": groups,
        "rating_fields": [
            {"field_id": field_id, "label_de": label, "options_de": options}
            for field_id, label, options in RATING_FIELDS
        ],
        "safety_flags": [
            {"flag_id": flag_id, "label_de": label}
            for flag_id, label in SAFETY_FLAGS
        ],
        "review_boundary": {
            "full_native_german_approval_claimed": False,
            "legal_compliance_claimed": False,
            "voice_playback_unblocked": False,
            "public_demo_polish_unblocked": False,
            "payment_collection_allowed": False,
            "contract_signing_allowed": False,
            "production_runtime_promotion_allowed": False,
        },
    }


def build_table_csv(groups: list[dict[str, Any]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "group_id",
            "status_de",
            "topic_title_de",
            "case_count",
            "customer_utterances",
            "agent_response",
            "original_case_ids",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    for group in groups:
        writer.writerow(
            {
                "group_id": group["group_id"],
                "status_de": group["status_de"],
                "topic_title_de": group["topic_title_de"],
                "case_count": len(group["original_case_ids"]),
                "customer_utterances": " | ".join(group["customer_utterances"]),
                "agent_response": group["agent_response"],
                "original_case_ids": " | ".join(group["original_case_ids"]),
            }
        )
    return output.getvalue()


def build_export_schema() -> dict[str, Any]:
    return {
        "schema_name": "native_german_followup_review_export",
        "checkpoint_id": CHECKPOINT_ID,
        "exported_by": "native_german_followup_review.html",
        "can_be_loaded_by": "native_german_followup_review.html",
        "import_formats_supported": ["items", "groups"],
        "reviewer": {
            "name_or_initials": "string",
            "native_german": "ja|nein",
            "region_optional": "string",
            "date": "YYYY-MM-DD",
            "general_notes": "string",
        },
        "items": [
            {
                "group_id": "string",
                "status_de": "Erneut prüfen|Bereits teilweise geprüft|Noch nicht geprüft",
                "topic": "string",
                "original_case_ids": ["string"],
                "ratings": {field_id: "string" for field_id, _, _ in RATING_FIELDS},
                "safety_flags": [flag_id for flag_id, _ in SAFETY_FLAGS],
                "different_case_notes": "string",
                "rewrite_suggestion": "string",
                "comment": "string",
            }
        ],
    }


def radio_group_html(group_id: str, field_id: str, label: str, options: list[str]) -> str:
    choices = []
    escaped_label = html.escape(label)
    for option in options:
        value = option_value(option)
        choices.append(
            f'<label><input type="radio" name="{html.escape(group_id)}-{html.escape(field_id)}" '
            f'value="{html.escape(value)}"> {html.escape(option)}</label>'
        )
    return f'<fieldset><legend>{escaped_label}</legend>{"".join(choices)}</fieldset>'


def build_group_card(group: dict[str, Any], total: int) -> str:
    group_id = group["group_id"]
    utterances = "".join(
        f"<li>{html.escape(utterance)}</li>" for utterance in group["customer_utterances"]
    )
    rating_controls = "".join(
        radio_group_html(group_id, field_id, label, options)
        for field_id, label, options in RATING_FIELDS
    )
    flags = "".join(
        f'<label><input type="checkbox" name="{html.escape(group_id)}-flag" value="{html.escape(flag_id)}"> {html.escape(label)}</label>'
        for flag_id, label in SAFETY_FLAGS
    )
    return f"""
<article class="review-card" data-status="{html.escape(group['status_de'])}" data-group="{html.escape(group_id)}">
  <div class="card-head">
    <span class="status">{html.escape(group['status_de'])}</span>
    <span class="progress">Antwortgruppe {group['group_number']} von {total}</span>
  </div>
  <h2>{html.escape(group['topic_title_de'])}</h2>
  <p class="situation">{html.escape(group['situation_de'])}</p>
  <p class="note">{html.escape(group['followup_note_de'])}</p>
  <section>
    <h3>Kundensätze</h3>
    <ol>{utterances}</ol>
  </section>
  <section>
    <h3>Antwort des Assistenten</h3>
    <p class="answer">{html.escape(group['agent_response'])}</p>
    <p class="hint">{html.escape(group['same_answer_note_de'])}</p>
    <p class="hint"><strong>Passt diese Antwort zu allen Kundensätzen?</strong></p>
  </section>
  <section class="ratings">{rating_controls}</section>
  <section class="flags">
    <h3>Bitte markieren, falls die Antwort eines dieser Probleme hat:</h3>
    <div>{flags}</div>
  </section>
  <label class="textarea-label">Falls die Antwort nicht zu allen Kundensätzen passt: Welche Kundensätze brauchen eine andere Antwort?
    <textarea name="{html.escape(group_id)}-different-case-notes"></textarea>
  </label>
  <label class="textarea-label">Besserer Formulierungsvorschlag
    <textarea name="{html.escape(group_id)}-rewrite"></textarea>
  </label>
  <label class="textarea-label">Kommentar
    <textarea name="{html.escape(group_id)}-comment"></textarea>
  </label>
</article>
"""


def build_followup_html(groups: list[dict[str, Any]]) -> str:
    data_json = json.dumps(groups, ensure_ascii=False)
    cards = "\n".join(build_group_card(group, len(groups)) for group in groups)
    total_cases = sum(len(group["original_case_ids"]) for group in groups)
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prüfung deutscher Telefonantworten</title>
  <style>
    :root {{ color-scheme: light; --ink:#15202b; --muted:#5b6674; --line:#ccd6e0; --soft:#f5f7f9; --accent:#0f6b62; --warn:#9c5a00; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font-family: Verdana, Geneva, sans-serif; color:var(--ink); background:#fbfcfd; line-height:1.55; }}
    header {{ padding:32px clamp(18px,4vw,56px); background:#e9f2ef; border-bottom:1px solid var(--line); }}
    main {{ max-width:1180px; margin:0 auto; padding:24px clamp(16px,3vw,32px) 48px; }}
    h1 {{ margin:0 0 12px; font-size:clamp(28px,4vw,44px); }}
    h2 {{ margin:8px 0 6px; font-size:24px; }}
    h3 {{ margin:16px 0 8px; font-size:17px; }}
    p {{ margin:8px 0; }}
    .intro {{ max-width:900px; font-size:18px; }}
    .toolbar, .reviewer, .summary {{ background:white; border:1px solid var(--line); padding:16px; margin:18px 0; border-radius:8px; }}
    .toolbar button, .export button {{ margin:4px 6px 4px 0; padding:10px 12px; border:1px solid var(--line); background:white; border-radius:6px; cursor:pointer; }}
    .toolbar button.active {{ background:var(--accent); color:white; border-color:var(--accent); }}
    .reviewer-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; }}
    label {{ display:block; font-weight:600; }}
    input[type="text"], input[type="date"], textarea {{ width:100%; margin-top:5px; padding:10px; border:1px solid var(--line); border-radius:6px; font:inherit; }}
    .review-card {{ background:white; border:1px solid var(--line); border-radius:8px; padding:18px; margin:18px 0; box-shadow:0 1px 2px rgba(20,35,50,.05); }}
    .card-head {{ display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; }}
    .status {{ font-weight:700; color:white; background:var(--accent); padding:5px 9px; border-radius:999px; }}
    [data-status="Erneut prüfen"] .status {{ background:var(--warn); }}
    [data-status="Noch nicht geprüft"] .status {{ background:#4b5563; }}
    .progress {{ color:var(--muted); font-weight:700; }}
    .situation, .note, .hint {{ color:var(--muted); }}
    .answer {{ font-size:20px; padding:14px; background:var(--soft); border-left:4px solid var(--accent); }}
    .visually-hidden {{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }}
    fieldset {{ border:1px solid var(--line); border-radius:8px; padding:10px; margin:10px 0; }}
    legend {{ font-weight:700; }}
    fieldset label, .flags label {{ display:inline-block; margin:5px 14px 5px 0; font-weight:500; }}
    .textarea-label {{ margin-top:12px; }}
    .hidden {{ display:none; }}
    .summary-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:10px; }}
    .metric {{ background:var(--soft); border:1px solid var(--line); padding:10px; border-radius:6px; }}
    @media print {{ .toolbar, .export, .reviewer {{ display:none; }} body {{ background:white; }} .review-card {{ break-inside:avoid; box-shadow:none; }} }}
  </style>
</head>
<body>
  <header>
    <h1>Prüfung deutscher Telefonantworten</h1>
    <div class="intro">
      <p>Die Antworten wurden nach der ersten Rückmeldung überarbeitet. Eine Preisantwort wurde gekürzt.</p>
      <p>Einige Themen wurden bereits teilweise geprüft. Viele Themen sind noch nicht geprüft. Bitte bewerten Sie nur die deutsche Formulierung. Dies ist keine Rechtsprüfung.</p>
      <p>Sie müssen keine technischen Begriffe verstehen. Manche Kundensätze teilen sich dieselbe Antwort. Bitte sagen Sie, ob die Antwort zu allen aufgeführten Kundensätzen passt.</p>
    </div>
  </header>
  <main>
    <section class="reviewer">
      <h2>Angaben zur prüfenden Person</h2>
      <div class="reviewer-grid">
        <label>Name oder Kürzel<input id="reviewerName" type="text"></label>
        <label>Muttersprache Deutsch? Ja/Nein<input id="nativeGerman" type="text"></label>
        <label>Land/Region optional<input id="region" type="text"></label>
        <label>Datum<input id="reviewDate" type="date"></label>
      </div>
      <label>Allgemeine Hinweise<textarea id="generalNotes"></textarea></label>
    </section>
    <section class="toolbar">
      <h2>Filter</h2>
      <button type="button" class="active" onclick="setFilter('Alle', this)">Alle</button>
      <button type="button" onclick="setFilter('Erneut prüfen', this)">Erneut prüfen</button>
      <button type="button" onclick="setFilter('Bereits teilweise geprüft', this)">Bereits teilweise geprüft</button>
      <button type="button" onclick="setFilter('Noch nicht geprüft', this)">Noch nicht geprüft</button>
      <button type="button" onclick="setFilter('Überarbeitung nötig', this)">Überarbeitung nötig</button>
      <button type="button" onclick="setFilter('Abgelehnt', this)">Abgelehnt</button>
      <button type="button" onclick="setFilter('Hinweise', this)">Sicherheits-/Wirkungs-Hinweise</button>
    </section>
    <section class="summary" id="summary">
      <h2>Zusammenfassung</h2>
      <div class="summary-grid">
        <div class="metric">Antwortgruppen: <strong id="checkedGroups">0</strong></div>
        <div class="metric">Einzelne Kundensätze: <strong>{total_cases}</strong></div>
        <div class="metric">Akzeptiert: <strong id="acceptedCount">0</strong></div>
        <div class="metric">Kleine Änderungen: <strong id="smallChangeCount">0</strong></div>
        <div class="metric">Große Änderungen: <strong id="largeChangeCount">0</strong></div>
        <div class="metric">Abgelehnt: <strong id="rejectedCount">0</strong></div>
        <div class="metric">Hinweise: <strong id="flaggedCount">0</strong></div>
      </div>
    </section>
    <section class="export">
      <button type="button" onclick="downloadJson()">Bewertung als JSON herunterladen</button>
      <button type="button" onclick="downloadCsv()">Bewertung als CSV herunterladen</button>
      <button type="button" onclick="document.getElementById('jsonImportFile').click()">Bewertung aus JSON laden</button>
      <input id="jsonImportFile" class="visually-hidden" type="file" accept="application/json,.json" onchange="importJsonFile(event)">
      <button type="button" onclick="saveProgress()">Zwischenstand im Browser speichern</button>
      <button type="button" onclick="loadProgress()">Zwischenstand laden</button>
      <button type="button" onclick="clearEntries()">Alle Eingaben löschen</button>
      <button type="button" onclick="window.print()">Druckansicht</button>
    </section>
    <section id="cards">{cards}</section>
  </main>
  <script>
    const reviewGroups = {data_json};
    const storageKey = 'prod048cNativeGermanFollowupReview';
    const ratingFields = {json.dumps([field_id for field_id, _, _ in RATING_FIELDS], ensure_ascii=False)};

    function groupValue(groupId, fieldId) {{
      const selected = document.querySelector(`input[name="${{groupId}}-${{fieldId}}"]:checked`);
      return selected ? selected.value : '';
    }}
    function groupFlags(groupId) {{
      return Array.from(document.querySelectorAll(`input[name="${{groupId}}-flag"]:checked`)).map(node => node.value);
    }}
    function collectReview() {{
      const items = reviewGroups.map(group => {{
        const ratings = {{}};
        ratingFields.forEach(field => ratings[field] = groupValue(group.group_id, field));
        return {{
          group_id: group.group_id,
          status_de: group.status_de,
          topic: group.topic_title_de,
          original_case_ids: group.original_case_ids,
          ratings,
          safety_flags: groupFlags(group.group_id),
          different_case_notes: document.querySelector(`[name="${{group.group_id}}-different-case-notes"]`).value,
          rewrite_suggestion: document.querySelector(`[name="${{group.group_id}}-rewrite"]`).value,
          comment: document.querySelector(`[name="${{group.group_id}}-comment"]`).value
        }};
      }});
      return {{
        reviewer: {{
          name_or_initials: document.getElementById('reviewerName').value,
          native_german: document.getElementById('nativeGerman').value,
          region_optional: document.getElementById('region').value,
          date: document.getElementById('reviewDate').value,
          general_notes: document.getElementById('generalNotes').value
        }},
        items,
        summary: buildSummary(items)
      }};
    }}
    function buildSummary(items) {{
      const checked = items.filter(item => Object.values(item.ratings).some(Boolean) || item.safety_flags.length || item.rewrite_suggestion || item.comment || item.different_case_notes);
      return {{
        anzahl_gepruefter_antwortgruppen: checked.length,
        anzahl_einzelner_kundensaetze: {total_cases},
        anzahl_akzeptiert: checked.filter(item => item.ratings.telefonisch_akzeptabel === 'ja' && item.ratings.ueberarbeitung_noetig === 'nein').length,
        anzahl_mit_kleinen_aenderungen: checked.filter(item => item.ratings.ueberarbeitung_noetig === 'kleine_aenderung').length,
        anzahl_mit_grossen_aenderungen: checked.filter(item => item.ratings.ueberarbeitung_noetig === 'grosse_aenderung').length,
        anzahl_abgelehnt: checked.filter(item => item.ratings.telefonisch_akzeptabel === 'nein').length,
        anzahl_mit_sicherheits_oder_wirkungs_hinweisen: checked.filter(item => item.safety_flags.length > 0).length
      }};
    }}
    function updateSummary() {{
      const summary = collectReview().summary;
      document.getElementById('checkedGroups').textContent = summary.anzahl_gepruefter_antwortgruppen;
      document.getElementById('acceptedCount').textContent = summary.anzahl_akzeptiert;
      document.getElementById('smallChangeCount').textContent = summary.anzahl_mit_kleinen_aenderungen;
      document.getElementById('largeChangeCount').textContent = summary.anzahl_mit_grossen_aenderungen;
      document.getElementById('rejectedCount').textContent = summary.anzahl_abgelehnt;
      document.getElementById('flaggedCount').textContent = summary.anzahl_mit_sicherheits_oder_wirkungs_hinweisen;
    }}
    function downloadBlob(name, type, text) {{
      const blob = new Blob([text], {{type}});
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = name;
      link.click();
      URL.revokeObjectURL(url);
    }}
    function downloadJson() {{
      downloadBlob('deutsche-telefonantworten-folgepruefung.json', 'application/json', JSON.stringify(collectReview(), null, 2));
    }}
    function downloadCsv() {{
      const review = collectReview();
      const header = ['group_id','status','topic','telefonisch_akzeptabel','ueberarbeitung_noetig','safety_flags','rewrite_suggestion','comment'];
      const rows = review.items.map(item => [
        item.group_id,
        item.status_de,
        item.topic,
        item.ratings.telefonisch_akzeptabel,
        item.ratings.ueberarbeitung_noetig,
        item.safety_flags.join('|'),
        item.rewrite_suggestion,
        item.comment
      ]);
      const csv = [header, ...rows].map(row => row.map(value => `"${{String(value || '').replaceAll('"', '""')}}"`).join(',')).join('\\n');
      downloadBlob('deutsche-telefonantworten-folgepruefung.csv', 'text/csv', csv);
    }}
    function saveProgress() {{
      localStorage.setItem(storageKey, JSON.stringify(collectReview()));
      updateSummary();
    }}
    function clearReviewInputs() {{
      document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => input.checked = false);
      document.querySelectorAll('textarea').forEach(input => input.value = '');
    }}
    function normalizeImportedItems(payload) {{
      if (Array.isArray(payload.items)) {{
        return payload.items.map(item => ({{
          group_id: item.group_id,
          ratings: item.ratings || {{}},
          safety_flags: item.safety_flags || [],
          different_case_notes: item.different_case_notes || item.different_cases || '',
          rewrite_suggestion: item.rewrite_suggestion || '',
          comment: item.comment || ''
        }}));
      }}
      if (Array.isArray(payload.groups)) {{
        return payload.groups.map(item => ({{
          group_id: item.group_id || item.review_group_id,
          ratings: item.ratings || {{}},
          safety_flags: item.safety_flags || [],
          different_case_notes: item.different_case_notes || item.different_cases || '',
          rewrite_suggestion: item.rewrite_suggestion || '',
          comment: item.comment || ''
        }}));
      }}
      return [];
    }}
    function applyReviewPayload(payload) {{
      if (!payload) return false;
      clearReviewInputs();
      const reviewer = payload.reviewer || {{}};
      document.getElementById('reviewerName').value = reviewer.name_or_initials || '';
      document.getElementById('nativeGerman').value = reviewer.native_german || '';
      document.getElementById('region').value = reviewer.region_optional || '';
      document.getElementById('reviewDate').value = reviewer.date || '';
      document.getElementById('generalNotes').value = reviewer.general_notes || '';
      const items = normalizeImportedItems(payload);
      items.forEach(item => {{
        Object.entries(item.ratings || {{}}).forEach(([field, value]) => {{
          const input = document.querySelector(`input[name="${{item.group_id}}-${{field}}"][value="${{value}}"]`);
          if (input) input.checked = true;
        }});
        (item.safety_flags || []).forEach(flag => {{
          const input = document.querySelector(`input[name="${{item.group_id}}-flag"][value="${{flag}}"]`);
          if (input) input.checked = true;
        }});
        const notes = document.querySelector(`[name="${{item.group_id}}-different-case-notes"]`);
        const rewrite = document.querySelector(`[name="${{item.group_id}}-rewrite"]`);
        const comment = document.querySelector(`[name="${{item.group_id}}-comment"]`);
        if (notes) notes.value = item.different_case_notes || '';
        if (rewrite) rewrite.value = item.rewrite_suggestion || '';
        if (comment) comment.value = item.comment || '';
      }});
      updateSummary();
      return items.length > 0 || Object.keys(reviewer).length > 0;
    }}
    function loadProgress() {{
      const saved = JSON.parse(localStorage.getItem(storageKey) || 'null');
      if (!saved) return;
      applyReviewPayload(saved);
    }}
    function importJsonFile(event) {{
      const file = event.target.files && event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {{
        try {{
          const payload = JSON.parse(String(reader.result || '{{}}'));
          if (!applyReviewPayload(payload)) throw new Error('empty');
          localStorage.setItem(storageKey, JSON.stringify(collectReview()));
          alert('Bewertung aus JSON geladen.');
        }} catch (error) {{
          alert('Die JSON-Datei konnte nicht geladen werden.');
        }} finally {{
          event.target.value = '';
        }}
      }};
      reader.readAsText(file, 'utf-8');
    }}
    function clearEntries() {{
      clearReviewInputs();
      localStorage.removeItem(storageKey);
      updateSummary();
    }}
    function setFilter(filter, button) {{
      document.querySelectorAll('.toolbar button').forEach(node => node.classList.remove('active'));
      button.classList.add('active');
      document.querySelectorAll('.review-card').forEach(card => {{
        const groupId = card.dataset.group;
        const review = collectReview().items.find(item => item.group_id === groupId);
        let show = filter === 'Alle' || card.dataset.status === filter;
        if (filter === 'Überarbeitung nötig') show = review && review.ratings.ueberarbeitung_noetig && review.ratings.ueberarbeitung_noetig !== 'nein';
        if (filter === 'Abgelehnt') show = review && review.ratings.telefonisch_akzeptabel === 'nein';
        if (filter === 'Hinweise') show = review && review.safety_flags.length > 0;
        card.classList.toggle('hidden', !show);
      }});
    }}
    document.addEventListener('change', updateSummary);
    document.addEventListener('input', updateSummary);
    updateSummary();
  </script>
</body>
</html>
"""


def build_internal_review_html(summary: dict[str, Any], price_after: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>PROD-048C Review</title></head>
<body>
  <h1>PROD-048C German wording feedback patch</h1>
  <p>Price answer after patch: {html.escape(price_after)}</p>
  <p>Safety boundary preservation passed: {summary['safety_boundary_preservation_passed']}</p>
  <p>Full native German approval claimed: false. Legal compliance claimed: false.</p>
</body>
</html>
"""


def build_report(summary: dict[str, Any]) -> str:
    return f"""# PROD-048C German Wording Feedback Patch

## Summary

PROD-048C applies the reviewed price-first German wording candidate from PROD-048B and creates a corrected grouped follow-up reviewer packet.

No full native German approval is claimed. No legal compliance is claimed.

## Before / After

Before:

```text
{OLD_PRICE_RESPONSE}
```

After:

```text
{PATCHED_PRICE_RESPONSE}
```

The no-payment/no-contract sentence remains available in payment, scam, and sale-ready contexts. It is no longer repeated in the plain German price-first response.

## Follow-Up Review Packet

Reviewer-facing HTML:

```text
research\\experiments\\generated\\PROD-048C-german-wording-feedback-patch\\native_german_followup_review.html
```

The `Preisfrage` group is marked `Erneut prüfen`. Previously accepted topics are marked `Bereits teilweise geprüft`. Unreviewed groups remain marked `Noch nicht geprüft`.

## Metrics

- Original German case count: `{summary['original_german_case_count']}`
- Follow-up group count: `{summary['followup_group_count']}`
- Erneut prüfen groups: `{summary['erneut_pruefen_group_count']}`
- Bereits teilweise geprüft groups: `{summary['bereits_teilweise_geprueft_group_count']}`
- Noch nicht geprüft groups: `{summary['noch_nicht_geprueft_group_count']}`
- Safety boundary preservation passed: `{summary['safety_boundary_preservation_passed']}`
- JSON import enabled in follow-up HTML: `{summary['json_import_enabled']}`

## Boundaries

- Runtime behavior changed: `true`, scoped to German plain price-first wording only.
- Runtime policy changed: `false`
- Call-control behavior changed: `false`
- Customer-move classification changed: `false`
- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`

## Next Checkpoint

Recommended next checkpoint: `{NEXT_CHECKPOINT_ID}`.
"""


def build_readme_de() -> str:
    return """# Prüfung deutscher Telefonantworten - Folgeprüfung

Diese Datei gehört zur Folgeprüfung nach der ersten Rückmeldung. Die erste Rückmeldung betraf die Preisantwort.

## Was hat sich geändert?

Die Preisantwort wurde gekürzt. Der letzte Satz über Zahlung und Vertragsabschluss wurde aus der normalen Preisantwort entfernt, weil er in der ersten Rückmeldung zu stark auf das Thema Zahlung gelenkt hat.

## Was soll geprüft werden?

Bitte prüfen Sie besonders die Preisantwort noch einmal. Einige andere Antwortgruppen wurden bereits teilweise geprüft. Viele Antwortgruppen sind noch nicht geprüft.

Bitte bewerten Sie nur die deutsche Formulierung. Es geht nicht um eine Rechtsprüfung und nicht um eine Bewertung des Produkts.

## So öffnen Sie die Prüfung

Öffnen Sie diese Datei im Browser:

```text
native_german_followup_review.html
```

Es ist kein Server nötig.

## Speichern und Exportieren

- Mit "Zwischenstand im Browser speichern" speichern Sie Ihre Eingaben im Browser.
- Mit "Zwischenstand laden" laden Sie gespeicherte Eingaben.
- Mit "Bewertung aus JSON laden" können Sie eine zuvor heruntergeladene Bewertung wieder in die Seite laden.
- Mit "Bewertung als JSON herunterladen" exportieren Sie die Bewertung als JSON.
- Mit "Bewertung als CSV herunterladen" exportieren Sie die Bewertung als CSV.

Bitte senden Sie die heruntergeladene JSON- oder CSV-Datei an Tarik zurück.
"""


def main() -> None:
    grouped_packet = read_json(GROUPED_PACKET_PATH)
    prod_048b_result = read_json(PROD_048B_RESULT_PATH)
    followup_plan = read_json(FOLLOWUP_PLAN_PATH)
    reviewed_items = read_json(REVIEWED_ITEMS_PATH)["items"]
    revision_candidates = read_json(REVISION_CANDIDATES_PATH)["items"]

    before_after, patch_results, safety_results = build_price_patch_results()
    followup_groups = build_followup_groups(grouped_packet, followup_plan)
    packet = build_packet(followup_groups, prod_048b_result["summary"])

    status_counts = {
        "Erneut prüfen": sum(1 for group in followup_groups if group["status_de"] == "Erneut prüfen"),
        "Bereits teilweise geprüft": sum(1 for group in followup_groups if group["status_de"] == "Bereits teilweise geprüft"),
        "Noch nicht geprüft": sum(1 for group in followup_groups if group["status_de"] == "Noch nicht geprüft"),
    }
    original_case_count = sum(len(group["original_case_ids"]) for group in followup_groups)
    safety_passed = all(item["passed"] for item in safety_results)
    price_patched = all(item["passed"] for item in patch_results)
    summary = {
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "reviewer_name_or_initials": prod_048b_result["summary"]["reviewer_name_or_initials"],
        "reviewer_native_german": prod_048b_result["summary"]["reviewer_native_german"],
        "reviewed_item_count_from_prod_048b": prod_048b_result["summary"]["reviewed_item_count"],
        "unreviewed_item_count_from_prod_048b": prod_048b_result["summary"]["unreviewed_item_count"],
        "price_first_wording_patched": price_patched,
        "price_revision_candidate_count": len(revision_candidates),
        "original_german_case_count": original_case_count,
        "followup_group_count": len(followup_groups),
        "erneut_pruefen_group_count": status_counts["Erneut prüfen"],
        "bereits_teilweise_geprueft_group_count": status_counts["Bereits teilweise geprüft"],
        "noch_nicht_geprueft_group_count": status_counts["Noch nicht geprüft"],
        "safety_boundary_preservation_passed": safety_passed,
        "json_import_enabled": True,
        "runtime_behavior_changed": True,
        "runtime_behavior_change_scope": "german_plain_price_first_wording_only",
        **BOUNDARY_FALSE_SUMMARY,
    }

    outputs = {
        "result": OUT_DIR / "result.json",
        "report": OUT_DIR / "report.md",
        "before_after": OUT_DIR / "price_feedback_patch_before_after.json",
        "patch_results": OUT_DIR / "price_feedback_patch_results.json",
        "safety": OUT_DIR / "safety_boundary_preservation_results.json",
        "review_html": OUT_DIR / "prod_048c_review.html",
        "followup_html": OUT_DIR / "native_german_followup_review.html",
        "followup_packet": OUT_DIR / "native_german_followup_review_packet.json",
        "readme_de": OUT_DIR / "native_german_followup_review_readme_de.md",
        "table_csv": OUT_DIR / "native_german_followup_review_table.csv",
        "export_schema": OUT_DIR / "native_german_followup_review_export_schema.json",
    }

    write_json(outputs["before_after"], {"items": before_after})
    write_json(outputs["patch_results"], {"items": patch_results})
    write_json(outputs["safety"], {"items": safety_results})
    write_json(outputs["followup_packet"], packet)
    write_json(outputs["export_schema"], build_export_schema())
    write_text(outputs["table_csv"], build_table_csv(followup_groups))
    write_text(outputs["followup_html"], build_followup_html(followup_groups))
    write_text(outputs["readme_de"], build_readme_de())
    write_text(outputs["review_html"], build_internal_review_html(summary, patch_results[0]["runtime_decision"]["agent_response"]))
    write_text(outputs["report"], build_report(summary))

    result = {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_id": SOURCE_CHECKPOINT_ID,
        "summary": summary,
        "outputs": {key: rel(path) for key, path in outputs.items()},
        "dependencies": {key: rel(path) for key, path in DEPENDENCY_RESULTS.items()},
        "validation": {"passed": price_patched and safety_passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }
    write_json(outputs["result"], result)
    print(f"Wrote {CHECKPOINT_ID} artifacts to {rel(OUT_DIR)}")


if __name__ == "__main__":
    main()
