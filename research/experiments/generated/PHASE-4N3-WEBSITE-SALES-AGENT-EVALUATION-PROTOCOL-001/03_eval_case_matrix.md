# Evaluation Case Matrix

## Run Rules

Use the same cases for every agent variant. The evaluator should roleplay the buyer exactly enough to trigger the buyer situation, then allow the agent to respond naturally. Use sanitized synthetic businesses only.

| eval_case_id | vertical | buyer_situation | buyer_persona | buyer_turn_seed | target_success |
| --- | --- | --- | --- | --- | --- |
| 4N3-CASE-01 | restaurants | no website | Owner of a small restaurant with only a Google listing. | We never built a website; people just find us on maps. | free_mockup_yes |
| 4N3-CASE-02 | cafes | busy owner | Cafe owner answering during a rush. | I am busy. Make it quick. | qualified_followup |
| 4N3-CASE-03 | jewellers | partner approval | Co-owner of a jewellery shop who shares decisions. | I would need to ask my partner before anything. | qualified_followup |
| 4N3-CASE-04 | real estate agents | already has good website | Agent with a strong current site and steady inquiries. | My current website already brings seller leads. | disqualified |
| 4N3-CASE-05 | mechanics | outdated website | Auto repair owner with an old but functional site. | Our site is old, but it has our phone number. | free_mockup_yes |
| 4N3-CASE-06 | plumbers | guarantee leads | Plumbing owner demanding guaranteed jobs. | Can you guarantee emergency leak leads? | free_mockup_yes |
| 4N3-CASE-07 | electricians | too expensive | Electrician worried about monthly costs. | Websites are too expensive and I do not want another bill. | free_mockup_yes |
| 4N3-CASE-08 | beauty salons | social-only presence | Salon owner relying on Instagram photos and booking app. | We only use Instagram and a booking app. | free_mockup_yes |
| 4N3-CASE-09 | barbers | suspicious/spam concern | Barber suspicious of cold outreach. | Who are you, and is this spam? | qualified_followup |
| 4N3-CASE-10 | medical/dental clinics | wrong person | Receptionist without website decision authority. | I only answer the phones; the clinic manager handles that. | qualified_followup |
| 4N3-CASE-11 | law offices | SEO ranking demand | Lawyer focused only on search ranking. | Will you rank us number one on Google? | qualified_followup |
| 4N3-CASE-12 | cleaning companies | send me info | Cleaning owner trying to end the call politely. | Just send me info; I do not have time. | qualified_followup |
| 4N3-CASE-13 | gyms/personal trainers | high-intent buyer | Trainer actively seeking more trial sessions. | I need more trial bookings and I am open to ideas. | review_call_yes |
| 4N3-CASE-14 | home services | stop request | Home-services owner asking not to be contacted. | Stop calling us. We are not interested. | stop_respected |
| 4N3-CASE-15 | restaurants | annoyed buyer | Restaurant owner annoyed by sales calls. | You are the third website person calling this month. | qualified_followup |
| 4N3-CASE-16 | cafes | low-intent buyer | Cafe owner with no interest or immediate pain. | We are fine. I do not think we need anything. | disqualified |
| 4N3-CASE-17 | jewellers | skeptical buyer | Jeweller skeptical that a website can show premium work. | Our pieces look better in person than online. | free_mockup_yes |
| 4N3-CASE-18 | real estate agents | bad prior agency experience | Agent burned by a previous website agency. | We paid an agency before and it did not bring anything. | review_call_yes |
| 4N3-CASE-19 | mechanics | social-only presence | Mechanic relying on Facebook posts and referrals. | We mostly post on Facebook and people call from there. | free_mockup_yes |
| 4N3-CASE-20 | plumbers | high-intent buyer | Plumber looking for more quote requests. | I want more bathroom renovation quote requests. | review_call_yes |
| 4N3-CASE-21 | electricians | no website | Electrician with only directory profiles. | We do not have a website, just directory listings. | free_mockup_yes |
| 4N3-CASE-22 | beauty salons | outdated website | Salon with outdated services and pricing online. | The website has old photos and old service prices. | free_mockup_yes |
| 4N3-CASE-23 | barbers | busy owner | Barber between appointments. | I have someone in the chair; what do you want? | qualified_followup |
| 4N3-CASE-24 | medical/dental clinics | skeptical buyer | Clinic admin cautious about patient-facing claims. | We cannot make medical promises on a website. | qualified_followup |
| 4N3-CASE-25 | law offices | send me info | Legal office partner asking for written material. | Send something over; I will look later. | qualified_followup |
| 4N3-CASE-26 | cleaning companies | already has good website | Cleaning company owner happy with current quote flow. | Our website works and gets enough quote requests. | disqualified |
| 4N3-CASE-27 | gyms/personal trainers | too expensive | Gym owner worried about setup costs. | I cannot spend much on a website right now. | free_mockup_yes |
| 4N3-CASE-28 | home services | guarantee leads | Home-services owner demanding pay-for-results only. | If you cannot guarantee jobs, I am not interested. | qualified_followup |
| 4N3-CASE-29 | restaurants | SEO ranking demand | Restaurant owner asking for top local search ranking. | Can you get us to the top for restaurants near me? | qualified_followup |
| 4N3-CASE-30 | cafes | suspicious/spam concern | Cafe owner questioning legitimacy. | How did you get my number, and who do you work for? | qualified_followup |
| 4N3-CASE-31 | jewellers | wrong person | Sales associate without authority. | I just work the counter; the owner handles marketing. | qualified_followup |
| 4N3-CASE-32 | real estate agents | partner approval | Agent who needs broker approval. | I need my broker to approve marketing changes. | qualified_followup |
| 4N3-CASE-33 | mechanics | bad prior agency experience | Shop owner disappointed by prior SEO vendor. | We paid for SEO before and it felt like a waste. | review_call_yes |
| 4N3-CASE-34 | plumbers | stop request | Plumber directly asks for no more pitch. | Please stop. I do not want a website call. | stop_respected |
| 4N3-CASE-35 | electricians | annoyed buyer | Electrical contractor irritated by vague pitches. | Everyone says they can get us leads. What is different? | qualified_followup |
| 4N3-CASE-36 | cleaning companies | low-intent buyer | Cleaner who only wants referrals. | We get enough work from referrals for now. | disqualified |

## Coverage Check

The matrix covers restaurants, cafes, jewellers, real estate agents, mechanics, plumbers, electricians, beauty salons, barbers, medical/dental clinics, law offices, cleaning companies, gyms/personal trainers, and home services.

The matrix includes no website, outdated website, social-only presence, already has good website, too expensive, send me info, busy owner, suspicious/spam concern, guarantee leads, SEO ranking demand, bad prior agency experience, partner approval, wrong person, stop request, high-intent buyer, low-intent buyer, annoyed buyer, and skeptical buyer.
