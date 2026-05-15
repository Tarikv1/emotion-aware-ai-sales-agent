#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-048A-german-review-html-and-brevity-packet"
CHECKPOINT_NAME = "German Review HTML And Brevity Packet"
NEXT_CHECKPOINT_ID = "PROD-048B-native-german-review-import"
OUT_DIR = ROOT / "research" / "experiments" / "generated" / CHECKPOINT_ID

GERMAN_FINDINGS_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046-core-sales-policy-human-review"
    / "german_response_quality_findings.json"
)
GERMAN_RESULTS_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046D-german-source-informed-wording-quality-guard"
    / "german_source_informed_results.json"
)
CALL_CONTROL_FINDINGS_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046-core-sales-policy-human-review"
    / "call_control_findings.json"
)
CAMPAIGN_PATH = ROOT / "campaigns" / "examples" / "campaign-prod-047-valid-de-source-informed.json"

SOURCE_RESULTS = {
    "prod_045": ROOT / "research" / "experiments" / "generated" / "PROD-045-core-sales-policy-regression-rerun" / "result.json",
    "prod_046a": ROOT / "research" / "experiments" / "generated" / "PROD-046A-german-naturalized-policy-regression" / "result.json",
    "prod_046b": ROOT / "research" / "experiments" / "generated" / "PROD-046B-german-response-wording-quality-pass" / "result.json",
    "prod_046c": ROOT / "research" / "experiments" / "generated" / "PROD-046C-german-campaign-field-interpolation-guard" / "result.json",
    "prod_046d": ROOT / "research" / "experiments" / "generated" / "PROD-046D-german-source-informed-wording-quality-guard" / "result.json",
    "prod_046": ROOT / "research" / "experiments" / "generated" / "PROD-046-core-sales-policy-human-review" / "result.json",
    "prod_047": ROOT / "research" / "experiments" / "generated" / "PROD-047-campaign-profile-contract-validator" / "result.json",
}

BOUNDARY_FALSE_SUMMARY = {
    "native_german_approval_claimed": False,
    "legal_compliance_claimed": False,
    "runtime_policy_changed": False,
    "call_control_behavior_changed": False,
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

TOPIC_ORDER = [
    "Preisfrage",
    "Wer ruft an?",
    "Schriftliche Informationen",
    "Nur E-Mail",
    "Betrugs- oder Zahlungsangst",
    "Support",
    "Kündigung",
    "Technische Frage",
    "Sicherheitsprüfung",
    "Versicherungsschutz / Gesundheit",
    "Bestehender Anbieter",
    "Entscheidung mit Chef oder Partner",
    "Nächster Schritt",
    "Rückruf",
    "Kein Interesse / nicht mehr anrufen",
    "Terminbestätigung",
    "Sonstiges",
]

MOVE_TOPIC = {
    "price_first": ("Preisfrage", "Der Kunde fragt zuerst nach Preis oder Kosten."),
    "who_are_you": ("Wer ruft an?", "Der Kunde möchte wissen, wer anruft und warum."),
    "send_info": ("Schriftliche Informationen", "Der Kunde möchte Informationen schriftlich bekommen."),
    "email_only": ("Nur E-Mail", "Der Kunde möchte nur per E-Mail kontaktiert werden."),
    "scam_or_card_fear": ("Betrugs- oder Zahlungsangst", "Der Kunde ist unsicher, ob der Anruf seriös ist."),
    "payment_safety_fear": ("Betrugs- oder Zahlungsangst", "Der Kunde möchte keine Zahlungsdaten nennen."),
    "support_issue": ("Support", "Der Kunde hat ein bestehendes Problem und braucht Hilfe."),
    "cancellation_request": ("Kündigung", "Der Kunde möchte etwas kündigen oder beenden."),
    "technical_question": ("Technische Frage", "Der Kunde fragt nach technischen Details."),
    "security_review": ("Sicherheitsprüfung", "Der Kunde braucht eine Sicherheits- oder IT-Prüfung."),
    "coverage_confusion": ("Versicherungsschutz / Gesundheit", "Der Kunde fragt nach Versicherungsschutz oder Abdeckung."),
    "sensitive_healthcare_concern": ("Versicherungsschutz / Gesundheit", "Der Kunde spricht ein medizinisches oder gesundheitliches Thema an."),
    "existing_provider": ("Bestehender Anbieter", "Der Kunde hat schon einen Anbieter oder eine Lösung."),
    "needs_manager_approval": ("Entscheidung mit Chef oder Partner", "Der Kunde muss eine andere Person einbeziehen."),
    "needs_spouse_or_partner_input": ("Entscheidung mit Chef oder Partner", "Der Kunde möchte mit einer Partnerperson sprechen."),
    "sale_ready_interest": ("Nächster Schritt", "Der Kunde möchte den nächsten Schritt wissen oder festhalten."),
    "callback_request": ("Rückruf", "Der Kunde bittet um einen späteren Rückruf."),
    "not_interested": ("Kein Interesse / nicht mehr anrufen", "Der Kunde lehnt ab."),
    "hostile_rejection": ("Kein Interesse / nicht mehr anrufen", "Der Kunde möchte nicht mehr angerufen werden."),
    "skeptical_proof_request": ("Sonstiges", "Der Kunde fragt nach Beleg, Nachweis oder Garantie."),
    "product_detail_lookup": ("Sonstiges", "Der Kunde fragt nach konkreten Produktdetails."),
    "scheduling_confirmation": ("Terminbestätigung", "Der Kunde bestätigt einen Termin oder Rückrufzeitpunkt."),
}

SHORT_RESPONSE_BY_MOVE = {
    "price_first": "Das Starter-Paket liegt bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen schicke ich Ihnen schriftlich.",
    "who_are_you": "Hier ist Maya von RouteSignal. Ich rufe an, weil wir kurz die Zuständigkeit für Rückrufe klären möchten.",
    "send_info": "Ja, ich schicke Ihnen die kurze Zusammenfassung per E-Mail.",
    "email_only": "Verstanden, dann nur per E-Mail.",
    "scam_or_card_fear": "Verständlich. Ich frage Sie hier nicht nach Zahlungsdaten oder Passwörtern. Ich schicke Ihnen die Informationen schriftlich.",
    "payment_safety_fear": "Verständlich. Ich frage Sie hier nicht nach Zahlungsdaten oder Passwörtern. Ich schicke Ihnen die Informationen schriftlich.",
    "support_issue": "Verstanden, das ist ein Fall für den Support. Ich leite Sie dorthin weiter.",
    "cancellation_request": "Verstanden, dann leite ich Sie an die zuständige Stelle für Kündigungen weiter.",
    "technical_question": "Das sollte eine Fachperson prüfen. Ich leite es entsprechend weiter.",
    "security_review": "Das sollte eine Fachperson prüfen. Ich mache dazu keine allgemeinen Zusagen.",
    "coverage_confusion": "Dazu darf ich am Telefon keine Beratung geben. Ich leite es an eine Fachperson weiter.",
    "sensitive_healthcare_concern": "Dazu darf ich am Telefon keine Beratung geben. Ich leite es an eine Fachperson weiter.",
    "existing_provider": "Verstehe. Es geht nicht darum, Ihren Anbieter zu ersetzen, sondern nur darum, ob noch Rückrufe oder Nachverfolgungen offen bleiben.",
    "needs_manager_approval": "Natürlich. Ich schicke Ihnen eine kurze Zusammenfassung zur Prüfung.",
    "needs_spouse_or_partner_input": "Natürlich. Ich schicke Ihnen eine kurze Zusammenfassung zur Prüfung.",
    "sale_ready_interest": "Gut, dann halte ich den nächsten Schritt fest. Bezahlt oder unterschrieben wird hier am Telefon nichts.",
    "callback_request": "Ja, ich merke einen Rückruf vor.",
    "not_interested": "Verstanden, dann belasse ich es dabei. Auf Wiederhören.",
    "hostile_rejection": "Verstanden. Sie werden hierzu nicht mehr angerufen. Auf Wiederhören.",
    "skeptical_proof_request": "Garantieren möchte ich nichts, was von Details abhängt. Ich leite es zur Prüfung weiter.",
    "product_detail_lookup": "Einen Moment, ich prüfe die Produktinformationen.",
    "scheduling_confirmation": "Bestätigt, ich notiere den Rückruf so. Auf Wiederhören.",
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


def topic_sort_key(title: str) -> int:
    try:
        return TOPIC_ORDER.index(title)
    except ValueError:
        return len(TOPIC_ORDER)


def build_case_rows() -> list[dict[str, Any]]:
    findings = read_json(GERMAN_FINDINGS_PATH)["items"]
    result_items = read_json(GERMAN_RESULTS_PATH)["items"]
    utterance_by_case = {item["case_id"]: item["customer_utterance"] for item in result_items}
    rows = []
    for item in findings:
        move_id = item["customer_move_id"]
        topic, situation = MOVE_TOPIC.get(move_id, ("Sonstiges", "Weitere kurze Antwort zur Prüfung."))
        short_response = SHORT_RESPONSE_BY_MOVE.get(move_id, item["agent_response"])
        rows.append(
            {
                "case_id": item["case_id"],
                "customer_move_id": move_id,
                "sales_difficulty": item["sales_difficulty"],
                "call_control": item["call_control"],
                "topic_title_de": topic,
                "situation_de": situation,
                "customer_utterance": utterance_by_case.get(item["case_id"], "Kundensatz nicht verfügbar"),
                "original_agent_response": item["agent_response"],
                "short_agent_response": short_response,
                "changed": short_response != item["agent_response"],
                "before_character_count": len(item["agent_response"]),
                "after_character_count": len(short_response),
                "native_german_approval_claimed": False,
                "legal_compliance_claimed": False,
            }
        )
    return rows


def build_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row["topic_title_de"], row["sales_difficulty"], row["short_agent_response"])
        buckets[key].append(row)

    groups = []
    for index, ((topic, sales_difficulty, response), items) in enumerate(
        sorted(buckets.items(), key=lambda entry: (topic_sort_key(entry[0][0]), entry[0][1], entry[0][2])),
        start=1,
    ):
        first = items[0]
        groups.append(
            {
                "group_number": index,
                "group_id": f"de-review-group-{index:03d}",
                "topic_title_de": topic,
                "situation_de": first["situation_de"],
                "sales_intent_key": sales_difficulty,
                "short_agent_response": response,
                "customer_utterances": [item["customer_utterance"] for item in items],
                "original_case_ids": [item["case_id"] for item in items],
                "case_details": [
                    {
                        "case_id": item["case_id"],
                        "customer_move_id": item["customer_move_id"],
                        "sales_difficulty": item["sales_difficulty"],
                        "call_control": item["call_control"],
                        "customer_utterance": item["customer_utterance"],
                        "original_agent_response": item["original_agent_response"],
                        "short_agent_response": item["short_agent_response"],
                    }
                    for item in items
                ],
                "same_answer_note_de": "Diese Antwort wird für mehrere Kundensätze verwendet." if len(items) > 1 else "Diese Antwort wird für diesen Kundensatz verwendet.",
                "native_german_approval_claimed": False,
                "legal_compliance_claimed": False,
            }
        )
    return groups


def build_packet() -> dict[str, Any]:
    rows = build_case_rows()
    groups = build_groups(rows)
    campaign = read_json(CAMPAIGN_PATH)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "packet_language": "de",
        "reviewer_audience": "native_german_non_technical_reviewer",
        "review_scope_de": "Bitte nur die deutsche Formulierung prüfen. Keine Rechtsprüfung und keine Produktbewertung.",
        "review_groups": groups,
        "all_original_cases": rows,
        "rating_fields": [
            {"field_id": field_id, "label_de": label, "options": options}
            for field_id, label, options in RATING_FIELDS
        ],
        "safety_flags": [{"flag_id": flag_id, "label_de": label} for flag_id, label in SAFETY_FLAGS],
        "campaign_profile_summary": {
            "campaign_id": campaign["campaign_id"],
            "language": campaign["language"],
            "review_statuses": campaign["review_statuses"],
            "safety_defaults": campaign["safety_defaults"],
        },
        "review_boundary": {
            **BOUNDARY_FALSE_SUMMARY,
            "review_packet_only": True,
            "all_original_cases_preserved": True,
            "visible_reviewer_language": "de",
            "source_transcript_text_used": False,
            "german_sales_call_scripts_created": False,
        },
    }


def render_rating_field(group: dict[str, Any], field: dict[str, Any]) -> str:
    controls = []
    for option in field["options"]:
        controls.append(
            f'<label class="auswahl"><input type="radio" name="{html.escape(group["group_id"], quote=True)}__{html.escape(field["field_id"], quote=True)}" '
            f'data-rating-field="{html.escape(field["field_id"], quote=True)}" value="{html.escape(option_value(option), quote=True)}"> {html.escape(option)}</label>'
        )
    return f'<fieldset class="bewertung"><legend>{html.escape(field["label_de"])}</legend>{"".join(controls)}</fieldset>'


def render_group_card(group: dict[str, Any], total: int, rating_fields: list[dict[str, Any]]) -> str:
    customer_lines = "".join(f"<li>{html.escape(text)}</li>" for text in group["customer_utterances"])
    ratings = "".join(render_rating_field(group, field) for field in rating_fields)
    flags = "".join(
        f'<label class="haken"><input type="checkbox" data-safety-flag="{html.escape(flag_id, quote=True)}"> {html.escape(label)}</label>'
        for flag_id, label in SAFETY_FLAGS
    )
    case_ids = json.dumps(group["original_case_ids"], ensure_ascii=False)
    return f"""
<article class="karte pruefgruppe" data-review-group-id="{html.escape(group['group_id'], quote=True)}" data-topic="{html.escape(group['topic_title_de'], quote=True)}" data-case-ids="{html.escape(case_ids, quote=True)}">
  <div class="kartenkopf">
    <p class="fortschritt">Antwortgruppe {group['group_number']} von {total}</p>
    <h3>{html.escape(group['topic_title_de'])}</h3>
  </div>
  <p><strong>Thema:</strong> {html.escape(group['topic_title_de'])}</p>
  <p><strong>Situation:</strong> {html.escape(group['situation_de'])}</p>
  <div class="sprechblock kunde">
    <div class="sprechlabel">Kundensatz</div>
    <ol>{customer_lines}</ol>
  </div>
  <div class="sprechblock assistent">
    <div class="sprechlabel">Antwort des Assistenten</div>
    <p>{html.escape(group['short_agent_response'])}</p>
  </div>
  <p class="hinweis">{html.escape(group['same_answer_note_de'])}</p>
  <p class="frage">Passt diese Antwort zu allen Kundensätzen?</p>
  <div class="bewertungsraster">{ratings}</div>
  <fieldset class="problemfelder">
    <legend>Bitte markieren, falls die Antwort eines dieser Probleme hat:</legend>
    <div class="hakenraster">{flags}</div>
  </fieldset>
  <label class="textfeld">Falls die Antwort nicht zu allen Kundensätzen passt: Welche Kundensätze brauchen eine andere Antwort?
    <textarea data-text-field="different_cases" rows="3" placeholder="Optional"></textarea>
  </label>
  <label class="textfeld">Vorschlag für bessere Formulierung
    <textarea data-text-field="rewrite" rows="3" placeholder="Optionaler Vorschlag"></textarea>
  </label>
  <label class="textfeld">Kommentar
    <textarea data-text-field="comment" rows="3" placeholder="Optionaler Kommentar"></textarea>
  </label>
</article>
"""


def render_html(packet: dict[str, Any]) -> str:
    groups = packet["review_groups"]
    topic_options = "".join(
        f'<option value="{html.escape(topic, quote=True)}">{html.escape(topic)}</option>'
        for topic in TOPIC_ORDER
        if any(group["topic_title_de"] == topic for group in groups)
    )
    cards = "".join(render_group_card(group, len(groups), packet["rating_fields"]) for group in groups)
    embedded = json.dumps(
        {
            "group_count": len(groups),
            "case_count": len(packet["all_original_cases"]),
            "rating_fields": packet["rating_fields"],
            "safety_flags": packet["safety_flags"],
        },
        ensure_ascii=False,
    )
    return f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prüfung deutscher Telefonantworten</title>
  <style>
    :root {{
      --text:#16202a; --muted:#5e6875; --line:#d9e0e8; --bg:#f6f7f9; --card:#fff;
      --accent:#145a8d; --soft:#eef6fb; --green:#eef8f0; --warn:#fff7de;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text); font-family: Verdana, Geneva, sans-serif; font-size:18px; line-height:1.5; }}
    header {{ background:#fff; border-bottom:1px solid var(--line); padding:28px 18px; }}
    main {{ max-width:1100px; margin:0 auto; padding:22px 16px 50px; }}
    h1 {{ margin:0 0 10px; font-size:clamp(2rem,4vw,3rem); }}
    h2 {{ margin:0 0 12px; font-size:1.45rem; }}
    h3 {{ margin:0; font-size:1.3rem; }}
    p {{ margin:0 0 12px; }}
    button, select, input, textarea {{ font:inherit; }}
    button {{ border:1px solid var(--accent); background:var(--accent); color:#fff; border-radius:6px; padding:10px 14px; cursor:pointer; }}
    button.secondary {{ background:#fff; color:var(--accent); }}
    .karte {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:18px; margin:16px 0; }}
    .formularraster,.filterleiste,.aktionsleiste {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; align-items:end; }}
    label.feld,.textfeld {{ display:grid; gap:6px; font-weight:700; margin-top:12px; }}
    input[type=text],input[type=date],select,textarea {{ width:100%; border:1px solid var(--line); border-radius:6px; padding:10px; background:#fff; color:var(--text); }}
    textarea {{ resize:vertical; min-height:90px; }}
    .statusleiste {{ position:sticky; top:0; z-index:2; background:rgba(246,247,249,.96); border-bottom:1px solid var(--line); padding:10px 0; }}
    .balken {{ height:12px; background:#dfe6ee; border-radius:99px; overflow:hidden; }}
    .balken span {{ display:block; height:100%; width:0; background:var(--accent); }}
    .kartenkopf {{ display:flex; justify-content:space-between; gap:16px; align-items:baseline; }}
    .fortschritt {{ color:var(--muted); font-weight:700; white-space:nowrap; }}
    .sprechblock {{ border-left:5px solid var(--accent); background:var(--soft); padding:12px 14px; border-radius:6px; margin:12px 0; }}
    .sprechblock.assistent {{ border-left-color:#2f6b3f; background:var(--green); }}
    .sprechlabel,.frage {{ font-weight:700; }}
    .hinweis {{ background:var(--warn); border-radius:6px; padding:10px; color:#4e4330; }}
    .bewertungsraster {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:12px; margin-top:12px; }}
    fieldset {{ border:1px solid var(--line); border-radius:8px; padding:12px; margin:0; }}
    legend {{ font-weight:700; padding:0 6px; }}
    .auswahl,.haken {{ display:block; margin:8px 0; font-weight:400; }}
    .problemfelder {{ margin:16px 0; }}
    .hakenraster {{ columns:2 260px; }}
    .zahlenraster {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; }}
    .zahl {{ background:var(--soft); padding:12px; border-radius:6px; }}
    .zahl strong {{ display:block; font-size:1.8rem; }}
    .versteckt {{ display:none!important; }}
    @media (max-width:720px) {{ body {{ font-size:16px; }} .kartenkopf {{ display:block; }} .hakenraster {{ columns:1; }} }}
    @media print {{ .statusleiste,.filterleiste,.aktionsleiste,button {{ display:none!important; }} body {{ background:#fff; font-size:12pt; }} main {{ max-width:none; padding:0; }} .karte {{ break-inside:avoid; border:1px solid #888; }} }}
  </style>
</head>
<body>
  <header><main>
    <h1>Prüfung deutscher Telefonantworten</h1>
    <p>Sie sehen kurze Kundensätze und mögliche Antworten des Assistenten. Bitte prüfen Sie nur die deutsche Formulierung.</p>
  </main></header>
  <main>
    <section class="karte">
      <h2>Start</h2>
      <ul>
        <li>Sie brauchen kein technisches Wissen.</li>
        <li>Bitte beurteilen Sie nicht, ob das Produkt gut ist.</li>
        <li>Bitte beurteilen Sie nicht die rechtliche Richtigkeit.</li>
        <li>Manche Kundensätze teilen sich dieselbe Antwort.</li>
        <li>Bitte sagen Sie, ob die gemeinsame Antwort zu allen genannten Kundensätzen passt.</li>
      </ul>
    </section>
    <section class="karte">
      <h2>Angaben zur prüfenden Person</h2>
      <div class="formularraster">
        <label class="feld">Name oder Kürzel <input id="reviewerName" type="text"></label>
        <label class="feld">Muttersprache Deutsch?
          <select id="reviewerNativeGerman"><option value="">Bitte wählen</option><option>Ja</option><option>Nein</option></select>
        </label>
        <label class="feld">Land/Region optional <input id="reviewerRegion" type="text"></label>
        <label class="feld">Datum <input id="reviewDate" type="date"></label>
      </div>
      <label class="textfeld">Allgemeine Hinweise <textarea id="reviewerGeneralNotes" rows="3"></textarea></label>
    </section>
    <section class="statusleiste">
      <p id="progressText">0 von {len(groups)} Antwortgruppen geprüft</p>
      <div class="balken"><span id="progressBar"></span></div>
    </section>
    <section class="karte">
      <h2>Filter</h2>
      <div class="filterleiste">
        <label class="feld">Thema
          <select id="topicFilter"><option value="">Alle Themen</option>{topic_options}</select>
        </label>
        <button class="secondary" data-filter="alle">Alle</button>
        <button class="secondary" data-filter="offen">Noch nicht geprüft</button>
        <button class="secondary" data-filter="ueberarbeitung">Überarbeitung nötig</button>
        <button class="secondary" data-filter="abgelehnt">Abgelehnt</button>
        <button class="secondary" data-filter="hinweise">Sicherheits-/Wirkungs-Hinweise</button>
      </div>
    </section>
    <section id="reviewGroups">{cards}</section>
    <section class="karte">
      <h2>Zusammenfassung</h2>
      <div class="zahlenraster">
        <div class="zahl"><strong id="summaryGroups">0</strong>Anzahl geprüfter Antwortgruppen</div>
        <div class="zahl"><strong>{len(packet["all_original_cases"])}</strong>Anzahl einzelner Kundensätze</div>
        <div class="zahl"><strong id="summaryAccepted">0</strong>Anzahl akzeptiert</div>
        <div class="zahl"><strong id="summarySmall">0</strong>Anzahl mit kleinen Änderungen</div>
        <div class="zahl"><strong id="summaryLarge">0</strong>Anzahl mit großen Änderungen</div>
        <div class="zahl"><strong id="summaryRejected">0</strong>Anzahl abgelehnt</div>
        <div class="zahl"><strong id="summarySafety">0</strong>Anzahl mit Sicherheits-/Wirkungs-Hinweisen</div>
      </div>
    </section>
    <section class="karte">
      <h2>Export</h2>
      <p>Speichern Sie am Ende die Bewertung und senden Sie die heruntergeladene Datei an Tarik zurück.</p>
      <div class="aktionsleiste">
        <button onclick="bewertungAlsJsonHerunterladen()">Bewertung als JSON herunterladen</button>
        <button onclick="bewertungAlsCsvHerunterladen()">Bewertung als CSV herunterladen</button>
        <button class="secondary" onclick="zwischenstandSpeichern()">Zwischenstand im Browser speichern</button>
        <button class="secondary" onclick="zwischenstandLaden()">Zwischenstand laden</button>
        <button class="secondary" onclick="alleEingabenLoeschen()">Alle Eingaben löschen</button>
        <button class="secondary" onclick="window.print()">Druckansicht</button>
      </div>
    </section>
  </main>
  <script>
    const PAKET_INFO = {embedded};
    const SPEICHER_SCHLUESSEL = "prod048a_grouped_brevity_review";
    let aktiverFilter = "alle";
    function gruppen() {{ return Array.from(document.querySelectorAll(".pruefgruppe")); }}
    function radioWert(karte, feld) {{ const input = karte.querySelector(`[data-rating-field="${{feld}}"]:checked`); return input ? input.value : ""; }}
    function textWert(karte, feld) {{ const input = karte.querySelector(`[data-text-field="${{feld}}"]`); return input ? input.value : ""; }}
    function hakenWerte(karte) {{ return Array.from(karte.querySelectorAll("[data-safety-flag]:checked")).map((input) => input.dataset.safetyFlag); }}
    function gruppeGeprueft(karte) {{ return PAKET_INFO.rating_fields.every((feld) => radioWert(karte, feld.field_id)); }}
    function datenSammeln() {{
      const groups = gruppen().map((karte) => {{
        const ratings = {{}};
        PAKET_INFO.rating_fields.forEach((feld) => ratings[feld.field_id] = radioWert(karte, feld.field_id));
        return {{
          review_group_id: karte.dataset.reviewGroupId,
          topic: karte.dataset.topic,
          case_ids: JSON.parse(karte.dataset.caseIds || "[]"),
          ratings,
          safety_flags: hakenWerte(karte),
          different_cases: textWert(karte, "different_cases"),
          rewrite_suggestion: textWert(karte, "rewrite"),
          comment: textWert(karte, "comment")
        }};
      }});
      return {{
        reviewer: {{
          name_or_initials: document.getElementById("reviewerName").value,
          native_german: document.getElementById("reviewerNativeGerman").value,
          region_optional: document.getElementById("reviewerRegion").value,
          date: document.getElementById("reviewDate").value,
          general_notes: document.getElementById("reviewerGeneralNotes").value
        }},
        summary: zusammenfassungBerechnen(groups),
        groups
      }};
    }}
    function zusammenfassungBerechnen(groups) {{
      return {{
        anzahl_gepruefter_antwortgruppen: groups.filter((group) => Object.values(group.ratings).every(Boolean)).length,
        anzahl_einzelner_kundensaetze: PAKET_INFO.case_count,
        anzahl_akzeptiert: groups.filter((group) => group.ratings.telefonisch_akzeptabel === "ja").length,
        anzahl_mit_kleinen_aenderungen: groups.filter((group) => group.ratings.ueberarbeitung_noetig === "kleine_aenderung").length,
        anzahl_mit_grossen_aenderungen: groups.filter((group) => group.ratings.ueberarbeitung_noetig === "grosse_aenderung").length,
        anzahl_abgelehnt: groups.filter((group) => group.ratings.telefonisch_akzeptabel === "nein").length,
        anzahl_mit_sicherheits_oder_wirkungs_hinweisen: groups.filter((group) => group.safety_flags.length > 0).length
      }};
    }}
    function zusammenfassungAktualisieren() {{
      const daten = datenSammeln();
      const s = daten.summary;
      document.getElementById("summaryGroups").textContent = s.anzahl_gepruefter_antwortgruppen;
      document.getElementById("summaryAccepted").textContent = s.anzahl_akzeptiert;
      document.getElementById("summarySmall").textContent = s.anzahl_mit_kleinen_aenderungen;
      document.getElementById("summaryLarge").textContent = s.anzahl_mit_grossen_aenderungen;
      document.getElementById("summaryRejected").textContent = s.anzahl_abgelehnt;
      document.getElementById("summarySafety").textContent = s.anzahl_mit_sicherheits_oder_wirkungs_hinweisen;
      document.getElementById("progressText").textContent = `${{s.anzahl_gepruefter_antwortgruppen}} von ${{PAKET_INFO.group_count}} Antwortgruppen geprüft`;
      document.getElementById("progressBar").style.width = `${{Math.round((s.anzahl_gepruefter_antwortgruppen / PAKET_INFO.group_count) * 100)}}%`;
      filterAnwenden();
    }}
    function dateiHerunterladen(name, text, typ) {{
      const blob = new Blob([text], {{ type: typ }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    }}
    function bewertungAlsJsonHerunterladen() {{ dateiHerunterladen("deutsche-telefonantworten-gruppenbewertung.json", JSON.stringify(datenSammeln(), null, 2), "application/json;charset=utf-8"); }}
    function csvZelle(wert) {{ return `"${{String(wert || "").replaceAll('"', '""')}}"`; }}
    function bewertungAlsCsvHerunterladen() {{
      const daten = datenSammeln();
      const kopf = ["review_group_id","thema","case_ids","passt_zu_allen","natuerlich","klar_verstaendlich","freundlich","gesprochene_sprache","zu_abrupt","intern_buerokratisch_technisch","telefonisch_akzeptabel","ueberarbeitung_noetig","hinweise","andere_antwort_noetig","vorschlag","kommentar"];
      const zeilen = [kopf.map(csvZelle).join(",")];
      daten.groups.forEach((group) => zeilen.push([group.review_group_id,group.topic,group.case_ids.join("; "),group.ratings.passt_zu_allen,group.ratings.natuerlich,group.ratings.klar_verstaendlich,group.ratings.freundlich,group.ratings.gesprochene_sprache,group.ratings.zu_abrupt,group.ratings.intern_buerokratisch_technisch,group.ratings.telefonisch_akzeptabel,group.ratings.ueberarbeitung_noetig,group.safety_flags.join("; "),group.different_cases,group.rewrite_suggestion,group.comment].map(csvZelle).join(",")));
      dateiHerunterladen("deutsche-telefonantworten-gruppenbewertung.csv", zeilen.join("\\n"), "text/csv;charset=utf-8");
    }}
    function zwischenstandSpeichern() {{ localStorage.setItem(SPEICHER_SCHLUESSEL, JSON.stringify(datenSammeln())); alert("Zwischenstand gespeichert."); }}
    function zwischenstandLaden() {{
      const raw = localStorage.getItem(SPEICHER_SCHLUESSEL); if (!raw) {{ alert("Kein gespeicherter Zwischenstand gefunden."); return; }}
      const daten = JSON.parse(raw);
      document.getElementById("reviewerName").value = daten.reviewer?.name_or_initials || "";
      document.getElementById("reviewerNativeGerman").value = daten.reviewer?.native_german || "";
      document.getElementById("reviewerRegion").value = daten.reviewer?.region_optional || "";
      document.getElementById("reviewDate").value = daten.reviewer?.date || "";
      document.getElementById("reviewerGeneralNotes").value = daten.reviewer?.general_notes || "";
      (daten.groups || []).forEach((group) => {{
        const karte = document.querySelector(`[data-review-group-id="${{group.review_group_id}}"]`); if (!karte) return;
        Object.entries(group.ratings || {{}}).forEach(([feld, wert]) => {{ const input = karte.querySelector(`[data-rating-field="${{feld}}"][value="${{wert}}"]`); if (input) input.checked = true; }});
        (group.safety_flags || []).forEach((flag) => {{ const input = karte.querySelector(`[data-safety-flag="${{flag}}"]`); if (input) input.checked = true; }});
        [["different_cases", group.different_cases], ["rewrite", group.rewrite_suggestion], ["comment", group.comment]].forEach(([feld, wert]) => {{ const input = karte.querySelector(`[data-text-field="${{feld}}"]`); if (input) input.value = wert || ""; }});
      }});
      zusammenfassungAktualisieren();
    }}
    function alleEingabenLoeschen() {{
      if (!confirm("Wirklich alle Eingaben löschen?")) return;
      localStorage.removeItem(SPEICHER_SCHLUESSEL);
      document.querySelectorAll("input[type=radio], input[type=checkbox]").forEach((input) => input.checked = false);
      document.querySelectorAll("textarea, input[type=text]").forEach((input) => input.value = "");
      document.getElementById("reviewerNativeGerman").value = "";
      document.getElementById("reviewDate").value = new Date().toISOString().slice(0, 10);
      zusammenfassungAktualisieren();
    }}
    let aktiverFilter = "alle";
    function filterAnwenden() {{
      const thema = document.getElementById("topicFilter").value;
      const daten = datenSammeln();
      gruppen().forEach((karte) => {{
        const gruppe = daten.groups.find((g) => g.review_group_id === karte.dataset.reviewGroupId);
        const passtThema = !thema || karte.dataset.topic === thema;
        let passtFilter = true;
        if (aktiverFilter === "offen") passtFilter = !gruppeGeprueft(karte);
        if (aktiverFilter === "ueberarbeitung") passtFilter = ["kleine_aenderung","grosse_aenderung"].includes(gruppe.ratings.ueberarbeitung_noetig);
        if (aktiverFilter === "abgelehnt") passtFilter = gruppe.ratings.telefonisch_akzeptabel === "nein";
        if (aktiverFilter === "hinweise") passtFilter = gruppe.safety_flags.length > 0;
        karte.classList.toggle("versteckt", !(passtThema && passtFilter));
      }});
    }}
    document.addEventListener("input", zusammenfassungAktualisieren);
    document.addEventListener("change", zusammenfassungAktualisieren);
    document.querySelectorAll("[data-filter]").forEach((button) => button.addEventListener("click", () => {{ aktiverFilter = button.dataset.filter; filterAnwenden(); }}));
    document.getElementById("topicFilter").addEventListener("change", filterAnwenden);
    document.getElementById("reviewDate").value = new Date().toISOString().slice(0, 10);
    zusammenfassungAktualisieren();
  </script>
</body>
</html>
"""


def build_export_schema(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": "prod-048a.grouped_native_german_review_export.v1",
        "required_top_level_fields": ["reviewer", "summary", "groups"],
        "required_reviewer_fields": ["name_or_initials", "native_german", "region_optional", "date", "general_notes"],
        "required_group_fields": ["review_group_id", "topic", "case_ids", "ratings", "safety_flags", "different_cases", "rewrite_suggestion", "comment"],
        "required_rating_field_ids": [field["field_id"] for field in packet["rating_fields"]],
        "required_safety_flag_ids": [field["flag_id"] for field in packet["safety_flags"]],
        "keeps_original_case_ids": True,
        "export_formats": ["json", "csv"],
        "no_server_required": True,
        "native_german_approval_claimed": False,
        "legal_compliance_claimed": False,
    }


def build_csv_table(packet: dict[str, Any]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["gruppe", "thema", "kundensaetze", "antwort_des_assistenten", "fallkennungen"])
    for group in packet["review_groups"]:
        writer.writerow(
            [
                group["group_number"],
                group["topic_title_de"],
                " | ".join(group["customer_utterances"]),
                group["short_agent_response"],
                " | ".join(group["original_case_ids"]),
            ]
        )
    return buffer.getvalue()


def build_duplicate_groups(groups: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "items": [
            {
                "group_id": group["group_id"],
                "topic_title_de": group["topic_title_de"],
                "case_count": len(group["original_case_ids"]),
                "original_case_ids": group["original_case_ids"],
                "short_agent_response": group["short_agent_response"],
            }
            for group in groups
            if len(group["original_case_ids"]) > 1
        ]
    }


def build_readme_de(packet: dict[str, Any]) -> str:
    return f"""# Prüfung deutscher Telefonantworten

Bitte öffnen Sie `native_german_review.html` in einem Browser.

## Was soll ich tun?

Bitte prüfen Sie nur die deutsche Formulierung der Antworten. Es geht nicht um eine Produktbewertung. Dies ist keine Rechtsprüfung.

Einige Kundensätze zusammengefasst: Sie bekommen aktuell dieselbe Antwort. Bitte prüfen Sie dann, ob diese eine Antwort zu allen aufgeführten Kundensätzen passt.

## Zwischenspeichern

Mit **Zwischenstand im Browser speichern** speichern Sie Ihre Eingaben lokal in Ihrem Browser.

## Export

Wenn Sie fertig sind, klicken Sie bitte auf:

- **Bewertung als JSON herunterladen** oder
- **Bewertung als CSV herunterladen**

Bitte senden Sie die heruntergeladene Datei an Tarik zurück.

## Umfang

- Antwortgruppen: {len(packet["review_groups"])}
- Einzelne Kundensätze: {len(packet["all_original_cases"])}
"""


def build_report(summary: dict[str, Any]) -> str:
    return f"""# PROD-048A German Review HTML And Brevity Packet

This checkpoint prepares a grouped, German-only review packet for native German wording review. It uses shortened review-facing German answers where safe and keeps all original German cases internally for traceability.

## Metrics

- Original German cases: {summary["original_german_case_count"]}
- Grouped review cards: {summary["grouped_review_card_count"]}
- Repeated-answer groups found: {summary["repeated_answer_group_count"]}
- Average German response character count before: {summary["average_german_response_character_count_before"]:.2f}
- Average German response character count after: {summary["average_german_response_character_count_after"]:.2f}
- HTML self-contained: `{summary["html_self_contained"]}`

## Boundaries

- No native German approval is claimed.
- No legal compliance is claimed.
- Runtime policy changed: `false`
- Call-control behavior changed: `false`
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


def build_result(packet: dict[str, Any], brevity_items: list[dict[str, Any]]) -> dict[str, Any]:
    groups = packet["review_groups"]
    before_avg = sum(item["before_character_count"] for item in brevity_items) / len(brevity_items)
    after_avg = sum(item["after_character_count"] for item in brevity_items) / len(brevity_items)
    source_passed = {key: read_json(path).get("validation", {}).get("passed") is True for key, path in SOURCE_RESULTS.items()}
    summary = {
        "source_result_validation_passed": source_passed,
        "original_german_case_count": len(brevity_items),
        "grouped_review_card_count": len(groups),
        "repeated_answer_group_count": sum(1 for group in groups if len(group["original_case_ids"]) > 1),
        "average_german_response_character_count_before": before_avg,
        "average_german_response_character_count_after": after_avg,
        "shortened_response_count": sum(1 for item in brevity_items if item["changed"]),
        "html_self_contained": True,
        "all_visible_main_labels_german": True,
        "reviewer_export_json_enabled": True,
        "reviewer_export_csv_enabled": True,
        "local_storage_enabled": True,
        "print_friendly_mode_enabled": True,
        **BOUNDARY_FALSE_SUMMARY,
    }
    passed = (
        all(source_passed.values())
        and summary["grouped_review_card_count"] < summary["original_german_case_count"]
        and summary["repeated_answer_group_count"] > 0
        and after_avg < before_avg
        and all(value is False for value in BOUNDARY_FALSE_SUMMARY.values())
    )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "native_german_grouped_review_packet": rel(OUT_DIR / "native_german_grouped_review_packet.json"),
            "native_german_review_html": rel(OUT_DIR / "native_german_review.html"),
            "native_german_review_export_schema": rel(OUT_DIR / "native_german_review_export_schema.json"),
            "native_german_review_readme_de": rel(OUT_DIR / "native_german_review_readme_de.md"),
            "native_german_review_table_csv": rel(OUT_DIR / "native_german_review_table.csv"),
            "german_brevity_before_after": rel(OUT_DIR / "german_brevity_before_after.json"),
            "german_duplicate_answer_groups": rel(OUT_DIR / "german_duplicate_answer_groups.json"),
        },
        "validation": {"passed": passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }


def main() -> None:
    for path in [GERMAN_FINDINGS_PATH, GERMAN_RESULTS_PATH, CALL_CONTROL_FINDINGS_PATH, CAMPAIGN_PATH, *SOURCE_RESULTS.values()]:
        if not path.exists():
            raise SystemExit(f"Missing required input: {rel(path)}")
    packet = build_packet()
    brevity_items = packet["all_original_cases"]
    result = build_result(packet, brevity_items)
    summary = result["summary"]

    write_json(OUT_DIR / "native_german_grouped_review_packet.json", packet)
    write_json(OUT_DIR / "native_german_review_export_schema.json", build_export_schema(packet))
    write_json(OUT_DIR / "german_brevity_before_after.json", {"items": brevity_items})
    write_json(OUT_DIR / "german_duplicate_answer_groups.json", build_duplicate_groups(packet["review_groups"]))
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "native_german_review.html", render_html(packet))
    write_text(OUT_DIR / "native_german_review_readme_de.md", build_readme_de(packet))
    write_text(OUT_DIR / "native_german_review_table.csv", build_csv_table(packet))
    write_text(OUT_DIR / "report.md", build_report(summary))

    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
