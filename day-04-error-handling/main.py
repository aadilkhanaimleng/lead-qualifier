import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="Lead Qualifier Mini API Service")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"]


class LeadInput(BaseModel):
    name: str
    email: str
    company: str | None = None
    message: str


class QualificationOutput(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Lead quality score 0-100")
    tier: str = Field(..., description="HOT, WARM, or COLD")
    summary: str = Field(..., description="1-line reason for the score")


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "lead-qualifier"}


@app.post("/qualify", response_model=QualificationOutput)
def qualify_lead(lead: LeadInput):
    prompt = f"""
Qualify this inbound B2B lead for an AI automation agency:
Name: {lead.name}
Email: {lead.email}
Company: {lead.company or 'Not provided'}
Message: {lead.message}
"""
    last_error = None
    for model_name in MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=QualificationOutput,
                    ),
                )
                return QualificationOutput.model_validate_json(response.text)
            except Exception as e:
                last_error = e
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    time.sleep(1)
                    continue
                break

    raise HTTPException(status_code=500, detail=str(last_error))
