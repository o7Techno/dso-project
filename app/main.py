import os
import re
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, field_validator
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


@app.middleware("http")
async def add_cache_control_headers(request: Request, call_next):
    """Add no-cache headers to all responses to avoid cacheable content alerts."""
    response: Response = await call_next(request)
    response.headers.setdefault("Cache-Control", "no-store, no-cache, must-revalidate")
    response.headers.setdefault("Pragma", "no-cache")
    response.headers.setdefault("Expires", "0")
    return response


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


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
):
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors[field] = error["msg"]
    return problem_response(
        request,
        code="validation_error",
        title="Request validation error",
        status_code=422,
        detail="Input validation failed",
        errors=errors,
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors[field] = error["msg"]
    return problem_response(
        request,
        code="validation_error",
        title="Request validation error",
        status_code=422,
        detail="Input validation failed",
        errors=errors,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/robots.txt")
def robots():
    return Response(
        content="User-agent: *\nDisallow: /",
        media_type="text/plain",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/sitemap.xml")
def sitemap():
    xml = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>'
    return Response(
        content=xml,
        media_type="application/xml",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


_DB = {"items": [], "events": []}


class ItemCreate(BaseModel):
    model_config = dict(extra="forbid")
    name: str = Field(
        min_length=1, max_length=100, pattern="^[a-zA-Z0-9\\s\\-_.,!?()]+$"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        # Запрет опасных символов для предотвращения инъекций
        dangerous_patterns = [
            r"<script",
            r"javascript:",
            r"on\w+\s*=",  # onerror=, onclick=, etc.
            r"[\x00-\x08\x0b-\x0c\x0e-\x1f]",  # Control characters
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("name contains dangerous characters")
        # Проверка на попытки SQL инъекций (хотя БД нет, но защита на будущее)
        sql_keywords = ["union", "select", "insert", "delete", "drop", "exec", "--"]
        v_lower = v.lower()
        for keyword in sql_keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", v_lower):
                raise ValueError("name contains potentially dangerous SQL keywords")
        return v.strip()


class EventCreate(BaseModel):
    model_config = dict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    event_date: datetime
    location: str = Field(min_length=1, max_length=200)
    price: Optional[Decimal] = Field(
        default=None, gt=0, max_digits=12, decimal_places=2
    )

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, v: datetime) -> datetime:
        # NFR-4: Нельзя создать событие в прошлом
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if v.tzinfo:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        if v < now:
            raise ValueError("event_date cannot be in the past")
        return v


@app.post("/items")
def create_item(item: ItemCreate):
    item_dict = {"id": len(_DB["items"]) + 1, "name": item.name}
    _DB["items"].append(item_dict)
    return item_dict


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise ApiError(code="not_found", message="item not found", status=404)


@app.post("/events")
def create_event(event: EventCreate):
    # Проверка на дубликаты (NFR-5)
    for existing in _DB["events"]:
        if (
            existing["title"] == event.title
            and existing["event_date"] == event.event_date.isoformat()
            and existing["location"] == event.location
        ):
            raise ApiError(
                code="duplicate_event",
                message="Event with same title, date and location already exists",
                status=409,
            )

    event_dict = {
        "id": len(_DB["events"]) + 1,
        "title": event.title,
        "description": event.description,
        "event_date": event.event_date.isoformat(),
        "location": event.location,
        "price": str(event.price) if event.price else None,
    }
    _DB["events"].append(event_dict)
    return event_dict


@app.get("/events/{event_id}")
def get_event(event_id: int):
    for ev in _DB["events"]:
        if ev["id"] == event_id:
            return ev
    raise ApiError(code="not_found", message="event not found", status=404)


SAFE_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(SAFE_UPLOAD_DIR, exist_ok=True)

MAGIC_BYTES = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
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


# HTTP клиент с таймаутами и ретраями (ADR-003)
HTTP_TIMEOUT = httpx.Timeout(
    connect=float(os.getenv("HTTP_TIMEOUT_CONNECT", "1.0")),
    read=float(os.getenv("HTTP_TIMEOUT_READ", "4.0")),
    write=float(os.getenv("HTTP_TIMEOUT_WRITE", "4.0")),
    pool=float(os.getenv("HTTP_TIMEOUT_POOL", "5.0")),
)
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "2"))
HTTP_RETRY_BACKOFF_BASE = float(os.getenv("HTTP_RETRY_BACKOFF_BASE", "0.1"))


def safe_http_request(
    method: str,
    url: str,
    correlation_id: Optional[str] = None,
    **kwargs,
) -> httpx.Response:
    """
    Безопасный HTTP клиент с таймаутами и ретраями.
    Реализует ADR-003: таймауты, ретраи с backoff, корреляция.
    """
    headers = kwargs.get("headers", {})
    if correlation_id:
        headers["x-correlation-id"] = correlation_id
    kwargs["headers"] = headers
    kwargs["timeout"] = HTTP_TIMEOUT
    kwargs["follow_redirects"] = True

    last_exception = None
    for attempt in range(HTTP_MAX_RETRIES + 1):
        try:
            with httpx.Client() as client:
                response = client.request(method, url, **kwargs)
                response.raise_for_status()
                return response
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
            last_exception = e
            if attempt < HTTP_MAX_RETRIES:
                backoff_time = HTTP_RETRY_BACKOFF_BASE * (2**attempt)
                time.sleep(backoff_time)
            else:
                raise
        except httpx.HTTPStatusError as e:
            if 400 <= e.response.status_code < 500:
                raise
            last_exception = e
            if attempt < HTTP_MAX_RETRIES:
                backoff_time = HTTP_RETRY_BACKOFF_BASE * (2**attempt)
                time.sleep(backoff_time)
            else:
                raise

    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected error in safe_http_request")


@app.get("/external/health")
def check_external_health(request: Request):
    """
    Проверка здоровья внешнего сервиса с использованием безопасного HTTP клиента.
    Пример использования ADR-003.
    """
    correlation_id = getattr(request.state, "correlation_id", None)
    external_url = os.getenv("EXTERNAL_HEALTH_URL", "https://httpbin.org/status/200")
    try:
        response = safe_http_request("GET", external_url, correlation_id=correlation_id)
        return {
            "external_service": "ok",
            "status_code": response.status_code,
            "correlation_id": correlation_id,
        }
    except Exception as e:
        raise ApiError(
            code="external_service_unavailable",
            message=f"External service check failed: {str(e)}",
            status=503,
        )
