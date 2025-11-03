import os
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette import status as http_status
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI(title="SecDev Course App", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["content-type", "x-correlation-id"],
)


CORRELATION_ID_HEADER = "x-correlation-id"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response


app.add_middleware(CorrelationIdMiddleware)


class ApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status: int = 400,
        errors: Optional[Dict[str, str]] = None,
    ):
        self.code = code
        self.message = message
        self.status = status
        self.errors = errors or {}


def problem_response(
    request: Request,
    *,
    code: str,
    title: str,
    status_code: int,
    detail: str = "",
    errors: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    body = {
        "type": f"about:blank#{code}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "correlation_id": correlation_id,
    }
    if errors:
        body["errors"] = errors
    return JSONResponse(status_code=status_code, content=body)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return problem_response(
        request,
        code=exc.code,
        title=(
            "Request validation error"
            if exc.status == 422
            else exc.code.replace("_", " ")
        ),
        status_code=exc.status,
        detail=exc.message,
        errors=exc.errors,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "http error"
    return problem_response(
        request,
        code="http_error",
        title="HTTP error",
        status_code=exc.status_code,
        detail=detail,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


_DB = {"items": []}


@app.post("/items")
def create_item(name: str):
    if not name or len(name) > 100:
        raise ApiError(
            code="validation_error", message="name must be 1..100 chars", status=422
        )
    item = {"id": len(_DB["items"]) + 1, "name": name}
    _DB["items"].append(item)
    return item


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


SAFE_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(SAFE_UPLOAD_DIR, exist_ok=True)

MAGIC_BYTES = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xFF\xD8\xFF",
    "application/pdf": b"%PDF",
}

MAX_UPLOAD_SIZE_BYTES = 1 * 1024 * 1024


def detect_magic_ok(header: bytes, content_type: str) -> bool:
    expected = MAGIC_BYTES.get(content_type)
    if not expected:
        return False
    return header.startswith(expected)


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if file.content_type not in MAGIC_BYTES:
        raise ApiError(
            code="unsupported_media_type",
            message="unsupported content type",
            status=http_status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    received = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(received) == 0:
        raise ApiError(code="validation_error", message="empty file", status=422)
    if len(received) > MAX_UPLOAD_SIZE_BYTES:
        raise ApiError(
            code="payload_too_large",
            message="file too large",
            status=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    header = received[:8]
    if not detect_magic_ok(header, file.content_type):
        raise ApiError(
            code="invalid_signature", message="file signature mismatch", status=422
        )

    new_name = f"{uuid.uuid4()}.bin"
    dest_path = os.path.join(SAFE_UPLOAD_DIR, new_name)

    os.makedirs(SAFE_UPLOAD_DIR, exist_ok=True)
    real_base = os.path.realpath(SAFE_UPLOAD_DIR)
    real_dest = os.path.realpath(dest_path)
    if not real_dest.startswith(real_base + os.sep):
        raise ApiError(code="path_traversal", message="invalid path", status=422)

    if os.path.islink(real_dest):
        raise ApiError(code="path_traversal", message="invalid path", status=422)

    with open(real_dest, "wb") as f:
        f.write(received)

    return {
        "filename": new_name,
        "size": len(received),
        "content_type": file.content_type,
    }
