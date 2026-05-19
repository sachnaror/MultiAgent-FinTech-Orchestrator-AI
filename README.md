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
2. What is the source of truth for vendor validation: internal DB, ERP API, Azure SQL, or a CSV upload?
3. What duplicate invoice rules matter: same vendor plus invoice ID, same total/date, or fuzzy matching?
4. What auto-approval threshold should be used for total amount and confidence score?
5. What should count as a minor issue versus a hard rejection?
6. Where should human-review tasks be created: email, Teams, ServiceNow, Jira, or an internal queue?
7. Which Azure services are approved: Azure Document Intelligence, Azure OpenAI, Azure SQL, Storage, Service Bus, App Insights?
8. What audit retention and compliance requirements apply to invoices and decisions?
9. Should the workflow fail fast on incomplete state, or route safely to human review?
10. Which downstream finance system receives approved invoices: ERP, AP system, payment rail, or data warehouse?

## Default Answers Used in This Build

- PDF parsing uses a local text parser for demo mode, with Azure Document Intelligence configuration ready for production.
- Vendor validation uses an in-memory repository seeded from `sample_data/vendors.json`.
- Duplicate detection uses `vendor + invoice_id`.
- Approval requires no validation issues, extraction confidence above threshold, and amount under threshold.
- Missing or corrupted state stops the workflow before the next agent.
- Human review is represented as a decision result and audit event.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`.

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

