from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

from app.core.config import settings
from app.routers.analytics import router

app = FastAPI(title="UrbanFlow API", version="1.0.0")
app.include_router(router)


class Health(BaseModel):
    status: str = "ok"
    service: str = "urbanflow-api"


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


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    if path.startswith("api/"):
        raise HTTPException(404, "Unknown API endpoint")
    root = Path(settings.web_dir).resolve()
    candidate = (root / path).resolve()
    if not candidate.is_relative_to(root):
        raise HTTPException(404, "Not found")
    if candidate.is_file():
        return FileResponse(candidate)
    index = root / "index.html"
    if index.is_file() and "." not in Path(path).name:
        return FileResponse(index)
    raise HTTPException(404, "Not found")
