# PROD-046D German Source-Informed Wording Quality Guard

PROD-046D narrows German customer-facing runtime wording after PROD-046C. It uses GER-001 accepted sources as source-informed wording guidance only, not as legal-compliance evidence.

The checkpoint rejects cold-call scripts and aggressive sales sources. It keeps retrieval, providers, LLM calls, private data, voice playback, public demo polish, payment collection, contract signing, and production promotion blocked.

## Results

- German source-informed cases: 99
- German source-informed pass/fail: 99 / 0
- Source-informed wording rewrites: 15
- Internal wording hits before: 14
- Internal wording hits after: 0
- Customer-facing `freigegeben` hits after: 0
- Source traceability source count: 11
- English PROD-045 still passed: `True`
- German PROD-046A still passed: `True`
- German PROD-046B still passed: `True`
- German PROD-046C still passed: `True`

## Before / After

### price-first-direct

- PROD-046C: Nach den freigegebenen Informationen liegt der Preisrahmen beim Starter-Paket bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen erhalten Sie schriftlich. In diesem Gespräch geht es nicht um Zahlung oder Vertragsunterzeichnung.
- PROD-046D: Nach den vorliegenden Informationen liegt das Starter-Paket bei 29 Euro pro Nutzer und Monat. Die genauen Bedingungen sende ich Ihnen schriftlich. In diesem Gespräch geht es nicht um Zahlung oder Vertragsabschluss.

### identity-repair

- PROD-046C: Hier ist Maya von RouteSignal. Ich rufe kurz an, um zu klären, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist. Wenn das für Sie nicht relevant ist, beende ich den Anruf.
- PROD-046D: Hier ist Maya von RouteSignal. Ich rufe an, weil wir kurz klären möchten, wer bei Ihnen für Rückrufe und Nachverfolgung zuständig ist. Wenn das für Sie nicht relevant ist, beende ich den Anruf.

### written-info-request

- PROD-046C: Ich kann Ihnen eine kurze freigegebene Zusammenfassung zusenden und es dabei belassen.
- PROD-046D: Ich sende Ihnen gern eine kurze Zusammenfassung per E-Mail und belasse es dabei.

### email-only-boundary

- PROD-046C: Verstanden. Ich halte es bei E-Mail, sende Ihnen eine kurze freigegebene E-Mail-Zusammenfassung und dränge nicht auf ein Telefonat.
- PROD-046D: Verstanden. Ich sende Ihnen die Informationen per E-Mail und dränge nicht auf ein Telefonat.

### scam-safety-boundary

- PROD-046C: Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen den offiziellen Verifizierungsweg und die schriftlichen Informationen zusenden.
- PROD-046D: Ich frage in diesem Gespräch nicht nach Zahlungsdaten, Kartendaten oder Passwörtern. Sie können die Informationen über die offizielle Seite prüfen. Ich sende Ihnen dazu schriftliche Informationen.

### payment-safety-boundary

- PROD-046C: Ich frage in diesem Gespräch nicht nach Zahlungsdaten oder Kartendaten. Ich kann Ihnen stattdessen eine kurze freigegebene Zusammenfassung zusenden.
- PROD-046D: Ich frage in diesem Gespräch nicht nach Zahlungsdaten, Kartendaten oder Passwörtern. Sie können die Informationen über die offizielle Seite prüfen. Ich sende Ihnen dazu schriftliche Informationen.

### support-route

- PROD-046C: Das ist ein Support-Thema. Ich stoppe den Vertriebsteil hier und leite Sie an den zuständigen Support weiter.
- PROD-046D: Dann ist das ein Support-Thema. Ich beende den Verkaufsteil hier und leite Sie an den zuständigen Support weiter.

### cancellation-route

- PROD-046C: Dann stoppe ich den Vertriebsteil hier und leite Sie an die zuständige Stelle für Kündigungen weiter.
- PROD-046D: Dann geht es um eine Kündigung. Ich beende den Verkaufsteil hier und leite Sie an die zuständige Stelle für Kündigungen weiter.

### technical-specialist-route

- PROD-046C: Was ich sicher sagen kann: das System kann Zuständigkeiten für Rückrufe und Nachverfolgung abbilden; Integrationsdetails müssen geprüft werden. Für weitere Details kann ich das an eine zuständige Fachperson weiterleiten.
- PROD-046D: Nach den vorliegenden Informationen kann das System Zuständigkeiten für Rückrufe und Nachverfolgung abbilden. Integrationsdetails sollte eine zuständige Fachperson prüfen.

### security-review-route

- PROD-046C: Für eine Sicherheitsprüfung braucht es freigegebene Unterlagen oder eine zuständige Fachperson. Ich mache hier keine pauschalen Compliance-Zusagen.
- PROD-046D: Das sollte eine zuständige Fachperson prüfen. Ich rate hier nicht und mache keine allgemeinen Zusagen.

### stakeholder-review

- PROD-046C: Ich kann Ihnen eine kurze freigegebene Zusammenfassung zur Prüfung schicken. Heute müssen Sie nichts entscheiden und gehen keine Verpflichtung ein.
- PROD-046D: Ich sende Ihnen eine kurze Zusammenfassung zur Prüfung. Heute müssen Sie nichts entscheiden.

### partner-review

- PROD-046C: Ich kann Ihnen eine kurze freigegebene Zusammenfassung zur Prüfung schicken. Heute müssen Sie nichts entscheiden und gehen keine Verpflichtung ein.
- PROD-046D: Ich sende Ihnen eine kurze Zusammenfassung zur Prüfung. Heute müssen Sie nichts entscheiden.

### do-not-call

- PROD-046C: Verstanden. Ich markiere den Kontakt so, dass Sie nicht mehr angerufen werden. Auf Wiederhören.
- PROD-046D: Verstanden. Sie sollen hierzu nicht mehr angerufen werden. Ich beende den Anruf hier. Auf Wiederhören.

### callback-request

- PROD-046C: Ich kann einen Rückrufwunsch dokumentieren und halte ihn optional. Keine feste Verpflichtung in diesem Anruf.
- PROD-046D: Ich kann einen Rückruf vormerken. Das bleibt optional; heute entsteht keine Verpflichtung.

### product-detail-lookup

- PROD-046C: Einen Moment, ich prüfe die freigegebenen Produktinformationen.
- PROD-046D: Einen Moment, ich prüfe die Produktinformationen.

## Source Guidance

- Accepted sources are official regulator, consumer-protection, public-service, and plain-language sources.
- Rejected sources are sales guru blogs, cold-call scripts, aggressive closing scripts, affiliate SEO pages, and copied competitor wording.
- The sources support wording style and safety posture only. PROD-046D does not claim legal compliance.

## Campaign Field Shape Rules

- Prefer full customer-facing sentence fields for identity, pricing, and verification responses.
- Use noun phrase fields only when the template is explicitly written for a noun phrase.
- Keep internal labels such as approved, route, boundary, campaign, or source status out of customer-facing German.
- Use active verbs and short sentences before human review.

## Remaining Wording Risks

- German wording still needs human/product review by a German speaker.
- This is a single-turn wording guard, not full conversation realism.
- This is not a legal-compliance checkpoint.

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
