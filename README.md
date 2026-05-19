# Multi-Agent FinTech Orchestrator AI

A stateful invoice approval workflow that demonstrates three finance agents with explicit trust boundaries:

```text
PDF invoice
  -> Agent A: Extractor
  -> Agent B: Validator and independent verifier
  -> Agent C: Decision agent
  -> Approved | Human review | Rejected | Stopped
```

The important design choice: downstream agents treat upstream output as a hypothesis, not a fact. Agent B re-checks source evidence and business rules before Agent C can make a decision.

## Top 10 Confirmation Questions

1. Which invoice PDF formats must be supported first: native text PDFs, scanned images, or both?

   Answer: This application currently supports native text PDFs through the local PDF text parser. Scanned PDFs are not processed locally yet; Azure Document Intelligence is configured as the intended OCR/document extraction service through environment variables.

2. What is the source of truth for vendor validation: internal DB, ERP API, Azure SQL, or a CSV upload?

   Answer: This application currently validates vendors against the in-memory vendor repository loaded from `sample_data/vendors.json`.

3. What duplicate invoice rules matter: same vendor plus invoice ID, same total/date, or fuzzy matching?
   Answer: This application currently detects duplicates by matching the same `vendor + invoice_id`.

4. What auto-approval threshold should be used for total amount and confidence score?
   Answer: This application currently auto-approves only when the invoice amount is at or below `AUTO_APPROVE_MAX_AMOUNT`, extraction confidence is at or above `MIN_EXTRACTION_CONFIDENCE`, and Agent B reports no validation issues.

5. What should count as a minor issue versus a hard rejection?
   Answer: This application currently sends major issues, such as low confidence or unclear source grounding, to human review. It rejects critical issues, such as an unknown vendor, duplicate invoice, missing source grounding for key fields, or total mismatch.

6. Where should human-review tasks be created: email, Teams, ServiceNow, Jira, or an internal queue?
   Answer: This application currently represents human review as a workflow decision and audit event in the API/UI response. It does not create external tickets or messages yet.

7. Which Azure services are approved: Azure Document Intelligence, Azure OpenAI, Azure SQL, Storage, Service Bus, App Insights?
   Answer: This application currently includes configuration fields for Azure Document Intelligence and Azure OpenAI in `.env.example`. The running demo uses local parsing and rule-based validation, so no live Azure service call is required.

8. What audit retention and compliance requirements apply to invoices and decisions?
   Answer: This application currently keeps audit events in the workflow response, including each agent name, status, message, extracted data, validation issues, and decision reason. It does not persist audit records to a database yet.

9. Should the workflow fail fast on incomplete state, or route safely to human review?
   Answer: This application currently fails fast on incomplete or corrupted state before the next agent runs. Complete but uncertain data is routed to human review.

10. Which downstream finance system receives approved invoices: ERP, AP system, payment rail, or data warehouse?
    Answer: This application currently returns the approval decision through the API/UI response. It does not send approved invoices to an ERP, AP system, payment rail, or data warehouse yet.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`.

## Observability

After processing an invoice, open `http://127.0.0.1:8000/observability` to see all recorded workflow runs.

The observability page shows:

- Stateful checkpoints for every agent run
- Validation issues, if any
- Final workflow status and decision
- Vendor, invoice ID, total amount, and decision reason

The same data is available through:

```bash
curl http://127.0.0.1:8000/api/observability/runs
curl http://127.0.0.1:8000/api/observability/runs/{workflow_id}
```

## Try The API

```bash
curl -X POST http://127.0.0.1:8000/api/process-text \
  -H "Content-Type: application/json" \
  -d @sample_data/sample_invoice.json
```

## Azure Configuration

Copy `.env.example` to `.env` and set the Azure values you want to use:

```bash
cp .env.example .env
```

The application works without live Azure credentials in local demo mode.

## Test

```bash
python3 -m unittest discover -s tests
```
