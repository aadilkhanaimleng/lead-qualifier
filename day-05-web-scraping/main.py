import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types
from crawl4ai import AsyncWebCrawler

load_dotenv()

app = FastAPI(title="Lead Qualifier API with Web Scraping")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODELS = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash"]


class LeadInput(BaseModel):
    name: str
    email: str
    company: str | None = None
    website: str | None = None
    message: str


class QualificationOutput(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Lead quality score 0-100")
    tier: str = Field(..., description="HOT, WARM, or COLD")
    summary: str = Field(..., description="1-line reason for the score")
    scraped_used: bool = Field(..., description="Whether company website context was scraped")


async def scrape_website_context(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            if result.success and result.markdown:
                return result.markdown[:2500]
    except Exception:
        pass
    return ""


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "lead-qualifier-day-05"}


@app.post("/qualify", response_model=QualificationOutput)
async def qualify_lead(lead: LeadInput):
    website_context = ""
    if lead.website:
        website_context = await scrape_website_context(lead.website)

    prompt = f"""
Qualify this inbound B2B lead for an AI automation agency:
Name: {lead.name}
Email: {lead.email}
Company: {lead.company or 'Not provided'}
Website: {lead.website or 'Not provided'}
Message: {lead.message}

Scraped Company Website Content (if available):
{website_context or 'No website content scraped.'}
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
                parsed = QualificationOutput.model_validate_json(response.text)
                parsed.scraped_used = bool(website_context)
                return parsed
            except Exception as e:
                last_error = e
                if "503" in str(e) or "UNAVAILABLE" in str(e):
                    time.sleep(1)
                    continue
                break

    raise HTTPException(status_code=500, detail=str(last_error))
