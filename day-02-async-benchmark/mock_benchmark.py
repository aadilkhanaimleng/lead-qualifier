import asyncio
import random
import time
from typing import Literal
from pydantic import BaseModel, Field


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


async def qualify_single_lead(lead: dict, semaphore: asyncio.Semaphore) -> dict:
    async with semaphore:
        start = time.perf_counter()
        # Har call ka realistic network latency (0.8s se 1.5s) simulate kar rahe hain
        simulated_latency = random.uniform(0.8, 1.5)
        await asyncio.sleep(simulated_latency)

        # Sample structured response ko Pydantic schema se validate kar rahe hain
        parsed = LeadScore(
            category="HOT" if int(lead["id"][1:]) in (1, 3, 7, 9) else "WARM",
            budget_tier="AED / AUD Lead",
            urgency="Immediate",
            next_action="Assign senior broker",
        )
        elapsed = time.perf_counter() - start
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
    print(f"Benchmarking {len(SAMPLE_LEADS)} Real Estate Inbound Leads (Local Async Sim)...\n")

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
