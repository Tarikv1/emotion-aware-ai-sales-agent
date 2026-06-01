# Campaign Intake Validation Rules

## Severity Levels

- blocker: adapter rendering must stop until fixed.
- warning: rendering may continue only with visible review notes.
- optional: useful improvement but not required for a safe package.

## Rules

### missing_pricing_policy

severity: blocker

Flag when pricing_model is empty or guarantees_or_refund_policy avoids commercial terms entirely. The agent needs pricing behavior even when exact prices are unavailable.

### missing_target_customer

severity: blocker

Flag when target_customer_segments or buyer_personas are empty. A sales agent without a target buyer will over-pitch and fail qualification.

### missing_conversion_goal

severity: blocker

Flag when primary_conversion_goal is missing or not actionable. The renderer needs one primary next step.

### missing_disqualification_rules

severity: blocker

Flag when disqualification_rules are empty. The agent needs explicit no-fit boundaries.

### missing_forbidden_claims

severity: blocker

Flag when forbidden_claims are empty. The safest default is not enough because campaign owners must name risky claims the agent must not make.

### unsupported_guarantees

severity: blocker

Flag when the intake claims guaranteed results without proof, policy, or legal approval. Example: claiming guaranteed leads without evidence is a blocker.

### vague_product_description

severity: warning

Flag when company_description, short_offer_summary, what_product_does, or what_product_does_not_do are generic enough that the agent cannot explain the offer plainly.

### unclear_next_step

severity: blocker

Flag when close_paths do not define an allowed commitment and spoken close. The agent must know exactly what to ask for.

### fake_side_effect_risk

severity: blocker

Flag when tool_permissions suggest an action but the current shell cannot perform it. Example: tool says "send email" but no email tool exists.

### third_party_impersonation_risk

severity: blocker

Flag when identity, proof, comparison, or authority language implies the agent represents an unaffiliated third party.

### no_compliance_boundary

severity: blocker

Flag when compliance_constraints are empty. A commercial agent needs explicit claims and conduct boundaries.

### weak_objection_responses

severity: warning

Flag when common_objections exist but objection_responses are missing, vague, or do not answer the objection directly.

### no_proof_points

severity: warning

Flag when proof_points and case_studies_or_examples are empty. The agent may still render, but it must use modest language and avoid proof-based persuasion.

### no_competitor_alternative_positioning

severity: warning

Flag when competitors_or_alternatives or comparison_rules are empty. The agent will be weaker when buyers mention alternatives.

### no_stop_request_policy

severity: blocker

Flag when stop_request_policy is missing. Missing stop-request policy is always a blocker because stop requests override persuasion.

## Optional Quality Checks

### tone_style_too_broad

severity: optional

Flag when tone_and_style is only generic, such as "friendly and professional", without pressure, length, or directness guidance.

### proof_not_buyer_relevant

severity: optional

Flag when proof points exist but are not tied to target buyer pains or personas.
