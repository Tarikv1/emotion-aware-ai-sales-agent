# COMMERCIAL-REVIEW-WARNING-RESIDUAL-AUDIT-001

## 1. Summary
Audited commercial packet warnings and cross-campaign ASR residuals before runtime patching.

## 2. Commercial Packet Warning Counts
- no_acknowledgement: 23
- over_deferential_stop_offer: 30

## 3. Classification Counts By Warning Type
- over_deferential_stop_offer / intentional_no_fit_or_stop: 15
- no_acknowledgement / false_positive_warning: 14
- over_deferential_stop_offer / needs_human_sales_review: 5

## 4. True Sales Defects
- None from the audited commercial warning instances.

## 5. False Positives / Intentional Warnings
- routesignal_live_demo | trust_challenge | who are you | no_acknowledgement -> false_positive_warning
- routesignal_live_demo | asr_garble | play a double be good | no_acknowledgement -> false_positive_warning
- routesignal_live_demo | asr_garble | yadav would be good | no_acknowledgement -> false_positive_warning
- routesignal_live_demo | no_fit_stop | not interested | over_deferential_stop_offer -> intentional_no_fit_or_stop
- routesignal_live_demo | no_fit_stop | I don't want to continue | over_deferential_stop_offer -> intentional_no_fit_or_stop
- routesignal_live_demo | no_fit_stop | stop calling | over_deferential_stop_offer -> intentional_no_fit_or_stop
- synthetic-insurance-review | asr_garble | play a double be good | no_acknowledgement -> false_positive_warning
- synthetic-insurance-review | asr_garble | yadav would be good | no_acknowledgement -> false_positive_warning
- synthetic-insurance-review | no_fit_stop | not interested | over_deferential_stop_offer -> intentional_no_fit_or_stop
- synthetic-insurance-review | no_fit_stop | I don't want to continue | over_deferential_stop_offer -> intentional_no_fit_or_stop

## 6. ASR Residual Classification

## 7. Recommended Patch Scope
- No runtime patch recommended; update warning classification only.

## 8. Whether Runtime Behavior Changed
- No. This audit is read-only.
