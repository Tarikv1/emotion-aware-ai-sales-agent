# CUSTOMER-FACING-OFFER-LANGUAGE-001

Status: PASS
Scenarios: 143
Campaigns: 9 total, 8 generic fixtures
Failures: 0

## Failure Types

## Opening Samples
- synthetic-telecom-plan-review: Hi, this is Maya calling from Cedar Telecom. I am doing a quick telecom plan fit check to see whether plan fit is worth a short specialist review. Do you have a minute?
- synthetic-insurance-review: Hi, this is Maya calling from Harbor Insurance. I am doing a quick policy fit check to see whether premium pressure is worth a licensed review. Do you have a minute?
- synthetic-automotive-service-review: Hi, this is Maya calling from Atlas Auto Service. I am doing a quick service fit check to see whether repair timing is worth a short specialist review. Do you have a minute?
- synthetic-membership-plan-review: Hi, this is Maya calling from Cedar Membership Services. I am doing a quick membership plan fit check to see whether plan fit is worth a short specialist review. Do you have a minute?
- synthetic-b2b-saas-operations: Hi, this is Maya calling from Vector Workflow Labs. I am doing a quick operations fit check to see whether manual work is worth a short specialist review. Do you have a minute?
- synthetic-home-services-estimate: Hi, this is Maya calling from Hearthside Home Services. I am doing a quick home service fit check to see whether service need is worth a short specialist review. Do you have a minute?
- synthetic-healthcare-admin-review: Hi, this is Maya calling from Harbor Admin Services. I am doing a quick admin fit check to see whether administrative issue is worth a short specialist review. Do you have a minute?
- synthetic-retail-support-review: Hi, this is Maya calling from Parcel Retail Support. I am doing a quick retail support fit check to see whether order issue is worth a short specialist review. Do you have a minute?

## Response Samples
- product_offer_questions / routesignal / what are you selling: Plainly, RouteSignal is a CRM workflow tool for inbound demo follow-up. The quick check before any review is whether that problem is active for you.
- product_offer_questions / routesignal / what is your product: Sure. RouteSignal is a CRM workflow tool for inbound demo follow-up. This call is only to check whether that problem is active before any review.
- product_offer_questions / routesignal / what do you do: RouteSignal CRM routes leads, captures follow-up tasks, and shows handoff status so inbound requests do not sit in a spreadsheet. Where does follow-up break first today: assignment, reminders, or missed replies?
- product_offer_questions / routesignal / what problem do you solve: Fair question. Mainly, RouteSignal is a CRM workflow tool for inbound demo follow-up. The high-level value is fewer missed replies, clearer ownership, and less manual follow-up drift.
- product_offer_questions / synthetic-telecom-plan-review / what are you selling: Fair question. This is telecom plan fit check. I am checking whether plan fit is still a problem; if so, the telecom account specialist reviews plan fit, coverage availability, and switching constraints against account-specific details.
- product_offer_questions / synthetic-telecom-plan-review / what is your product: Sure. This is telecom plan fit check. I can explain the high-level scope; this call is only to check whether plan fit is still a problem; if it is relevant, the telecom account specialist reviews the actual details.
- product_offer_questions / synthetic-telecom-plan-review / what do you do: This is telecom plan fit check. I can explain that high-level scope; A telecom account specialist reviews plan fit and the actual details.
- product_offer_questions / synthetic-telecom-plan-review / what problem do you solve: Fair question. Mainly, this helps decide whether plan fit is still a problem. This is telecom plan fit check. Avoid wasting time on a bad-fit plan or switching path before account-specific details are checked. If it is relevant, the telecom account specialist reviews the actual details.
- product_offer_questions / synthetic-insurance-review / what are you selling: Fair question. This is policy fit check. I am checking whether premium pressure is still a problem; if so, the licensed insurance specialist reviews premium pressure, coverage fit, and renewal timing against actual policy details.
- product_offer_questions / synthetic-insurance-review / what is your product: Sure. This is policy fit check. I can explain the high-level scope; this call is only to check whether premium pressure is still a problem; if it is relevant, the licensed insurance specialist reviews the actual details.
- product_offer_questions / synthetic-insurance-review / what do you do: This is policy fit check. I can explain that high-level scope; A licensed insurance specialist reviews premium pressure and the actual details.
- product_offer_questions / synthetic-insurance-review / what problem do you solve: Fair question. Mainly, this helps decide whether premium pressure is still a problem. This is policy fit check. Route policy-specific questions to a licensed reviewer before any coverage, premium, or eligibility claim is made. If it is relevant, the licensed insurance specialist reviews the actual details.
- product_offer_questions / synthetic-automotive-service-review / what are you selling: Fair question. This is service fit check. I am checking whether repair timing is still a problem; if so, the service advisor reviews vehicle issue, repair timing, and warranty or estimate context.
- product_offer_questions / synthetic-automotive-service-review / what is your product: Sure. This is service fit check. I can explain the high-level scope; this call is only to check whether repair timing is still a problem; if it is relevant, the service advisor reviews the actual details.
- product_offer_questions / synthetic-automotive-service-review / what do you do: This is service fit check. I can explain that high-level scope; A service advisor reviews repair timing and the actual details.
- product_offer_questions / synthetic-automotive-service-review / what problem do you solve: Fair question. Mainly, this helps decide whether repair timing is still a problem. This is service fit check. Route timing, warranty, or estimate questions to a service advisor before any remote diagnosis or cost claim is made. If it is relevant, the service advisor reviews the actual details.
- product_offer_questions / synthetic-membership-plan-review / what are you selling: Fair question. This is membership plan fit check. I am checking whether plan fit is still a problem; if so, the account support specialist reviews plan fit, renewal or cancellation, and usage or value against account-specific details.
- product_offer_questions / synthetic-membership-plan-review / what is your product: Sure. This is membership plan fit check. I can explain the high-level scope; this call is only to check whether plan fit is still a problem; if it is relevant, the account support specialist reviews the actual details.
- product_offer_questions / synthetic-membership-plan-review / what do you do: This is membership plan fit check. I can explain that high-level scope; An account support specialist reviews plan fit and the actual details.
- product_offer_questions / synthetic-membership-plan-review / what problem do you solve: Fair question. Mainly, this helps decide whether plan fit is still a problem. This is membership plan fit check. Route account-specific renewal, cancellation, or usage questions to support before any account action or refund claim is made. If it is relevant, the account support specialist reviews the actual details.
- product_offer_questions / synthetic-b2b-saas-operations / what are you selling: Fair question. This is operations fit check. I am checking whether manual work is still a problem; if so, the implementation specialist reviews manual work, integration risk, and visibility gaps against the actual operating workflow.
- product_offer_questions / synthetic-b2b-saas-operations / what is your product: Sure. This is operations fit check. I can explain the high-level scope; this call is only to check whether manual work is still a problem; if it is relevant, the implementation specialist reviews the actual details.
- product_offer_questions / synthetic-b2b-saas-operations / what do you do: This is operations fit check. I can explain that high-level scope; An implementation specialist reviews manual work and the actual details.
- product_offer_questions / synthetic-b2b-saas-operations / what problem do you solve: Fair question. Mainly, this helps decide whether manual work is still a problem. This is operations fit check. Route workflow-fit questions to an implementation specialist before any integration, security, or business-outcome claim is made. If it is relevant, the implementation specialist reviews the actual details.

## Side Effects
- Provider calls, local LLM calls, email, calendar, CRM writes, PROD-102, live TTS, and audio-file creation must remain false.
