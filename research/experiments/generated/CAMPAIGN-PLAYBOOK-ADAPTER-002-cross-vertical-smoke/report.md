# CAMPAIGN-PLAYBOOK-ADAPTER-002 Cross-Vertical Smoke

Status: pass

## Synthetic Campaigns

- synthetic-automotive-service-001: vertical=automotive_service, playbook=synthetic-automotive-service-001-playbook, gaps=vehicle_issue, repair_timing, warranty_or_estimate, cautions=automotive_service_safety_or_warranty, legal_or_contract_sensitive, financial_or_payment_sensitive
- synthetic-b2b-saas-001: vertical=b2b_saas, playbook=synthetic-b2b-saas-001-playbook, gaps=manual_work, integration_risk, visibility_gap, cautions=legal_or_contract_sensitive, financial_or_payment_sensitive
- synthetic-healthcare-admin-001: vertical=healthcare_admin_or_medical_equipment, playbook=synthetic-healthcare-admin-001-playbook, gaps=admin_workflow_need, equipment_or_service_fit, specialist_review_needed, cautions=healthcare_admin_or_medical_equipment, financial_or_payment_sensitive, legal_or_contract_sensitive
- synthetic-home-services-001: vertical=home_services, playbook=synthetic-home-services-001-playbook, gaps=service_need, scheduling_urgency, estimate_or_property_details, cautions=home_services_safety_or_estimate, legal_or_contract_sensitive, financial_or_payment_sensitive
- synthetic-insurance-001: vertical=insurance, playbook=synthetic-insurance-001-playbook, gaps=coverage_fit, premium_or_budget, renewal_or_timing, cautions=insurance, financial_or_payment_sensitive, legal_or_contract_sensitive
- synthetic-membership-001: vertical=membership_or_subscription, playbook=synthetic-membership-001-playbook, gaps=plan_fit, renewal_or_cancellation, usage_or_value, cautions=membership_or_subscription_cancellation, financial_or_payment_sensitive, legal_or_contract_sensitive
- synthetic-retail-support-001: vertical=retail_or_ecommerce_support_sales, playbook=synthetic-retail-support-001-playbook, gaps=product_fit, availability_or_delivery, return_or_warranty, cautions=retail_or_ecommerce_refund_warranty_availability, financial_or_payment_sensitive, legal_or_contract_sensitive
- synthetic-telecom-001: vertical=telecom, playbook=synthetic-telecom-001-playbook, gaps=coverage_or_availability, plan_fit, contract_or_switching, cautions=telecom_contract_or_coverage, legal_or_contract_sensitive, financial_or_payment_sensitive

## RouteSignal Preservation

- Default playbook id: ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001
- Live campaign playbook id: ROUTESIGNAL-DIAGNOSTIC-PLAYBOOK-001
- 4B3 behavior validator still valid: true

## Safety

- creates_calendar_event: false
- local_llm_calls_made: false
- opens_prod_102: false
- provider_calls_made: false
- sends_email: false
- writes_crm: false
