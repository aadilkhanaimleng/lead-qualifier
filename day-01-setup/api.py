from fastapi import FastAPI
from pydantic import BaseModel

from hybrid_qualifier import qualify_lead_hybrid
from qualifier_core import LeadQualification

app = FastAPI(title="Lead Qualifier API")


class LeadInput(BaseModel):
    lead_name: str
    niche: str  # "real_estate" or "solar"
    message: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/qualify", response_model=LeadQualification)
def qualify_endpoint(lead: LeadInput):
    return qualify_lead_hybrid(
        name=lead.lead_name,
        niche=lead.niche,
        message=lead.message,
    )