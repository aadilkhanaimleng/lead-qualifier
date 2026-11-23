from pydantic import BaseModel


class LeadQualification(BaseModel):
    lead_name: str
    niche: str
    is_high_ticket: bool
    priority: str
    reason: str


def qualify_lead_rules(name: str, niche: str, message: str) -> LeadQualification:
    text = message.lower()

    if niche.lower() == "real_estate":
        high_ticket = any(k in text for k in ["cr", "crore", "villa", "penthouse", "plot"])
        urgent = any(k in text for k in ["weekend", "visit", "ready to buy", "immediately", "site visit"])
    else:  # solar
        high_ticket = any(k in text for k in ["kw", "commercial", "factory", "lakh", "rooftop"])
        urgent = any(k in text for k in ["quote", "site survey", "this week", "bill", "install"])

    priority = "HIGH" if (high_ticket and urgent) else ("MEDIUM" if (high_ticket or urgent) else "LOW")
    reason = f"Niche={niche}, high_ticket={high_ticket}, urgent={urgent}"

    return LeadQualification(
        lead_name=name,
        niche=niche,
        is_high_ticket=high_ticket,
        priority=priority,
        reason=reason,
    )


sample_leads = [
    ("Vikram", "real_estate", "Hi, I'm Vikram from Pune. Looking for a 3 BHK villa around ₹2.5 Cr and want to visit this weekend."),
    ("Ramesh", "solar", "Need a 10 kW rooftop solar quote and site survey this week for my house."),
    ("Amit", "real_estate", "Just checking general 1 BHK prices in the area."),
]

for name, niche, msg in sample_leads:
    out = qualify_lead_rules(name, niche, msg)
    print(out.model_dump())
