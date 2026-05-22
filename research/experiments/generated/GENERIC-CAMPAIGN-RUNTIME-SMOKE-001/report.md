# GENERIC-CAMPAIGN-RUNTIME-SMOKE-001

Status: pass

## Synthetic Campaigns

- b2b_saas: campaign=synthetic-b2b-saas-runtime-001, playbook=synthetic-b2b-saas-runtime-001-playbook, vertical=b2b_saas, core_gaps=['manual_work', 'integration_risk', 'visibility_gap']
- home_services: campaign=synthetic-home-services-runtime-001, playbook=synthetic-home-services-runtime-001-playbook, vertical=home_services, core_gaps=['service_need', 'scheduling_urgency', 'estimate_or_property_details']
- insurance: campaign=synthetic-insurance-runtime-001, playbook=synthetic-insurance-runtime-001-playbook, vertical=insurance, core_gaps=['coverage_fit', 'premium_or_budget', 'renewal_or_timing']
- telecom: campaign=synthetic-telecom-runtime-001, playbook=synthetic-telecom-runtime-001-playbook, vertical=telecom, core_gaps=['coverage_or_availability', 'plan_fit', 'contract_or_switching']

## Smoke Coverage

- Scenario A: agent open
- Scenario B: permission acknowledgement
- Scenario C: first gap clear
- Scenario D: pain confirmed
- Scenario E: send info
- Scenario F: right person
- Scenario G: regulated caution for insurance, telecom, and home_services

Note: home_services Scenario C follows the supplied utterance `scheduling is fine`, so the expected target is `scheduling_urgency` rather than the first listed gap.

## RouteSignal Preservation

- callbacks clear: semantic=current_gap_clear, target_gap=callbacks, playbook_id=ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001
