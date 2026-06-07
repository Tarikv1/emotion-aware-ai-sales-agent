# Vertical General Playbooks

Layer: Universal Sales RAG

Category ID: `vertical_general_playbooks`

Owns: reusable vertical lenses such as local services, restaurants, clinics, professional services, education, trades, ecommerce, SaaS, nonprofits, and regulated industries.

Does Not Own: vertical-specific claims, compliance requirements, customer results, pricing, or proof for a campaign.

Retrieval Triggers: "restaurant", "clinic", "local business", "SaaS", "ecommerce", "professional services", "regulated", "trade", "nonprofit".

Operating Rules: use vertical as context for likely concerns, not as proof. Local services often care about calls, trust, and scheduling. SaaS often cares about integration, adoption, security, and ROI. Regulated verticals require stricter claim and handoff discipline.

Failure Modes: stereotyping the buyer, inventing vertical facts, assuming regulation details, or importing one vertical's playbook into another without campaign approval.

Campaign Overlay Handoff: campaign overlay decides the specific vertical playbook, approved language, proof, and forbidden claims for the current campaign.
