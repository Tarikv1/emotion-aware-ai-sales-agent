# PROD-046C German Campaign Field Interpolation Guard

PROD-046C fixes narrow German campaign-field interpolation bugs found after PROD-046B.

This is not a runtime-policy expansion checkpoint and not a German realism pass. It keeps the PROD-045, PROD-046A, and PROD-046B regression surfaces intact while adding deterministic guards for malformed German customer-facing strings.

## Results

- German positive cases: 66
- German false-positive cases: 6
- German interpolation guard cases: 33
- Malformed German response count: 0
- Duplicate `zuständige Fachperson` same-sentence count: 0
- Positive unknown-runtime-signal count: 0
- Positive generic clarification count: 0
- False-positive unknown-runtime-signal count: 2
- False-positive generic clarification count: 0
- English PROD-045 still passed: `True`
- German PROD-046A still passed: `True`
- German PROD-046B still passed: `True`

## Before / After

### price-first-direct

- PROD-046B: Nach den freigegebenen Informationen liegt der Preisrahmen bei beim Starter-Paket 29 Euro pro Nutzer und Monat; die genauen Bedingungen kommen schriftlich. In diesem Gespräch geht es nicht um Zahlung oder Vertragsunterzeichnung.
- PROD-046C: Nach den vorliegenden Informationen liegt das Starter-Paket bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen sende ich Ihnen schriftlich. In diesem Gespräch geht es nicht um Zahlung oder Vertragsabschluss.

### identity-repair

- PROD-046B: Hier ist Maya von RouteSignal. Ich rufe kurz an, um ein kurzer Abgleich zur Zuständigkeit für Rückrufe und Nachverfolgung. Wenn das für Sie nicht relevant ist, beende ich den Anruf.
- PROD-046C: Hier ist Maya von RouteSignal. Ich rufe an, weil wir kurz klären möchten, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist. Wenn das für Sie nicht relevant ist, beende ich den Anruf.

### security-review-route

- PROD-046B: Für eine Sicherheitsprüfung braucht es freigegebene Unterlagen oder eine zuständige Fachperson. Ich kann das an eine zuständige Fachperson weiterleiten und mache hier keine pauschalen Compliance-Zusagen.
- PROD-046C: Das sollte eine zuständige Fachperson prüfen. Ich rate hier nicht und mache keine allgemeinen Zusagen.

### sale-ready-commitment

- PROD-046B: Gut, ich halte fest, dass Sie den nächsten freigegebenen Schritt möchten. Es findet hier keine Zahlung und keine Vertragsunterzeichnung statt.
- PROD-046C: Gut, ich halte fest, dass Sie den nächsten Schritt möchten. Es findet hier keine Zahlung und keine Vertragsunterzeichnung statt.

## Remaining Wording Risks

- German response quality still needs human/product review by a German speaker.
- The guard catches known malformed interpolation classes, not every possible grammar issue.
- Campaign fields remain a product-quality bottleneck unless future profiles clearly separate full customer-facing sentences from fragments.

## Boundaries

- Retrieval enabled: `false`
- Provider calls made: `false`
- LLM used: `false`
- Private data read: `false`
- Voice playback unblocked: `false`
- Public demo polish unblocked: `false`
- Payment collection allowed: `false`
- Contract signing allowed: `false`
- Production runtime promotion allowed: `false`

Next recommended checkpoint: `PROD-046-core-sales-policy-human-review`.
