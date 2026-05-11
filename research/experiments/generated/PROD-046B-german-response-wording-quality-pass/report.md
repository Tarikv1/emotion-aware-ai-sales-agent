# PROD-046B German Response Wording Quality Pass

PROD-046B keeps PROD-046A routing intact and improves German customer-facing response wording so the output is less internal-policy-like.

This is not final German human review. It is a deterministic wording pass over synthetic de-DE regression cases and campaign fixture wording.

## Results

- German wording rewrites: 16
- Banned internal terms before: 9
- Banned internal terms after: 0
- German positive regression passed: `True`
- German false-positive regression passed: `True`
- English PROD-045 regression still passed: `True`
- German sale-ready term count after: 0
- German internal route term count after: 0

## Before / After Examples

### price-first-direct

- Before: Der freigegebene Preisrahmen liegt beim Starter-Paket bei 29 Euro pro Nutzer und Monat; die genauen Bedingungen kommen schriftlich. Keine Zahlung und keine Verpflichtung in diesem Anruf.
- After: Nach den freigegebenen Informationen liegt der Preisrahmen bei beim Starter-Paket 29 Euro pro Nutzer und Monat; die genauen Bedingungen kommen schriftlich. In diesem Gespräch geht es nicht um Zahlung oder Vertragsunterzeichnung.

### identity-repair

- Before: Hier ist Maya von RouteSignal. Der Grund für den Anruf ist ein kurzer Abgleich zur Zuständigkeit für Rückrufe und Nachverfolgung. Wenn das nicht relevant ist, höre ich hier auf.
- After: Hier ist Maya von RouteSignal. Ich rufe kurz an, um ein kurzer Abgleich zur Zuständigkeit für Rückrufe und Nachverfolgung. Wenn das für Sie nicht relevant ist, beende ich den Anruf.

### written-info-request

- Before: Ich kann die freigegebene schriftliche Zusammenfassung senden und es dabei belassen.
- After: Ich kann Ihnen eine kurze freigegebene Zusammenfassung zusenden und es dabei belassen.

### email-only-boundary

- Before: Verstanden. Nur per E-Mail. Ich kann die freigegebene E-Mail-Zusammenfassung senden und dränge nicht auf einen Anruf.
- After: Verstanden. Ich halte es bei E-Mail, sende Ihnen eine kurze freigegebene E-Mail-Zusammenfassung und dränge nicht auf ein Telefonat.

### scam-safety-boundary

- Before: In diesem Anruf werden keine Zahlungs-, Karten- oder sensiblen Daten aufgenommen. Ich kann die öffentliche Verifizierungsseite und die schriftliche Zusammenfassung zur Verifizierung senden.
- After: Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen den offiziellen Verifizierungsweg und die schriftlichen Informationen zusenden.

### payment-safety-boundary

- Before: Hier werden keine Karten- oder Zahlungsdaten benötigt. Ich halte den nächsten Schritt nur bei sicheren schriftlichen Informationen: die freigegebene einseitige Zusammenfassung.
- After: Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen eine kurze freigegebene Zusammenfassung zusenden.

### support-route

- Before: Das ist ein Support-Thema. Ich stoppe den Verkaufspfad und leite das an die Support-Warteschlange weiter.
- After: Das ist ein Support-Thema. Ich stoppe den Vertriebsteil hier und leite Sie an den zuständigen Support weiter.

### cancellation-route

- Before: Ich stoppe den Verkaufspfad und leite das an die Kündigungs-Warteschlange weiter.
- After: Dann stoppe ich den Vertriebsteil hier und leite Sie an die zuständige Stelle für Kündigungen weiter.

## Remaining German Wording Risks

- German wording is improved deterministically but still needs human/product review by a German speaker.
- The response surface remains single-turn and campaign-field-driven; this checkpoint does not validate full live conversation naturalness.
- The borrowed German term Support remains allowed because the preferred wording explicitly uses zuständiger Support.

## Boundaries

- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`

Next recommended checkpoint: `PROD-046-core-sales-policy-human-review`.
