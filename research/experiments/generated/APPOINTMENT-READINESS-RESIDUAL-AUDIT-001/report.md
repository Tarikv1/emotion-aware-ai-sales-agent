# APPOINTMENT-READINESS-RESIDUAL-AUDIT-001

## 1. Summary
- Classification basis: `legacy_residual_heuristic`
- Recommended patch scope: Fix review-packet warning logic for callback_time_provided turns; no runtime behavior patch is justified.
- Runtime behavior changed: `false`

## 2. Total appointment_not_asked_when_ready warnings
- Current packet warning occurrences: `0`
- Current flagged turns: `0`
- Current flagged conversations: `0`
- Legacy residual reported occurrences: `30`
- Legacy residual turns: `15`

## 3. Count by classification
- `review_packet_warning_bug`: `15`

## 4. Top true missed-next-step examples
- None

## 5. Top weak-close examples
- None

## 6. False-positive examples
- `commercial-sales-conversation-review-001-01-01-routesignal_live_demo-smooth_qualified_appointment` turn `5` `callback_time_provided`: Got it. I'll note that time for the verified implementation reviewer to follow up.
- `commercial-sales-conversation-review-001-01-03-routesignal_live_demo-tentative_pain` turn `6` `callback_time_provided`: Got it. I'll note that time for the verified implementation reviewer to follow up.
- `commercial-sales-conversation-review-001-01-04-routesignal_live_demo-direct_question` turn `6` `callback_time_provided`: Got it. I'll note that time for the verified implementation reviewer to follow up.
- `commercial-sales-conversation-review-001-02-01-synthetic-insurance-review-smooth_qualified_appointment` turn `5` `callback_time_provided`: Got it. I'll note that time for the licensed insurance specialist to follow up.
- `commercial-sales-conversation-review-001-02-03-synthetic-insurance-review-tentative_pain` turn `6` `callback_time_provided`: Got it. I'll note that time for the licensed insurance specialist to follow up.

## 7. Warning-logic defects
- Review-packet warning bug count: `15`
- The old warning treated callback-time confirmation as a missed appointment ask.

## 8. Runtime defects
- True missed-next-step count: `0`
- State preservation bug count: `0`

## 9. Recommended patch scope
- Fix review-packet warning logic for callback_time_provided turns; no runtime behavior patch is justified.

## 10. Whether runtime behavior changed
- `false`
