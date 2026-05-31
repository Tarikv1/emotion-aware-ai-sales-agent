# Public OpenAI ChatGPT Plans Source Notes

Checkpoint: `PUBLIC-OPENAI-SOURCE-BUNDLE-001`

Retrieved: `2026-05-24T18:18:00Z`

Last verified: `2026-05-31T02:25:00Z`

Last verification checkpoint: `PHASE-4L5-OPENAI-CLAIM-PRECISION-HARDENING-001`

Scope: official public OpenAI, ChatGPT, and OpenAI Help Center sources only. No non-OpenAI sources were used.

## Sources Used

- `https://chatgpt.com/pricing/` for the public plan comparison and plan names.
- `https://help.openai.com/en/articles/12677804-what-is-chatgpt-faq` for the high-level ChatGPT description, web/mobile availability, plan overview, and variable-limit caveat.
- `https://help.openai.com/en/articles/9260256-chatgpt-capabilities-overview` for broad ChatGPT capabilities.
- `https://help.openai.com/en/articles/11989085-what-is-chatgpt-go` for Go positioning, features, sign-up path, and privacy note.
- `https://help.openai.com/en/articles/6950777-what-is-chatgpt-plus` for Plus price, Plus benefits, sign-up path, API-separate boundary, limits, and privacy note.
- `https://help.openai.com/en/articles/9793128-what-is-chatgpt-pro` for Pro positioning, Pro tier pricing, upgrade path, features, and usage-guardrail caveat.
- `https://help.openai.com/en/articles/8792828-what-is-chatgpt-business` for Business seat types, pricing, Business Codex seat boundary, minimum seats, privacy, and API-separate boundary.
- `https://help.openai.com/en/articles/8265053-what-is-chatgpt-enterprise` for Enterprise positioning, organization-level purchase, contact-sales route, admin/security controls, and API membership boundary.
- `https://help.openai.com/en/articles/7730893-data-controls-in-chatgpt` for consumer training opt-out and Temporary Chat boundaries.
- `https://openai.com/enterprise-privacy/` for business-data ownership/control, no-training-by-default boundary, enterprise controls, and data handling caveats.

## Notes

- Source claims are paraphrased and represented as claim objects in `source_manifest.json`.
- Short quote excerpts are included only where useful for traceability.
- Price fields are conservative. If a visible source page did not expose a price clearly to the parser, the campaign fixture records `source_visible_but_parser_blank` or `requires_manual_review` instead of inventing a price.
- Phase 4L4 rechecked the official ChatGPT pricing page and ChatGPT Go help article. The captured taxonomy remains individual `Free`, `Go`, `Plus`, `Pro` and business/enterprise `Business`, `Enterprise`, with Go treated as the lower-cost paid individual step between Free and Plus.
- Phase 4L5 added claim precision categories for buyer-facing speech:
  - `stable_source_claim`
  - `current_terms_claim_requires_caveat`
  - `source_conflict_or_ambiguous`
  - `unsupported_do_not_say`
  - `official_route_only`
- Phase 4L5 downgraded exact Go feature-list speech to `source_conflict_or_ambiguous`. The Go help article broadly names projects, tasks, and custom GPTs, while the pricing-page feature table can show more granular or different feature states such as Tasks availability. The safe spoken wording is: "Go gives more access than Free to common ChatGPT features, but exact current feature availability and limits should be checked on the official plans page."
- Exact pricing, terms, feature availability, model access, usage limits, regional availability, ads status, privacy/training terms, and Business/Enterprise security or compliance specifics require an official-page or contact-sales route.
- This is an internal public-data simulation. It is not an official OpenAI sales agent and must not claim OpenAI affiliation or authorization.
- API usage is treated as separate from ChatGPT subscriptions where the official Plus, Business, or Enterprise sources support that boundary.
