from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

app = FastAPI(title="UrbanFlow API", version="0.1.0")


class Health(BaseModel):
    status: str = "ok"
    service: str = "urbanflow-api"


class DatasetStatus(BaseModel):
    status: str = "not_published"
    run_id: str | None = None
    message: str = (
        "No analytical dataset has been published. Ingest and validate source data first."
    )


@app.exception_handler(HTTPException)
async def handle_http_error(request: Request, error: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {"code": "http_error", "message": str(error.detail)},
        },
        headers=error.headers,
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {"code": "validation_error", "message": "Invalid request parameters"},
        },
    )


@app.get("/health", response_model=Health)
def health() -> Health:
    """Process liveness, independent of database readiness."""
    return Health()


@app.get("/api/v1/datasets/status", response_model=DatasetStatus)
def dataset_status() -> DatasetStatus:
    """Foundation status; MongoDB publication integration follows ingestion."""
    return DatasetStatus()
