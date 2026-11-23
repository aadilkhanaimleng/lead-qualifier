# AI-Powered Lead Qualifier (`lead-qualifier`)

Automated lead qualification and routing pipeline built with **FastAPI**, **Gemini AI**, **n8n**, **Gmail**, and **Google Sheets**.

## Architecture & Flow

```text
Webhook (POST /webhook/quality%20lead)
  --> HTTP Request (POST [http://127.0.0.1:8000/qualify](http://127.0.0.1:8000/qualify))
        --> FastAPI + Gemini AI Qualification (lead_name, niche, is_high_ticket, priority, reason)
              --> If (is_high_ticket == true)
                    |-- True  --> Edit Fields --> Send an Email (Gmail Alert)
                    |-- Both True & False --> Edit Fields1 --> Append row in sheet (AI LEAD QUALIFIER CRM)
```

## Key Components

* **FastAPI `/qualify` Endpoint (`api.py`, `qualifier_core.py`, `hybrid_qualifier.py`)**: Validates incoming payload against `LeadInput` (`lead_name`, `niche`, `message`) and returns structured qualification fields (`is_high_ticket`, `priority`, `reason`).
* **n8n Workflow (`lead-qualifier-workflow.json`)**:
  * Maps incoming webhook fields into `LeadInput` (`lead_name`, `niche`, `message`) to avoid `422` validation errors.
  * Bypasses `Split Out` for single-object `/qualify` responses and routes leads via `If` on `is_high_ticket`.
  * Sends email alerts on high-ticket leads and logs leads directly from the `HTTP Request` output into **AI LEAD QUALIFIER CRM** (`TIMESTAMP`, `LEAD ID`, `CATEGORY`, `URGENCY`, `NEXT ACTION`, `RAW MESSAGE`).

## Sample Test Command

```bash
curl -X POST "http://localhost:5678/webhook/quality%20lead" \
  -H "Content-Type: application/json" \
  -d '{"max_concurrency":1,"max_retries":0,"leads":[{"id":"L01","source":"Meta Ads Dubai","msg":"2BR off-plan Dubai Marina, 2.8M AED, ready to book viewing this week."}]}'
```

## Progress Log

* **Day 02**: Async benchmarking (`day-02-async-benchmark`), n8n webhook routing (`HOT` vs `Nurture`) with Gmail alerts (`day-02-n8n-email-routing`), and automated Google Sheet CRM logging (`AI LEAD QUALIFIER CRM`).
