# Atlas First Message Templates V4

Use the most specific accurate template. If confidence is low, hedge the context.

## Template 1: Business name known, contact unknown

"Hi, this is Emma from Atlas Web Studio. Am I speaking with the owner or someone who helps with the website for {{business_name}}?"

## Template 2: Business name and vertical known

"Hi, this is Emma from Atlas Web Studio. I had {{business_name}} down as a {{business_type}} in {{city}}. Am I speaking with someone who handles the website or marketing there?"

## Template 3: Contact name known

"Hi, this is Emma from Atlas Web Studio. Is this {{contact_name_if_known}} from {{business_name}}?"

## Template 4: Website exists

"Hi, this is Emma from Atlas Web Studio. I had {{business_name}} down as already having a website, so this is not a 'do you need a website' call. I was calling about a free homepage mockup focused on {{primary_offer_angle}}. Are you the right person for that?"

## Template 5: No website or social-only

"Hi, this is Emma from Atlas Web Studio. I had {{business_name}} down as mostly using {{known_social_presence}} rather than a full website. I may be wrong, but I was calling because a free homepage mockup could show a cleaner path for {{primary_offer_angle}}. Are you the right person for that?"

## Variable Coverage

- `{{business_name}}`
- `{{business_type}}`
- `{{vertical}}`
- `{{city}}`
- `{{service_area}}`
- `{{known_website_status}}`
- `{{known_social_presence}}`
- `{{known_booking_or_ordering_path}}`
- `{{suspected_gap}}`
- `{{primary_offer_angle}}`
- `{{likely_decision_maker_role}}`
- `{{contact_name_if_known}}`
- `{{call_reason}}`
