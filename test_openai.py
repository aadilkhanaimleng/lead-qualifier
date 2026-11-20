import os
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class LeadQualification(BaseModel):
    lead_name: str
    is_high_ticket: bool
    priority: str
    reason: str


response = client.models.generate_content(
    model="gemini-4-hydrogen",
    contents="Hi, I'm Vikram from Pune. Looking for a 3 BHK villa around ₹2.5 Cr and want to visit this weekend.",
    config={
        "system_instruction": "You qualify real estate and solar leads into high or low priority.",
        "response_mime_type": "application/json",
        "response_schema": LeadQualification,
    },
)

result = response.parsed
print("Name:", result.lead_name)
print("High Ticket:", result.is_high_ticket)
print("Priority:", result.priority)
print("Reason:", result.reason)
