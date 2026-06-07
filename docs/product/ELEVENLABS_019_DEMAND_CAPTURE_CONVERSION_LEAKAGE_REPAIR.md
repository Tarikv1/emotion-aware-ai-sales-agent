# ELEVENLABS-019 Demand Capture Conversion Leakage Repair

Package ID: `ELEVENLABS-019-demand-capture-conversion-leakage-repair`

## Decision

`ELEVENLABS-018` made the value answer safer, but the mechanism was still too
abstract. Phrases like owned indexable page, local visibility support, trust
basics, contact path, clearer page, and something to judge are not enough when a
buyer asks what the website does for the business.

This checkpoint changes the sales value layer to demand capture and conversion
leakage:

- The website does not create guaranteed demand.
- The website can help the business waste less existing attention.
- Existing attention may come from Google, Google Maps, Instagram, Facebook,
  referrals, QR codes, print, word of mouth, ads, direct search, or shared links.
- The useful sales question is whether someone who already finds or hears about
  the business gets enough trust, offer clarity, and convenience to take the next
  step.
- The free mockup is the proof object before payment.

Approved pattern:

`Not as a guarantee. The real point is not magic new traffic. It is helping you
waste less of the attention you already get. If someone finds you through
Google, Instagram, a referral, or a shared link, the page should quickly show why
they should trust you, what you offer, and what to do next.`

## Demand-Capture Mechanisms

Vertical mechanisms added:

- Restaurant / cafe: Google Maps, Instagram, referrals, walk-by interest to
  reserve, order, call, or visit.
- Salon / barber: Instagram, referrals, and Google search to appointment booking.
- Plumber / urgent service: emergency search, referrals, and local maps to call.
- Mechanic / repair shop: Google, referrals, and reviews to call or estimate.
- Law office: Google, referral, and local search to consultation request.
- Dental / clinic: Google, referral, and insurance/provider search to
  appointment request.
- Real estate: broker page, referral, Google, and social to seller inquiry.
- Gym / trainer: Instagram, referrals, and local search to trial/session.
- Home cleaning: Google, referrals, and local groups to quote request.
- HVAC / electrician: urgent search, referrals, and Google Maps to call or quote.

## V4 Simulation Criteria

New V4 criteria live in:

`runtime/providers/elevenlabs_agents/tests/web_design_demand_capture_conversion_leakage_v4_simulation_tests.json`

Folder target for offline request generation:

`Atlas Web Studio - Cross-Vertical Local Business Simulation V4`

The V4 tests fail value answers that do not include:

- no-guarantee boundary
- existing attention source
- conversion leakage/action mechanism
- proof-before-purchase step

Covered cases:

- plumber asking about more emergency calls
- salon asking if a website gets more bookings
- restaurant asking if a website brings more customers
- mechanic asking if a website builds trust
- dental office asking if a website brings new patients
- law office asking about ranking and consultation inquiries
- Google/Instagram status quo objection

## Commands

Validate without provider calls:

```powershell
python scripts\validate_elevenlabs_019_demand_capture_conversion_leakage_repair.py
```

Required regression chain:

```powershell
python scripts\validate_elevenlabs_018_sales_value_and_contact_control_repair.py
git diff --check
```

## Boundary

- No ElevenLabs API calls.
- No OpenAI API calls.
- No live outbound calls.
- No lead scraping.
- No CRM, email, calendar, payment, or account tools are enabled.
- No private customer data is included.
- No API key value is stored in tracked files.
- No production readiness is claimed; production readiness is not claimed.
- A fresh V4 simulation run and human review are required before any green or
  production-readiness claim.
