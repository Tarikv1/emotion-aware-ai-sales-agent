# COMMERCIAL-REVIEW-WARNING-RESIDUAL-AUDIT-001

## 1. Summary
Audited commercial packet warnings and cross-campaign ASR residuals before runtime patching.

## 2. Commercial Packet Warning Counts
- no_acknowledgement: 35
- over_deferential_stop_offer: 40

## 3. Classification Counts By Warning Type
- no_acknowledgement / false_positive_warning: 22
- over_deferential_stop_offer / intentional_no_fit_or_stop: 15
- over_deferential_stop_offer / needs_human_sales_review: 10

## 4. True Sales Defects
- None from the audited commercial warning instances.

## 5. False Positives / Intentional Warnings
- routesignal_live_demo | direct_question | what does your product do | no_acknowledgement -> false_positive_warning
- routesignal_live_demo | direct_question | why should I care | no_acknowledgement -> false_positive_warning
- routesignal_live_demo | trust_challenge | who are you | no_acknowledgement -> false_positive_warning
- routesignal_live_demo | asr_garble | play a double be good | no_acknowledgement -> false_positive_warning
- routesignal_live_demo | asr_garble | yadav would be good | no_acknowledgement -> false_positive_warning
- routesignal_live_demo | no_fit_stop | not interested | over_deferential_stop_offer -> intentional_no_fit_or_stop
- routesignal_live_demo | no_fit_stop | I don't want to continue | over_deferential_stop_offer -> intentional_no_fit_or_stop
- routesignal_live_demo | no_fit_stop | stop calling | over_deferential_stop_offer -> intentional_no_fit_or_stop
- synthetic-insurance-review | asr_garble | play a double be good | no_acknowledgement -> false_positive_warning
- synthetic-insurance-review | asr_garble | yadav would be good | no_acknowledgement -> false_positive_warning

## 6. ASR Residual Classification

## 7. Recommended Patch Scope
- No runtime patch recommended; update warning classification only.

## 8. Whether Runtime Behavior Changed
- No. This audit is read-only.
