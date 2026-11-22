import asyncio
import random
import time
from typing import Literal
import httpx
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Real Estate Lead Qualification Engine")


class InboundLead(BaseModel):
    id: str
    source: str
    msg: str


class BatchRequest(BaseModel):
    leads: list[InboundLead]
    max_concurrency: int = Field(default=5, ge=1, le=20)
    max_retries: int = Field(default=2, ge=0, le=5)
    webhook_url: str | None = Field(default=None, description="Optional CRM/n8n callback URL")


class QualifiedLead(BaseModel):
    id: str
    category: Literal["HOT", "WARM", "COLD"]
    budget_tier: str
    urgency: str
    next_action: str
    latency_sec: float
    attempts: int


class BatchResponse(BaseModel):
    total_leads: int
    total_time_sec: float
    webhook_delivered: bool | None
    results: list[QualifiedLead]


async def qualify_lead_with_retry(lead: InboundLead, sem: asyncio.Semaphore, max_retries: int) -> QualifiedLead:
    async with sem:
        start = time.perf_counter()
        last_err: Exception | None = None

        for attempt in range(1, max_retries + 2):
            try:
                # Simulated async I/O latency
                await asyncio.sleep(random.uniform(0.5, 1.1))

                # Simulated rare transient spike (~10%) on first attempt to test retry behavior
                if attempt == 1 and random.random() < 0.1:
                    raise TimeoutError("Simulated upstream transient timeout")

                text = lead.msg.lower()
                if any(k in text for k in ["2.8m", "$1.6m", "6.5m", "$1.2m", "cash buyer", "asap", "this week", "next month"]):
                    category = "HOT"
                elif any(k in text for k in ["rental", "brochure", "500k"]):
                    category = "COLD"
                else:
                    category = "WARM"

                return QualifiedLead(
                    id=lead.id,
                    category=category,
                    budget_tier="Extracted from lead",
                    urgency="Immediate" if category == "HOT" else "Follow-up",
                    next_action="Route to senior broker" if category == "HOT" else "Send automated nurture",
                    latency_sec=round(time.perf_counter() - start, 2),
                    attempts=attempt,
                )
            except Exception as exc:
                last_err = exc
                if attempt <= max_retries:
                    await asyncio.sleep(0.3 * attempt)

        raise RuntimeError(f"Failed lead {lead.id} after retries: {last_err}")


async def push_to_webhook(webhook_url: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            return 200 <= resp.status_code < 300
    except httpx.HTTPError:
        return False


@app.post("/qualify-batch", response_model=BatchResponse)
async def qualify_batch(payload: BatchRequest):
    start = time.perf_counter()
    sem = asyncio.Semaphore(payload.max_concurrency)
    tasks = [qualify_lead_with_retry(lead, sem, payload.max_retries) for lead in payload.leads]
    results = await asyncio.gather(*tasks)
    total_time = round(time.perf_counter() - start, 2)

    response_obj = BatchResponse(
        total_leads=len(results),
        total_time_sec=total_time,
        webhook_delivered=None,
        results=results,
    )

    if payload.webhook_url:
        response_obj.webhook_delivered = await push_to_webhook(payload.webhook_url, response_obj.model_dump())

    return response_obj
