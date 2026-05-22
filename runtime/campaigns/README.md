# Local Campaign Registry

This directory stores local, file-backed generic SalesCampaign configs for deterministic dry-run validation.

Rules:

- Configs are JSON only.
- Example configs must be synthetic and must not contain customer data, private transcripts, secrets, provider keys, audio, or CRM/email/calendar instructions.
- Loading goes through `runtime.core.campaign_registry.load_campaign_config`.
- Invalid generic configs fail closed through `CampaignConfigValidationError`.
- RouteSignal live-demo behavior is not a fallback for invalid generic configs.
- `allowed_claims` must be present. It may be empty when no claim is approved.
- Regulated verticals must include non-empty `blocked_claims` and explicit `regulated_cautions`.
- Runtime safety flags default to false and may not be set true in these local configs.

Expected local structure:

```text
runtime/campaigns/
  README.md
  schema/campaign_config.schema.json
  examples/
    synthetic-insurance-review.json
    synthetic-telecom-plan-review.json
    synthetic-home-services-estimate.json
    synthetic-b2b-saas-operations.json
    synthetic-healthcare-admin-review.json
    synthetic-automotive-service-review.json
    synthetic-membership-plan-review.json
    synthetic-retail-support-review.json
```
