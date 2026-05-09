# PROD-028 Synthetic Campaign Knowledge Grounding

PROD-028 creates a fictional but reality-patterned B2B CRM campaign so the local sales agent can answer concrete buyer questions instead of only asking discovery questions.

## Result

- Checkpoint id: `PROD-028-synthetic-campaign-knowledge-grounding`
- Reality-based source patterning: `true`
- Fictional product: `true`
- Same questions compared: `true`
- Question count: `12`
- Direct answer rate: `1.0`
- Factual correctness rate: `1.0`
- Price correctness rate: `1.0`
- Question overuse rate: `0.0`
- Baseline question overuse rate: `1.0`
- Safe unknown handling rate: `1.0`
- Unsupported claim count: `0`
- Payment collection count: `0`
- Provider calls made: `false`
- Runtime behavior changed: `false`
- Next checkpoint: `PROD-029-grounded-full-scenario-rerun`

## Reality Pattern Sources

The source pages were used as inspiration only for SaaS/CRM pricing and packaging patterns. No real company wording, plan names, brand identity, or claims were copied into the fictional campaign.
- `prod-028-source-hubspot-sales-product`: https://www.hubspot.com/products/sales - reuse label `inspiration only`
- `prod-028-source-pipedrive-pricing`: https://www.pipedrive.com/en/pricing - reuse label `inspiration only`
- `prod-028-source-salesforce-sales-pricing`: https://www.salesforce.com/sales/pricing/ - reuse label `inspiration only`
- `prod-028-source-zendesk-pricing`: https://www.zendesk.com/pricing/ - reuse label `inspiration only`

## Synthetic Campaign

- Client: `Northstar Workflow Labs`
- Product: `RouteSignal CRM`
- Product facts visible: `true`
- Payment collection enabled: `false`

## Same-Question Comparison

### PROD-028-Q01

- Customer question: How much would this cost for 12 users if we used the realistic plan?
- Baseline answer: That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
- Grounded answer: For 12 users, Growth is the realistic fit at $59 per user per month on annual billing, so subscription cost is $708 per month before taxes or add-ons. Assisted setup is a one-time $1,500 package.
- Fact refs used: `plan_growth_price, growth_minimum_users, onboarding_fee`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q02

- Customer question: What do we actually get in Growth that Starter does not have?
- Baseline answer: Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
- Grounded answer: Starter covers the shared lead inbox, pipeline, templates, callback tasks, reports, and CSV import. Growth adds lead routing, Gmail and Outlook sync, Slack alerts, Zapier handoffs, duplicate detection, and team reporting.
- Fact refs used: `starter_included, growth_included`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q03

- Customer question: Are we locked into a contract, or can we cancel if it does not work?
- Baseline answer: Understood. What written information would help procurement review this without asking you for anything firm today?
- Grounded answer: You can choose monthly or annual billing. Annual billing is 15% lower, and cancellation takes effect at the paid period boundary; there is no payment handled on this call.
- Fact refs used: `monthly_available, annual_available, cancellation_period_boundary, no_payment_call`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q04

- Customer question: How long would setup take if we already have a spreadsheet of leads?
- Baseline answer: Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
- Grounded answer: With a spreadsheet-ready team, assisted setup is typically two to four weeks after admin access and import scope are confirmed. Standard CSV import is included; deeper migration is the $900 package.
- Fact refs used: `typical_setup_weeks, csv_import, migration_package`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q05

- Customer question: Does it connect with the tools our team already uses?
- Baseline answer: Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
- Grounded answer: Yes. The synthetic campaign facts list Salesforce, HubSpot, Gmail, Outlook, Slack, Zapier, and CSV import as supported handoff paths, with final scope confirmed by a specialist.
- Fact refs used: `integrations_supported`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q06

- Customer question: Who can see the lead data? We need role control and audit logs.
- Baseline answer: Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
- Grounded answer: Role control and audit logs sit in the Scale plan, along with SSO, sandbox, approval workflows, custom roles, and priority support. A solutions specialist should confirm the exact security review.
- Fact refs used: `scale_security, specialist_review`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q07

- Customer question: Can you discount it if we pay yearly?
- Baseline answer: Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
- Grounded answer: The standard yearly option is annual billing with a 15% subscription reduction. Anything beyond that needs a written specialist quote, so I would not promise a custom discount on this call.
- Fact refs used: `annual_discount, custom_discount_quote`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q08

- Customer question: We only have six sales people. Are we too small for this?
- Baseline answer: Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
- Grounded answer: Six sales people is not too small. Starter begins at 3 users, and Growth begins at 5 users, so we would choose between those based on routing needs.
- Fact refs used: `eligibility_minimum, starter_minimum, growth_minimum`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q09

- Customer question: If we need SSO and a sandbox, is that included or is it a special request?
- Baseline answer: Good question. I want to check the approved product information before answering, so I do not guess on plan details.
- Grounded answer: SSO and sandbox are Scale-plan capabilities, not Starter or Growth defaults. Because those details affect security review, I would route the exact setup to a solutions specialist.
- Fact refs used: `scale_security, specialist_review`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q10

- Customer question: We already use spreadsheets and Pipedrive. Why would we even look at this?
- Baseline answer: Fair question. I can keep this call short: would it help if I first explain the concrete reason for reaching out?
- Grounded answer: I would not replace a setup that already works. This is worth reviewing only if routing, callback ownership, or reporting are the gaps; CSV import and CRM handoffs help evaluate that without starting from zero.
- Fact refs used: `no_badmouthing, routing_fit, csv_import`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q11

- Customer question: That sounds too expensive for us right now.
- Baseline answer: That makes sense. Is your bigger concern the monthly price, the contract terms, or whether reviewing options is worth your time?
- Grounded answer: That may be a reason to start smaller. Starter is $29 per user per month on annual billing, and the 14-day sandbox trial has no card requirement.
- Fact refs used: `starter_price, trial, no_pressure`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

### PROD-028-Q12

- Customer question: Can you promise it will increase revenue by 30 percent?
- Baseline answer: Thanks. To make this useful, is your main question about price, fit, timing, or exact product details?
- Grounded answer: I cannot promise a revenue lift. What I can say is RouteSignal CRM can centralize lead intake and route leads by region, source, priority, or owner.
- Fact refs used: `forbidden_revenue_guarantee, allowed_product_capability`
- Direct answer: `true`
- Factual correct: `true`
- Question overuse: `false`

