# VERTICAL-SALES-PLAYBOOKS-001

Status: pass

## Contract

- Non-integrated vertical sales adapter skeletons.
- Uses universal sales knowledge IDs where possible.
- No campaign migration or runtime routing integration in this phase.

## Vertical IDs

- automotive_service
- b2b_saas
- healthcare_admin_or_medical_equipment
- home_services
- insurance
- membership_or_subscription
- retail_or_ecommerce_support_sales
- telecom

## Regulated Caution Coverage

- automotive_service: automotive_service_safety_or_warranty, financial_or_payment_sensitive, legal_or_contract_sensitive
- b2b_saas: financial_or_payment_sensitive, legal_or_contract_sensitive
- healthcare_admin_or_medical_equipment: financial_or_payment_sensitive, healthcare_admin_or_medical_equipment, legal_or_contract_sensitive
- home_services: financial_or_payment_sensitive, home_services_safety_or_estimate, legal_or_contract_sensitive
- insurance: financial_or_payment_sensitive, insurance, legal_or_contract_sensitive
- membership_or_subscription: financial_or_payment_sensitive, legal_or_contract_sensitive, membership_or_subscription_cancellation
- retail_or_ecommerce_support_sales: financial_or_payment_sensitive, legal_or_contract_sensitive, retail_or_ecommerce_refund_warranty_availability
- telecom: financial_or_payment_sensitive, legal_or_contract_sensitive, telecom_contract_or_coverage

## Forbidden Terms

- Campaign term check passed: true
- Forbidden campaign terms found: none
- Forbidden claim phrases found: none

## Suggested Universal Additions

- Count: 0
