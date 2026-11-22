import asyncio
import os
import time
from typing import Literal
from dotenv import load_dotenv, find_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv(find_dotenv())
os.environ.pop("OPENAI_BASE_URL", None)

client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


class LeadScore(BaseModel):
    category: Literal["HOT", "WARM", "COLD"]
    budget_tier: str = Field(description="Extracted budget in AED or AUD")
    urgency: str = Field(description="Buying timeline e.g. Immediate, 1-3 months, Exploring")
    next_action: str = Field(description="Recommended immediate action for broker")


SAMPLE_LEADS = [
    {"id": "L01", "source": "Meta Ads Dubai", "msg": "Looking for 2BR off-plan in Dubai Marina, budget 2.8M AED, ready to book viewing this week."},
    {"id": "L02", "source": "Property Finder", "msg": "Just checking prices for villas in Arabian Ranches, maybe next year."},
    {"id": "L03", "source": "Sydney Portal", "msg": "Pre-approved for $1.6M AUD, looking for a 3BR townhouse in Parramatta ASAP."},
    {"id": "L04", "source": "WhatsApp Inbound", "msg": "Hi send brochure please"},
    {"id": "L05", "source": "Meta Ads Dubai", "msg": "Cash buyer looking for 1BR investment apartment in Business Bay around 1.5M AED."},
    {"id": "L06", "source": "Melbourne Ads", "msg": "Want to sell my current apartment first before buying in Southbank."},
    {"id": "L07", "source": "Bayut Lead", "msg": "Need a 4BR villa in Dubai Hills, moving with family next month, budget 6.5M AED."},
    {"id": "L08", "source": "Instagram DM", "msg": "Do you have studio apartments under 500k AED in Downtown?"},
    {"id": "L09", "source": "Brisbane Portal", "msg": "Investor looking for high-yield duplex around $1.2M AUD, can jump on a call tomorrow."},
    {"id": "L10", "source": "Website Form", "msg": "Looking for rental options only, 60k AED yearly."},
]

SYSTEM_PROMPT = (
    "You are an elite real estate lead qualification engine for UAE and Australian brokerages. "
    "Return ONLY valid JSON matching keys: category (HOT|WARM|COLD), budget_tier, urgency, next_action. "
    "HOT: clear high budget + immediate/1-3 month intent; WARM: valid budget/intent with longer timeline; "
    "COLD: unrealistic budget, rental-only for sales, or vague inquiry."
)


async def qualify_single_lead(lead: dict, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        start = time.perf_counter()
        response = await client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Source: {lead['source']} | Message: {lead['msg']}"},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        elapsed = time.perf_counter() - start
        raw_content = response.choices[0].message.content
        parsed = LeadScore.model_validate_json(raw_content)
        return {
            "id": lead["id"],
            "category": parsed.category,
            "budget": parsed.budget_tier,
            "latency_sec": round(elapsed, 2),
        }


async def run_sequential(leads: list[dict]) -> float:
    sem = asyncio.Semaphore(1)
    start = time.perf_counter()
    for lead in leads:
        await qualify_single_lead(lead, sem)
    return round(time.perf_counter() - start, 2)


async def run_concurrent(leads: list[dict], max_concurrency: int = 5) -> tuple[float, list[dict]]:
    sem = asyncio.Semaphore(max_concurrency)
    start = time.perf_counter()
    tasks = [qualify_single_lead(lead, sem) for lead in leads]
    results = await asyncio.gather(*tasks)
    total_time = round(time.perf_counter() - start, 2)
    return total_time, results


async def main():
    print(f"Benchmarking {len(SAMPLE_LEADS)} Real Estate Inbound Leads...\n")

    seq_time = await run_sequential(SAMPLE_LEADS)
    print(f"1. Sequential (1-by-1) Total Time : {seq_time}s")

    conc_time, results = await run_concurrent(SAMPLE_LEADS, max_concurrency=5)
    speedup = round(seq_time / conc_time, 2) if conc_time > 0 else 0
    print(f"2. Concurrent (Async x5) Total Time: {conc_time}s  ({speedup}x faster)\n")

    print("--- Qualified Output ---")
    for r in results:
        print(f"[{r['id']}] {r['category']:<4} | Budget: {r['budget']:<18} | Call Time: {r['latency_sec']}s")


if __name__ == "__main__":
    asyncio.run(main())
