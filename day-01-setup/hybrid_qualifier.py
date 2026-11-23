import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors
from pydantic import BaseModel

from qualifier_core import LeadQualification, qualify_lead_rules

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


def qualify_lead_hybrid(
    name: str,
    niche: str,
    message: str,
    model: str = "gemini-3.1-flash-lite",
) -> LeadQualification:
    if client:
        try:
            response = client.models.generate_content(
                model=model,
                contents=f"Niche: {niche}\nLead Name: {name}\nMessage: {message}",
                config={
                    "system_instruction": (
                        "You qualify real estate and solar leads in India. "
                        "Return structured output matching LeadQualification. "
                        "Set priority strictly to HIGH, MEDIUM, or LOW."
                    ),
                    "response_mime_type": "application/json",
                    "response_schema": LeadQualification,
                },
            )
            if response.parsed:
                return response.parsed
        except (errors.ServerError, errors.ClientError, Exception):
            pass

    fallback = qualify_lead_rules(name, niche, message)
    fallback.reason = f"[Fallback] {fallback.reason}"
    return fallback


if __name__ == "__main__":
    leads = [
        ("Vikram", "real_estate", "Hi, I'm Vikram from Pune. Looking for a 3 BHK villa around ₹2.5 Cr and want to visit this weekend."),
        ("Ramesh", "solar", "Need a 10 kW rooftop solar quote and site survey this week for my house."),
        ("Amit", "real_estate", "Just checking general 1 BHK prices in the area."),
    ]
    for name, niche, msg in leads:
        res = qualify_lead_hybrid(name, niche, msg)
        print(res.model_dump())