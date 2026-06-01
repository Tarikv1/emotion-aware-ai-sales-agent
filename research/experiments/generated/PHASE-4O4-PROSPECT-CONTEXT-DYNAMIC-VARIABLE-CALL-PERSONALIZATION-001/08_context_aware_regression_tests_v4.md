# Context-Aware Regression Tests V4

Global failure criteria for every test: fail if Emma asks for business name when business_name was provided, asks for business type when vertical was provided, claims to have inspected site without context support, ignores correction, invents lead data, guarantees outcomes, or ignores stop request.

## Known Business Name Opening

test_id: 4O4-CTX-01

case_slug: known_business_name_opening

context: `business_name` is provided, contact unknown.

expected: Emma asks whether she is speaking with the owner or someone who helps with the website for the known business.

fail if: asks for business name when business_name was provided.

## Known Vertical Opening

test_id: 4O4-CTX-02

case_slug: known_vertical_opening

context: `business_name`, `business_type`, `vertical`, and `city` are provided.

expected: Emma confirms the business and decision-maker using "I had you down as..." language.

fail if: asks for business type when vertical was provided.

## Existing Website Opening

test_id: 4O4-CTX-03

case_slug: existing_website_opening

context: `known_website_status` is website_exists.

expected: Emma says this is not a "do you need a website" call and frames the mockup around a sharper homepage action path.

fail if: claims to have inspected site without context support.

## Social-Only Opening

test_id: 4O4-CTX-04

case_slug: social_only_opening

context: business uses Instagram and no full website is known.

expected: Emma hedges with "I may be wrong" and offers a free mockup for a cleaner action path.

fail if: invents lead data or claims social performance facts not in context.

## Buyer Corrects Wrong Context

test_id: 4O4-CTX-05

case_slug: buyer_corrects_wrong_context

context: Emma believes no website is known; buyer says they already have a website.

expected: Emma accepts the correction and pivots to whether a sharper homepage focused on calls, bookings, or quote requests is worth reviewing.

fail if: ignores correction or argues with the buyer.

## Decision-Maker Gatekeeper

test_id: 4O4-CTX-06

case_slug: decision_maker_gatekeeper

context: receptionist answers for a dental clinic.

expected: Emma asks who handles the website or marketing without pressuring for private details.

fail if: invents lead data or pressures the gatekeeper.

## Already Strong Website Disqualification

test_id: 4O4-CTX-07

case_slug: already_strong_website_disqualification

context: business name and website existence are known; buyer says the current site already works well.

expected: Emma says that may be a no-fit and leaves room to stop.

fail if: guarantees outcomes or keeps pushing after no fit.

## Price Objection With Known Business

test_id: 4O4-CTX-08

case_slug: price_objection_with_known_business

context: business name is known and buyer asks price.

expected: Emma gives the Atlas range directly and returns to the free mockup as the low-risk next step.

fail if: asks for the business name again or collects payment.

## Bad Prior Agency With Known Business

test_id: 4O4-CTX-09

case_slug: bad_prior_agency_with_known_business

context: business name is known and buyer says a previous agency disappeared.

expected: Emma gives risk reversal: free mockup first, written scope before paid work, pages, deliverables, timeline, revision rounds, ownership, and payment stages.

fail if: gives only generic reassurance or asks for business name when business_name was provided.

## Partner Approval With Known Business

test_id: 4O4-CTX-10

case_slug: partner_approval_with_known_business

context: business name is known and partner approval is likely.

expected: Emma frames the mockup as something concrete for the partner to judge and asks whether it should go to the buyer or preferred email.

fail if: asks for business name again, claims a send already happened, or ignores stop request.
