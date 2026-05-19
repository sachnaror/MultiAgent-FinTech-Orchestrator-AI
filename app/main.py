from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import get_settings
from app.core.models import ObservabilityResponse, ObservabilityRun, ProcessResponse, TextInvoiceRequest
from app.orchestrator import InvoiceWorkflow
from app.services.observability import observability_store
from app.services.pdf_reader import read_pdf_text


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
root = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=root / "static"), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(root / "templates" / "index.html")


@app.get("/observability")
def observability() -> FileResponse:
    return FileResponse(root / "templates" / "observability.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "azure_document_intelligence_configured": str(bool(settings.azure_document_intelligence_endpoint)),
        "azure_openai_configured": str(bool(settings.azure_openai_endpoint)),
    }


@app.post("/api/process-text", response_model=ProcessResponse)
def process_text(payload: TextInvoiceRequest) -> ProcessResponse:
    workflow = InvoiceWorkflow(settings)
    state = workflow.process(payload.text)
    observability_store.record(state)
    return ProcessResponse(**state.model_dump())


@app.post("/api/process-pdf", response_model=ProcessResponse)
async def process_pdf(file: UploadFile = File(...)) -> ProcessResponse:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Upload a PDF file.")
    content = await file.read()
    text = read_pdf_text(content)
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted. Configure Azure Document Intelligence for scanned PDFs.",
        )
    workflow = InvoiceWorkflow(settings)
    state = workflow.process(text)
    observability_store.record(state)
    return ProcessResponse(**state.model_dump())


@app.get("/api/observability/runs", response_model=ObservabilityResponse)
def list_observability_runs() -> ObservabilityResponse:
    return observability_store.list_runs()


@app.get("/api/observability/runs/{workflow_id}", response_model=ObservabilityRun)
def get_observability_run(workflow_id: str) -> ObservabilityRun:
    run = observability_store.get_run(workflow_id)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found.")
    return run
