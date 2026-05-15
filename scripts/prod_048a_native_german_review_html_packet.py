#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
from io import StringIO
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_ID = "PROD-048A-native-german-review-html-packet"
CHECKPOINT_NAME = "Native German Review HTML Packet"
SOURCE_CHECKPOINTS = [
    "PROD-046-core-sales-policy-human-review",
    "PROD-047-campaign-profile-contract-validator",
]
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
CALL_CONTROL_FINDINGS_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046-core-sales-policy-human-review"
    / "call_control_findings.json"
)
GERMAN_RESULT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046D-german-source-informed-wording-quality-guard"
    / "german_source_informed_results.json"
)
PROD_046_RESULT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-046-core-sales-policy-human-review"
    / "result.json"
)
PROD_047_RESULT_PATH = (
    ROOT
    / "research"
    / "experiments"
    / "generated"
    / "PROD-047-campaign-profile-contract-validator"
    / "result.json"
)
CAMPAIGN_PATH = ROOT / "campaigns" / "examples" / "campaign-prod-047-valid-de-source-informed.json"

BOUNDARY_FALSE_SUMMARY = {
    "native_german_approval_claimed": False,
    "legal_compliance_claimed": False,
    "runtime_behavior_changed": False,
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
    "price_first",
    "who_are_you",
    "send_info",
    "email_only",
    "scam_or_card_fear",
    "payment_safety_fear",
    "support_issue",
    "cancellation_request",
    "technical_question",
    "security_review",
    "coverage_confusion",
    "sensitive_healthcare_concern",
    "existing_provider",
    "needs_manager_approval",
    "needs_spouse_or_partner_input",
    "sale_ready_interest",
    "callback_request",
    "not_interested",
    "hostile_rejection",
    "skeptical_proof_request",
    "product_detail_lookup",
    "scheduling_confirmation",
]

TOPIC_DE = {
    "price_first": {
        "title": "Preisfrage",
        "description": "Der Kunde fragt früh nach Kosten oder Preisrahmen.",
        "situation": "Der Kunde möchte zuerst wissen, was das Angebot kostet.",
    },
    "who_are_you": {
        "title": "Wer ruft an?",
        "description": "Der Kunde möchte wissen, wer anruft und warum.",
        "situation": "Der Kunde ist unsicher, wer am Telefon ist.",
    },
    "send_info": {
        "title": "Schriftliche Informationen",
        "description": "Der Kunde möchte die Informationen erst schriftlich sehen.",
        "situation": "Der Kunde bittet um eine schriftliche Zusammenfassung.",
    },
    "email_only": {
        "title": "Nur E-Mail",
        "description": "Der Kunde möchte nicht weiter telefonieren und bevorzugt E-Mail.",
        "situation": "Der Kunde setzt eine klare E-Mail-Grenze.",
    },
    "scam_or_card_fear": {
        "title": "Betrugsangst",
        "description": "Der Kunde fragt, ob der Anruf seriös ist.",
        "situation": "Der Kunde ist bei dem Anruf vorsichtig und möchte Sicherheit.",
    },
    "payment_safety_fear": {
        "title": "Zahlungsangst",
        "description": "Der Kunde will keine Zahlungs- oder Kartendaten nennen.",
        "situation": "Der Kunde macht deutlich, dass am Telefon keine Zahlungsdaten genannt werden.",
    },
    "support_issue": {
        "title": "Support",
        "description": "Der Kunde hat ein bestehendes Problem und braucht Hilfe.",
        "situation": "Der Kunde beschreibt ein Support-Thema statt Interesse an einem Angebot.",
    },
    "cancellation_request": {
        "title": "Kündigung",
        "description": "Der Kunde möchte kündigen oder etwas beenden.",
        "situation": "Der Kunde spricht eine Kündigung oder Beendigung an.",
    },
    "technical_question": {
        "title": "Technische Frage",
        "description": "Der Kunde fragt nach technischen Details.",
        "situation": "Der Kunde stellt eine technische Frage, die nicht geraten werden sollte.",
    },
    "security_review": {
        "title": "Sicherheitsprüfung",
        "description": "Der Kunde braucht Prüfung durch IT, Security oder Compliance.",
        "situation": "Der Kunde möchte eine Sicherheitsprüfung oder Unterlagen dafür.",
    },
    "coverage_confusion": {
        "title": "Versicherungsschutz / Gesundheit",
        "description": "Der Kunde fragt nach Abdeckung, Tarif, Versicherungsschutz oder Gesundheit.",
        "situation": "Der Kunde fragt nach Versicherungsschutz oder einer ähnlichen fachlichen Grenze.",
    },
    "sensitive_healthcare_concern": {
        "title": "Versicherungsschutz / Gesundheit",
        "description": "Der Kunde spricht ein gesundheitliches oder medizinisches Thema an.",
        "situation": "Der Kunde fragt nach medizinischer oder gesundheitlicher Einordnung.",
    },
    "existing_provider": {
        "title": "Bestehender Anbieter",
        "description": "Der Kunde sagt, dass bereits ein Anbieter oder eine Lösung vorhanden ist.",
        "situation": "Der Kunde verweist auf eine bestehende Lösung.",
    },
    "needs_manager_approval": {
        "title": "Entscheidung mit Chef/Partner",
        "description": "Der Kunde muss intern eine weitere Person einbeziehen.",
        "situation": "Der Kunde kann oder möchte nicht allein entscheiden.",
    },
    "needs_spouse_or_partner_input": {
        "title": "Entscheidung mit Chef/Partner",
        "description": "Der Kunde möchte zu Hause oder mit einer Partnerperson Rücksprache halten.",
        "situation": "Der Kunde braucht eine Entscheidung mit einer weiteren Person.",
    },
    "sale_ready_interest": {
        "title": "Nächster Schritt",
        "description": "Der Kunde zeigt Bereitschaft für den nächsten Schritt.",
        "situation": "Der Kunde signalisiert Interesse und fragt nach dem weiteren Vorgehen.",
    },
    "callback_request": {
        "title": "Rückruf",
        "description": "Der Kunde bittet um einen späteren Rückruf.",
        "situation": "Der Kunde möchte zu einem anderen Zeitpunkt sprechen.",
    },
    "not_interested": {
        "title": "Kein Interesse / nicht mehr anrufen",
        "description": "Der Kunde lehnt freundlich oder knapp ab.",
        "situation": "Der Kunde sagt, dass kein Interesse besteht.",
    },
    "hostile_rejection": {
        "title": "Kein Interesse / nicht mehr anrufen",
        "description": "Der Kunde verlangt, nicht mehr angerufen zu werden.",
        "situation": "Der Kunde setzt eine klare Grenze gegen weitere Anrufe.",
    },
    "skeptical_proof_request": {
        "title": "Nachweis / Zweifel",
        "description": "Der Kunde fragt nach Beleg, Nachweis oder Garantie.",
        "situation": "Der Kunde möchte wissen, ob eine Aussage belegt werden kann.",
    },
    "product_detail_lookup": {
        "title": "Produktdetails",
        "description": "Der Kunde fragt nach konkreten Details des Angebots.",
        "situation": "Der Kunde möchte wissen, was genau enthalten ist.",
    },
    "scheduling_confirmation": {
        "title": "Terminbestätigung",
        "description": "Der Kunde bestätigt einen Zeitpunkt.",
        "situation": "Der Kunde nennt oder bestätigt eine passende Zeit.",
    },
}

RATING_FIELDS = [
    {
        "field_id": "natuerlich",
        "label_de": "Klingt natürlich?",
        "options": ["Ja", "Teilweise", "Nein"],
    },
    {
        "field_id": "klar_verstaendlich",
        "label_de": "Ist die Antwort klar verständlich?",
        "options": ["Ja", "Teilweise", "Nein"],
    },
    {
        "field_id": "freundlich",
        "label_de": "Ist die Antwort freundlich?",
        "options": ["Ja", "Teilweise", "Nein"],
    },
    {
        "field_id": "gesprochene_sprache",
        "label_de": "Klingt die Antwort wie echte gesprochene Sprache?",
        "options": ["Ja", "Teilweise", "Nein"],
    },
    {
        "field_id": "zu_abrupt",
        "label_de": "Klingt die Antwort zu abrupt?",
        "options": ["Nein", "Etwas", "Ja"],
    },
    {
        "field_id": "intern_buerokratisch_technisch",
        "label_de": "Klingt die Antwort intern, bürokratisch oder technisch?",
        "options": ["Nein", "Etwas", "Ja"],
    },
    {
        "field_id": "telefonisch_akzeptabel",
        "label_de": "Würden Sie diese Antwort am Telefon akzeptieren?",
        "options": ["Ja", "Nur mit Änderung", "Nein"],
    },
    {
        "field_id": "ueberarbeitung_noetig",
        "label_de": "Muss die Antwort überarbeitet werden?",
        "options": ["Nein", "Kleine Änderung", "Große Änderung"],
    },
]

SAFETY_FLAGS = [
    ("zu_draengend", "Klingt zu drängend"),
    ("verkaufsdruck", "Klingt wie ein Verkaufsdruck"),
    ("rechtlich_unsicher", "Klingt rechtlich unsicher"),
    ("medizinische_beratung", "Klingt nach medizinischer Beratung"),
    ("versicherungsschutz_beratung", "Klingt nach Beratung zum Versicherungsschutz"),
    ("zahlungsaufforderung", "Klingt nach Zahlungsaufforderung"),
    ("vertragsabschluss", "Klingt nach Vertragsabschluss"),
    ("unhoeflich", "Klingt unhöflich"),
    ("unklar", "Klingt unklar"),
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


def topic_sort_key(item: dict[str, Any]) -> tuple[int, str]:
    move_id = item["customer_move_id"]
    try:
        index = TOPIC_ORDER.index(move_id)
    except ValueError:
        index = len(TOPIC_ORDER)
    return index, item["case_id"]


def build_review_items() -> list[dict[str, Any]]:
    findings = read_json(GERMAN_FINDINGS_PATH)["items"]
    german_results = read_json(GERMAN_RESULT_PATH)["items"]
    by_case = {item["case_id"]: item for item in german_results}
    call_control_items = read_json(CALL_CONTROL_FINDINGS_PATH)["items"]
    call_control_by_case = {item["case_id"]: item for item in call_control_items}

    sorted_findings = sorted(findings, key=topic_sort_key)
    review_items = []
    for index, finding in enumerate(sorted_findings, start=1):
        case_id = finding["case_id"]
        result = by_case.get(case_id, {})
        move_id = finding["customer_move_id"]
        topic = TOPIC_DE.get(
            move_id,
            {
                "title": "Weitere Antwort",
                "description": "Weitere kurze Antwort zur Prüfung.",
                "situation": "Der Kunde sagt etwas Kurzes im Telefonat.",
            },
        )
        review_items.append(
            {
                "review_item_number": index,
                "review_item_id": f"de-review-{index:03d}",
                "source_case_id": case_id,
                "customer_move_id": move_id,
                "topic_id": topic["title"].lower().replace(" ", "-"),
                "topic_title_de": topic["title"],
                "topic_description_de": topic["description"],
                "situation_de": topic["situation"],
                "customer_utterance": result.get("customer_utterance", "Kundensatz nicht verfügbar"),
                "agent_response": finding["agent_response"],
                "review_instruction_de": "Bitte bewerten Sie nur die Formulierung der Antwort.",
                "prior_review_hint_de": build_prior_hint(finding),
                "technical_details": {
                    "source_case_id": case_id,
                    "customer_move_id": move_id,
                    "sales_difficulty": finding.get("sales_difficulty"),
                    "call_control": finding.get("call_control"),
                    "quality_risks": finding.get("quality_risks", {}),
                    "call_control_finding": call_control_by_case.get(case_id),
                },
                "native_german_approval_claimed": False,
                "legal_compliance_claimed": False,
            }
        )
    return review_items


def build_prior_hint(finding: dict[str, Any]) -> str:
    risks = finding.get("quality_risks", {})
    hints = []
    if risks.get("too_abrupt"):
        hints.append("Die Antwort könnte kurz oder abrupt wirken.")
    if risks.get("robotic_or_legalistic"):
        hints.append("Die Antwort könnte etwas steif wirken.")
    if risks.get("internal_sounding"):
        hints.append("Die Antwort könnte intern oder bürokratisch klingen.")
    return " ".join(hints) if hints else "Keine besondere Vorbemerkung."


def build_topic_groups(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        title = item["topic_title_de"]
        if title in seen:
            continue
        seen.add(title)
        groups.append(
            {
                "topic_title_de": title,
                "topic_description_de": item["topic_description_de"],
                "item_count": sum(1 for candidate in items if candidate["topic_title_de"] == title),
            }
        )
    return groups


def campaign_summary(campaign: dict[str, Any]) -> dict[str, Any]:
    fields = campaign.get("fields", {})
    field_summary = {
        field_id: {
            "shape": value.get("shape"),
            "source_boundary": value.get("source_boundary"),
            "review_statuses": value.get("review_statuses", []),
            "customer_facing": value.get("customer_facing"),
        }
        for field_id, value in fields.items()
    }
    return {
        "campaign_id": campaign.get("campaign_id"),
        "language": campaign.get("language"),
        "review_statuses": campaign.get("review_statuses", []),
        "field_count": len(fields),
        "field_summary": field_summary,
        "safety_defaults": campaign.get("safety_defaults", {}),
    }


def build_packet() -> dict[str, Any]:
    items = build_review_items()
    campaign = read_json(CAMPAIGN_PATH)
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "packet_language": "de",
        "reviewer_audience": "native_german_non_technical_reviewer",
        "source_checkpoints": SOURCE_CHECKPOINTS,
        "review_purpose_de": "Prüfung deutscher Telefonantworten durch eine muttersprachliche Person.",
        "review_scope_de": "Bitte nur die deutsche Formulierung prüfen. Keine Rechtsprüfung und keine Produktbewertung.",
        "review_items": items,
        "topic_groups": build_topic_groups(items),
        "rating_fields": RATING_FIELDS,
        "safety_flags": [{"flag_id": flag_id, "label_de": label} for flag_id, label in SAFETY_FLAGS],
        "campaign_profile_summary": campaign_summary(campaign),
        "export_schema_path": rel(OUT_DIR / "native_german_review_export_schema.json"),
        "review_boundary": {
            **BOUNDARY_FALSE_SUMMARY,
            "review_packet_only": True,
            "visible_reviewer_language": "de",
            "non_technical_reviewer_target": True,
            "source_transcript_text_used": False,
            "german_sales_call_scripts_created": False,
        },
    }


def html_attr(text: Any) -> str:
    return html.escape(str(text), quote=True)


def render_rating_field(item: dict[str, Any], field: dict[str, Any]) -> str:
    controls = []
    item_id = item["review_item_id"]
    field_id = field["field_id"]
    for option in field["options"]:
        value = option.lower().replace(" ", "_").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
        controls.append(
            f'<label class="auswahl"><input type="radio" name="{html_attr(item_id)}__{html_attr(field_id)}" '
            f'data-rating-field="{html_attr(field_id)}" value="{html_attr(value)}"> {html.escape(option)}</label>'
        )
    return (
        f'<fieldset class="bewertung"><legend>{html.escape(field["label_de"])}</legend>'
        f'{"".join(controls)}</fieldset>'
    )


def render_item_card(item: dict[str, Any], total: int) -> str:
    rating_html = "".join(render_rating_field(item, field) for field in RATING_FIELDS)
    safety_html = "".join(
        f'<label class="haken"><input type="checkbox" data-safety-flag="{html_attr(flag_id)}"> '
        f"{html.escape(label)}</label>"
        for flag_id, label in SAFETY_FLAGS
    )
    tech = item["technical_details"]
    return f"""
<article class="karte pruefkarte" data-review-item-id="{html_attr(item['review_item_id'])}" data-topic="{html_attr(item['topic_title_de'])}">
  <div class="kartenkopf">
    <p class="fortschritt">Antwort {item['review_item_number']} von {total}</p>
    <h3>{html.escape(item['topic_title_de'])}</h3>
  </div>
  <p class="gruppenhinweis">{html.escape(item['topic_description_de'])}</p>
  <p><strong>Situation:</strong> {html.escape(item['situation_de'])}</p>
  <div class="sprechblock kunde">
    <div class="sprechlabel">Kundensatz</div>
    <p>{html.escape(item['customer_utterance'])}</p>
  </div>
  <div class="sprechblock assistent">
    <div class="sprechlabel">Antwort des Assistenten</div>
    <p>{html.escape(item['agent_response'])}</p>
  </div>
  <p class="hinweis">Bitte bewerten Sie nur die Formulierung der Antwort.</p>
  <p class="vorhinweis">{html.escape(item['prior_review_hint_de'])}</p>
  <div class="bewertungsraster">
    {rating_html}
  </div>
  <fieldset class="problemfelder">
    <legend>Bitte markieren, falls die Antwort eines dieser Probleme hat:</legend>
    <div class="hakenraster">{safety_html}</div>
  </fieldset>
  <label class="textfeld">Vorschlag für bessere Formulierung
    <textarea data-text-field="rewrite" rows="3" placeholder="Optionaler Vorschlag"></textarea>
  </label>
  <label class="textfeld">Kommentar
    <textarea data-text-field="comment" rows="3" placeholder="Optionaler Kommentar"></textarea>
  </label>
  <details class="details">
    <summary>Technische Details anzeigen</summary>
    <dl>
      <dt>Fallkennung</dt><dd>{html.escape(item['source_case_id'])}</dd>
      <dt>Thema-Code</dt><dd>{html.escape(item['customer_move_id'])}</dd>
      <dt>Interne Einstufung</dt><dd>{html.escape(str(tech.get('sales_difficulty')))}</dd>
      <dt>Gesprächssteuerung</dt><dd>{html.escape(str(tech.get('call_control')))}</dd>
    </dl>
  </details>
</article>
"""


def render_html(packet: dict[str, Any]) -> str:
    items = packet["review_items"]
    topic_options = "".join(
        f'<option value="{html_attr(group["topic_title_de"])}">{html.escape(group["topic_title_de"])}</option>'
        for group in packet["topic_groups"]
    )
    topic_summary = "".join(
        f'<li><strong>{html.escape(group["topic_title_de"])}:</strong> '
        f'{html.escape(group["topic_description_de"])} ({group["item_count"]})</li>'
        for group in packet["topic_groups"]
    )
    cards = "".join(render_item_card(item, len(items)) for item in items)
    embedded_packet = json.dumps(
        {
            "checkpoint_id": CHECKPOINT_ID,
            "review_item_count": len(items),
            "rating_fields": RATING_FIELDS,
            "safety_flags": [{"flag_id": flag_id, "label_de": label} for flag_id, label in SAFETY_FLAGS],
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
      --text: #17202a;
      --muted: #5b6470;
      --line: #d8dee6;
      --bg: #f7f8fa;
      --card: #ffffff;
      --accent: #0b5cab;
      --soft: #eef5ff;
      --warn: #fff6df;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      font-size: 18px;
      line-height: 1.5;
    }}
    header.seitenkopf {{
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 28px 20px;
    }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 22px 16px 48px; }}
    h1 {{ margin: 0 0 10px; font-size: clamp(2rem, 4vw, 3rem); }}
    h2 {{ font-size: 1.5rem; margin: 0 0 12px; }}
    h3 {{ margin: 0; font-size: 1.35rem; }}
    p {{ margin: 0 0 12px; }}
    button, select, input, textarea {{
      font: inherit;
    }}
    button {{
      border: 1px solid var(--accent);
      background: var(--accent);
      color: white;
      border-radius: 6px;
      padding: 10px 14px;
      cursor: pointer;
    }}
    button.secondary {{ background: white; color: var(--accent); }}
    .karte {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      margin: 16px 0;
    }}
    .einleitung li {{ margin: 6px 0; }}
    .formularraster, .filterleiste, .aktionsleiste {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      align-items: end;
    }}
    label.feld, .textfeld {{ display: grid; gap: 6px; font-weight: 700; }}
    input[type="text"], input[type="date"], select, textarea {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      background: white;
      color: var(--text);
    }}
    textarea {{ resize: vertical; min-height: 92px; }}
    .statusleiste {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: rgba(247, 248, 250, .96);
      border-bottom: 1px solid var(--line);
      padding: 10px 0;
      backdrop-filter: blur(4px);
    }}
    .balken {{ height: 12px; background: #dfe6ee; border-radius: 99px; overflow: hidden; }}
    .balken span {{ display: block; height: 100%; width: 0; background: var(--accent); }}
    .sprechblock {{
      border-left: 5px solid var(--accent);
      background: var(--soft);
      padding: 12px 14px;
      border-radius: 6px;
      margin: 12px 0;
    }}
    .sprechblock.assistent {{ border-left-color: #366b2f; background: #f1f8ee; }}
    .sprechlabel {{ font-weight: 700; margin-bottom: 6px; }}
    .hinweis, .vorhinweis {{ color: var(--muted); }}
    .vorhinweis {{ background: var(--warn); border-radius: 6px; padding: 10px; }}
    .kartenkopf {{ display: flex; justify-content: space-between; gap: 16px; align-items: baseline; }}
    .fortschritt {{ color: var(--muted); font-weight: 700; white-space: nowrap; }}
    .bewertungsraster {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 12px;
    }}
    fieldset {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      margin: 0;
    }}
    legend {{ font-weight: 700; padding: 0 6px; }}
    .auswahl, .haken {{ display: block; margin: 8px 0; font-weight: 400; }}
    .problemfelder {{ margin: 16px 0; }}
    .hakenraster {{ columns: 2 260px; }}
    .details {{ margin-top: 14px; color: var(--muted); }}
    .details summary {{ cursor: pointer; }}
    .details dl {{ display: grid; grid-template-columns: minmax(140px, 220px) 1fr; gap: 6px 12px; }}
    .details dt {{ font-weight: 700; }}
    .versteckt {{ display: none !important; }}
    .zahlenraster {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
    }}
    .zahl {{ background: var(--soft); padding: 12px; border-radius: 6px; }}
    .zahl strong {{ display: block; font-size: 1.8rem; }}
    @media (max-width: 720px) {{
      body {{ font-size: 16px; }}
      .kartenkopf {{ display: block; }}
      .hakenraster {{ columns: 1; }}
    }}
    @media print {{
      .statusleiste, .aktionsleiste, .filterleiste, button, details {{ display: none !important; }}
      body {{ background: white; font-size: 12pt; }}
      main {{ max-width: none; padding: 0; }}
      .karte {{ break-inside: avoid; border: 1px solid #888; }}
      textarea {{ min-height: 40px; }}
    }}
  </style>
</head>
<body>
  <header class="seitenkopf">
    <main>
      <h1>Prüfung deutscher Telefonantworten</h1>
      <p>Sie sehen kurze Kundensätze und mögliche Antworten des Assistenten. Bitte prüfen Sie nur, ob die deutsche Formulierung natürlich, klar, freundlich und passend für ein Telefonat klingt.</p>
    </main>
  </header>
  <main>
    <section class="karte einleitung" aria-labelledby="start">
      <h2 id="start">Start</h2>
      <ul>
        <li>Sie brauchen kein technisches Wissen.</li>
        <li>Bitte beurteilen Sie nicht, ob das Produkt gut ist.</li>
        <li>Bitte beurteilen Sie nicht die rechtliche Richtigkeit.</li>
        <li>Bitte markieren Sie Antworten, die zu drängend, zu abrupt, unnatürlich oder intern klingen.</li>
        <li>Wenn möglich, schreiben Sie einen besseren Formulierungsvorschlag.</li>
      </ul>
    </section>

    <section class="karte" aria-labelledby="prueferdaten">
      <h2 id="prueferdaten">Angaben zur prüfenden Person</h2>
      <div class="formularraster">
        <label class="feld">Name oder Kürzel <input id="reviewerName" type="text"></label>
        <label class="feld">Muttersprache Deutsch?
          <select id="reviewerNativeGerman">
            <option value="">Bitte wählen</option>
            <option>Ja</option>
            <option>Nein</option>
          </select>
        </label>
        <label class="feld">Land/Region optional <input id="reviewerRegion" type="text"></label>
        <label class="feld">Datum <input id="reviewDate" type="date"></label>
      </div>
      <label class="textfeld">Allgemeine Hinweise
        <textarea id="reviewerGeneralNotes" rows="3"></textarea>
      </label>
    </section>

    <section class="karte" aria-labelledby="themen">
      <h2 id="themen">Themen</h2>
      <ul>{topic_summary}</ul>
    </section>

    <section class="statusleiste" aria-label="Fortschritt">
      <p id="progressText">0 von {len(items)} Antworten geprüft</p>
      <div class="balken"><span id="progressBar"></span></div>
    </section>

    <section class="karte" aria-labelledby="filter">
      <h2 id="filter">Filter</h2>
      <div class="filterleiste">
        <label class="feld">Thema
          <select id="topicFilter">
            <option value="">Alle Themen</option>
            {topic_options}
          </select>
        </label>
        <button class="secondary" data-filter="alle">Alle</button>
        <button class="secondary" data-filter="offen">Noch nicht geprüft</button>
        <button class="secondary" data-filter="ueberarbeitung">Überarbeitung nötig</button>
        <button class="secondary" data-filter="abgelehnt">Abgelehnt</button>
        <button class="secondary" data-filter="hinweise">Sicherheits-/Wirkungs-Hinweise</button>
      </div>
    </section>

    <section id="reviewItems" aria-label="Antworten zur Prüfung">
      {cards}
    </section>

    <section class="karte" aria-labelledby="zusammenfassung">
      <h2 id="zusammenfassung">Zusammenfassung</h2>
      <div class="zahlenraster">
        <div class="zahl"><strong id="summaryTotal">0</strong>Anzahl geprüfter Antworten</div>
        <div class="zahl"><strong id="summaryAccepted">0</strong>Anzahl akzeptiert</div>
        <div class="zahl"><strong id="summarySmall">0</strong>Anzahl mit kleinen Änderungen</div>
        <div class="zahl"><strong id="summaryLarge">0</strong>Anzahl mit großen Änderungen</div>
        <div class="zahl"><strong id="summaryRejected">0</strong>Anzahl abgelehnt</div>
        <div class="zahl"><strong id="summarySafety">0</strong>Anzahl mit Sicherheits-/Wirkungs-Hinweisen</div>
      </div>
    </section>

    <section class="karte" aria-labelledby="export">
      <h2 id="export">Export</h2>
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
    const PAKET_INFO = {embedded_packet};
    const SPEICHER_SCHLUESSEL = "prod048a_native_german_review";
    let aktiverFilter = "alle";

    function karten() {{
      return Array.from(document.querySelectorAll(".pruefkarte"));
    }}

    function radioWert(karte, feld) {{
      const input = karte.querySelector(`[data-rating-field="${{feld}}"]:checked`);
      return input ? input.value : "";
    }}

    function textWert(karte, feld) {{
      const input = karte.querySelector(`[data-text-field="${{feld}}"]`);
      return input ? input.value : "";
    }}

    function hakenWerte(karte) {{
      return Array.from(karte.querySelectorAll("[data-safety-flag]:checked")).map((input) => input.dataset.safetyFlag);
    }}

    function karteGeprueft(karte) {{
      return PAKET_INFO.rating_fields.every((feld) => radioWert(karte, feld.field_id));
    }}

    function datenSammeln() {{
      const items = karten().map((karte) => {{
        const ratings = {{}};
        PAKET_INFO.rating_fields.forEach((feld) => ratings[feld.field_id] = radioWert(karte, feld.field_id));
        return {{
          review_item_id: karte.dataset.reviewItemId,
          topic: karte.dataset.topic,
          ratings,
          safety_flags: hakenWerte(karte),
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
        summary: zusammenfassungBerechnen(items),
        items
      }};
    }}

    function zusammenfassungBerechnen(items) {{
      const geprueft = items.filter((item) => Object.values(item.ratings).every(Boolean));
      return {{
        anzahl_gepruefter_antworten: geprueft.length,
        anzahl_akzeptiert: items.filter((item) => item.ratings.telefonisch_akzeptabel === "ja").length,
        anzahl_mit_kleinen_aenderungen: items.filter((item) => item.ratings.ueberarbeitung_noetig === "kleine_aenderung").length,
        anzahl_mit_grossen_aenderungen: items.filter((item) => item.ratings.ueberarbeitung_noetig === "grosse_aenderung").length,
        anzahl_abgelehnt: items.filter((item) => item.ratings.telefonisch_akzeptabel === "nein").length,
        anzahl_mit_sicherheits_oder_wirkungs_hinweisen: items.filter((item) => item.safety_flags.length > 0).length
      }};
    }}

    function zusammenfassungAktualisieren() {{
      const daten = datenSammeln();
      const summary = daten.summary;
      document.getElementById("summaryTotal").textContent = summary.anzahl_gepruefter_antworten;
      document.getElementById("summaryAccepted").textContent = summary.anzahl_akzeptiert;
      document.getElementById("summarySmall").textContent = summary.anzahl_mit_kleinen_aenderungen;
      document.getElementById("summaryLarge").textContent = summary.anzahl_mit_grossen_aenderungen;
      document.getElementById("summaryRejected").textContent = summary.anzahl_abgelehnt;
      document.getElementById("summarySafety").textContent = summary.anzahl_mit_sicherheits_oder_wirkungs_hinweisen;
      document.getElementById("progressText").textContent = `${{summary.anzahl_gepruefter_antworten}} von {len(items)} Antworten geprüft`;
      document.getElementById("progressBar").style.width = `${{Math.round((summary.anzahl_gepruefter_antworten / {len(items)}) * 100)}}%`;
      filterAnwenden();
    }}

    function dateiHerunterladen(name, text, typ) {{
      const blob = new Blob([text], {{ type: typ }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    }}

    function bewertungAlsJsonHerunterladen() {{
      const daten = datenSammeln();
      dateiHerunterladen("deutsche-telefonantworten-bewertung.json", JSON.stringify(daten, null, 2), "application/json;charset=utf-8");
    }}

    function csvZelle(wert) {{
      return `"${{String(wert || "").replaceAll('"', '""')}}"`;
    }}

    function bewertungAlsCsvHerunterladen() {{
      const daten = datenSammeln();
      const kopf = ["review_item_id", "thema", "natuerlich", "klar_verstaendlich", "freundlich", "gesprochene_sprache", "zu_abrupt", "intern_buerokratisch_technisch", "telefonisch_akzeptabel", "ueberarbeitung_noetig", "hinweise", "vorschlag", "kommentar"];
      const zeilen = [kopf.map(csvZelle).join(",")];
      daten.items.forEach((item) => {{
        zeilen.push([
          item.review_item_id,
          item.topic,
          item.ratings.natuerlich,
          item.ratings.klar_verstaendlich,
          item.ratings.freundlich,
          item.ratings.gesprochene_sprache,
          item.ratings.zu_abrupt,
          item.ratings.intern_buerokratisch_technisch,
          item.ratings.telefonisch_akzeptabel,
          item.ratings.ueberarbeitung_noetig,
          item.safety_flags.join("; "),
          item.rewrite_suggestion,
          item.comment
        ].map(csvZelle).join(","));
      }});
      dateiHerunterladen("deutsche-telefonantworten-bewertung.csv", zeilen.join("\\n"), "text/csv;charset=utf-8");
    }}

    function zwischenstandSpeichern() {{
      localStorage.setItem(SPEICHER_SCHLUESSEL, JSON.stringify(datenSammeln()));
      alert("Zwischenstand gespeichert.");
    }}

    function zwischenstandLaden() {{
      const raw = localStorage.getItem(SPEICHER_SCHLUESSEL);
      if (!raw) {{
        alert("Kein gespeicherter Zwischenstand gefunden.");
        return;
      }}
      const daten = JSON.parse(raw);
      document.getElementById("reviewerName").value = daten.reviewer?.name_or_initials || "";
      document.getElementById("reviewerNativeGerman").value = daten.reviewer?.native_german || "";
      document.getElementById("reviewerRegion").value = daten.reviewer?.region_optional || "";
      document.getElementById("reviewDate").value = daten.reviewer?.date || "";
      document.getElementById("reviewerGeneralNotes").value = daten.reviewer?.general_notes || "";
      (daten.items || []).forEach((item) => {{
        const karte = document.querySelector(`[data-review-item-id="${{item.review_item_id}}"]`);
        if (!karte) return;
        Object.entries(item.ratings || {{}}).forEach(([feld, wert]) => {{
          const input = karte.querySelector(`[data-rating-field="${{feld}}"][value="${{wert}}"]`);
          if (input) input.checked = true;
        }});
        (item.safety_flags || []).forEach((flag) => {{
          const input = karte.querySelector(`[data-safety-flag="${{flag}}"]`);
          if (input) input.checked = true;
        }});
        const rewrite = karte.querySelector('[data-text-field="rewrite"]');
        const comment = karte.querySelector('[data-text-field="comment"]');
        if (rewrite) rewrite.value = item.rewrite_suggestion || "";
        if (comment) comment.value = item.comment || "";
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

    function filterAnwenden() {{
      const thema = document.getElementById("topicFilter").value;
      karten().forEach((karte) => {{
        const daten = datenSammeln().items.find((item) => item.review_item_id === karte.dataset.reviewItemId);
        const passtThema = !thema || karte.dataset.topic === thema;
        let passtFilter = true;
        if (aktiverFilter === "offen") passtFilter = !karteGeprueft(karte);
        if (aktiverFilter === "ueberarbeitung") passtFilter = ["kleine_aenderung", "grosse_aenderung"].includes(daten.ratings.ueberarbeitung_noetig);
        if (aktiverFilter === "abgelehnt") passtFilter = daten.ratings.telefonisch_akzeptabel === "nein";
        if (aktiverFilter === "hinweise") passtFilter = daten.safety_flags.length > 0;
        karte.classList.toggle("versteckt", !(passtThema && passtFilter));
      }});
    }}

    document.addEventListener("input", zusammenfassungAktualisieren);
    document.addEventListener("change", zusammenfassungAktualisieren);
    document.querySelectorAll("[data-filter]").forEach((button) => {{
      button.addEventListener("click", () => {{
        aktiverFilter = button.dataset.filter;
        filterAnwenden();
      }});
    }});
    document.getElementById("topicFilter").addEventListener("change", filterAnwenden);
    document.getElementById("reviewDate").value = new Date().toISOString().slice(0, 10);
    zusammenfassungAktualisieren();
  </script>
</body>
</html>
"""


def build_export_schema(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_id": "prod-048a.native_german_review_export.v1",
        "description": "Browser-exported review result schema for the German wording reviewer packet.",
        "required_top_level_fields": ["reviewer", "summary", "items"],
        "required_reviewer_fields": ["name_or_initials", "native_german", "region_optional", "date", "general_notes"],
        "required_item_fields": [
            "review_item_id",
            "topic",
            "ratings",
            "safety_flags",
            "rewrite_suggestion",
            "comment",
        ],
        "required_rating_field_ids": [field["field_id"] for field in packet["rating_fields"]],
        "required_safety_flag_ids": [field["flag_id"] for field in packet["safety_flags"]],
        "export_formats": ["json", "csv"],
        "no_server_required": True,
        "native_german_approval_claimed": False,
        "legal_compliance_claimed": False,
    }


def build_csv_table(packet: dict[str, Any]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["nummer", "thema", "kundensatz", "antwort_des_assistenten", "fallkennung"])
    for item in packet["review_items"]:
        writer.writerow(
            [
                item["review_item_number"],
                item["topic_title_de"],
                item["customer_utterance"],
                item["agent_response"],
                item["source_case_id"],
            ]
        )
    return buffer.getvalue()


def build_readme_de(packet: dict[str, Any]) -> str:
    return f"""# Prüfung deutscher Telefonantworten

Diese Mappe ist für eine muttersprachliche Prüfung deutscher Telefonantworten.

## Was soll geprüft werden?

Bitte prüfen Sie nur die deutsche Formulierung der Antworten:

- Klingt die Antwort natürlich?
- Ist die Antwort klar verständlich?
- Ist die Antwort freundlich?
- Passt die Antwort zu einem kurzen Telefonat?
- Klingt die Antwort zu abrupt, zu technisch, zu bürokratisch oder zu drängend?

Bitte beurteilen Sie nicht, ob das Produkt gut ist. Dies ist keine Rechtsprüfung.

## Datei öffnen

Öffnen Sie diese Datei in einem Browser:

`native_german_review.html`

Es wird kein Server und kein Internetzugang benötigt.

## Zwischenspeichern

Mit **Zwischenstand im Browser speichern** können Sie Ihre Eingaben lokal im Browser speichern.

Mit **Zwischenstand laden** können Sie später weiterarbeiten.

## Export

Wenn Sie fertig sind, laden Sie bitte eine der Dateien herunter:

- **Bewertung als JSON herunterladen**
- **Bewertung als CSV herunterladen**

Senden Sie die heruntergeladene Datei an Tarik zurück.

## Umfang

Anzahl der Antworten: {len(packet["review_items"])}

Wichtig: Diese Prüfung bedeutet noch keine endgültige Freigabe. Es geht nur um eine sprachliche Einschätzung.
"""


def build_report(packet: dict[str, Any], summary: dict[str, Any]) -> str:
    return f"""# PROD-048A Native German Review HTML Packet

PROD-048A creates a German-only, non-technical, local browser review packet for native German wording review.

## Source Inputs

- `research/experiments/generated/PROD-046-core-sales-policy-human-review/german_response_quality_findings.json`
- `research/experiments/generated/PROD-046-core-sales-policy-human-review/call_control_findings.json`
- `research/experiments/generated/PROD-046D-german-source-informed-wording-quality-guard/german_source_informed_results.json`
- `runtime/campaigns/examples/campaign-prod-047-valid-de-source-informed.json`
- `research/experiments/generated/PROD-047-campaign-profile-contract-validator/result.json`

## Outputs

- `native_german_review.html`: self-contained German reviewer interface.
- `native_german_review_packet.json`: source packet used by the HTML.
- `native_german_review_export_schema.json`: expected browser export shape.
- `native_german_review_readme_de.md`: German reviewer instructions.
- `native_german_review_table.csv`: simple review table.

## Metrics

- Review items: {summary["review_item_count"]}
- Topic groups: {summary["topic_count"]}
- HTML self-contained: `{summary["html_self_contained"]}`
- JSON export enabled: `{summary["reviewer_export_json_enabled"]}`
- CSV export enabled: `{summary["reviewer_export_csv_enabled"]}`
- Local storage enabled: `{summary["local_storage_enabled"]}`
- Print-friendly mode enabled: `{summary["print_friendly_mode_enabled"]}`

## Boundaries

- No native German approval is claimed.
- No legal compliance is claimed.
- Runtime behavior changed: `false`
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


def build_result(packet: dict[str, Any]) -> dict[str, Any]:
    source_046 = read_json(PROD_046_RESULT_PATH)
    source_047 = read_json(PROD_047_RESULT_PATH)
    summary = {
        "source_checkpoint_ids": SOURCE_CHECKPOINTS,
        "prod_046_result_validation_passed": source_046.get("validation", {}).get("passed") is True,
        "prod_047_result_validation_passed": source_047.get("validation", {}).get("passed") is True,
        "review_item_count": len(packet["review_items"]),
        "topic_count": len(packet["topic_groups"]),
        "html_self_contained": True,
        "all_visible_main_labels_german": True,
        "reviewer_export_json_enabled": True,
        "reviewer_export_csv_enabled": True,
        "local_storage_enabled": True,
        "print_friendly_mode_enabled": True,
        **BOUNDARY_FALSE_SUMMARY,
    }
    passed = (
        summary["prod_046_result_validation_passed"]
        and summary["prod_047_result_validation_passed"]
        and summary["review_item_count"] > 0
        and summary["topic_count"] >= 10
        and all(value is False for value in BOUNDARY_FALSE_SUMMARY.values())
    )
    return {
        "checkpoint_id": CHECKPOINT_ID,
        "checkpoint_name": CHECKPOINT_NAME,
        "source_checkpoint_ids": SOURCE_CHECKPOINTS,
        "summary": summary,
        "outputs": {
            "report": rel(OUT_DIR / "report.md"),
            "native_german_review_packet": rel(OUT_DIR / "native_german_review_packet.json"),
            "native_german_review_html": rel(OUT_DIR / "native_german_review.html"),
            "native_german_review_export_schema": rel(OUT_DIR / "native_german_review_export_schema.json"),
            "native_german_review_readme_de": rel(OUT_DIR / "native_german_review_readme_de.md"),
            "native_german_review_table_csv": rel(OUT_DIR / "native_german_review_table.csv"),
        },
        "validation": {"passed": passed},
        "next_checkpoint_recommended": NEXT_CHECKPOINT_ID,
    }


def main() -> None:
    for path in (
        GERMAN_FINDINGS_PATH,
        CALL_CONTROL_FINDINGS_PATH,
        GERMAN_RESULT_PATH,
        PROD_046_RESULT_PATH,
        PROD_047_RESULT_PATH,
        CAMPAIGN_PATH,
    ):
        if not path.exists():
            raise SystemExit(f"Missing required input: {rel(path)}")

    packet = build_packet()
    result = build_result(packet)
    summary = result["summary"]

    write_json(OUT_DIR / "native_german_review_packet.json", packet)
    write_json(OUT_DIR / "native_german_review_export_schema.json", build_export_schema(packet))
    write_json(OUT_DIR / "result.json", result)
    write_text(OUT_DIR / "native_german_review.html", render_html(packet))
    write_text(OUT_DIR / "native_german_review_readme_de.md", build_readme_de(packet))
    write_text(OUT_DIR / "native_german_review_table.csv", build_csv_table(packet))
    write_text(OUT_DIR / "report.md", build_report(packet, summary))

    print(json.dumps({"checkpoint_id": CHECKPOINT_ID, "validation": result["validation"], "summary": summary}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
