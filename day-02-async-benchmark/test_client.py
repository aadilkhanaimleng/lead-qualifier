import asyncio
import httpx

PAYLOAD = {
    "max_concurrency": 5,
    "max_retries": 2,
    "leads": [
        {"id": "L01", "source": "Meta Ads Dubai", "msg": "2BR off-plan Dubai Marina, 2.8M AED, ready to book viewing this week."},
        {"id": "L02", "source": "Property Finder", "msg": "Checking villa prices in Arabian Ranches for next year."},
        {"id": "L03", "source": "Sydney Portal", "msg": "Pre-approved $1.6M AUD, 3BR townhouse in Parramatta ASAP."},
        {"id": "L04", "source": "Website Form", "msg": "Rental options only, 60k AED yearly."},
    ],
}


async def main():
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post("http://127.0.0.1:8000/qualify-batch", json=PAYLOAD)
        resp.raise_for_status()
        data = resp.json()
        print(f"Processed {data['total_leads']} leads in {data['total_time_sec']}s")
        for item in data["results"]:
            print(f"[{item['id']}] -> {item['category']} | attempts={item['attempts']} | {item['latency_sec']}s")


if __name__ == "__main__":
    asyncio.run(main())
