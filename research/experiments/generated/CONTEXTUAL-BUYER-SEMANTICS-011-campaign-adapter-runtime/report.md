# CONTEXTUAL-BUYER-SEMANTICS-011 Campaign Adapter Runtime

Status: pass

## Synthetic Campaigns

- b2b_saas: playbook=synthetic-b2b-saas-contextual-011-playbook, vertical=b2b_saas, core_gaps=['manual_work', 'integration_risk', 'visibility_gap']
- home_services: playbook=synthetic-home-services-contextual-011-playbook, vertical=home_services, core_gaps=['service_need', 'scheduling_urgency', 'estimate_or_property_details']
- insurance: playbook=synthetic-insurance-contextual-011-playbook, vertical=insurance, core_gaps=['coverage_fit', 'premium_or_budget', 'renewal_or_timing']
- telecom: playbook=synthetic-telecom-contextual-011-playbook, vertical=telecom, core_gaps=['coverage_or_availability', 'plan_fit', 'contract_or_switching']

## RouteSignal Preservation

- callbacks clear: semantic=current_gap_clear, target_gap=callbacks, playbook_id=ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001

## Dependency Boundary

- imports_campaign_playbook_adapter: true
- imports_sales_diagnostic_playbook: false
- module_core_gaps_assignment: false
- module_gap_labels_assignment: false
