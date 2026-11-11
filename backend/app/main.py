from contextlib import asynccontextmanager
import logging
from pathlib import Path
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine

setup_logging()
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_ASSETS_DIR = STATIC_DIR / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"

# Prevent caching of index.html so browsers always receive the latest SPA updates
HTML_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and clean resource teardown."""
    logger.info("arXiv-GPT API starting up (environment=%s)", "render" if settings.RENDER else "local")
    yield
    logger.info("arXiv-GPT API shutting down; disposing database engine pool")
    engine.dispose()


app = FastAPI(
    title="arXiv-GPT",
    description="Production AI Research Assistant API",
    version="2.0",
    lifespan=lifespan,
)

# Explicit CORS allowlist based on settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_request_observability(request: Request, call_next):
    """Attach a unique request ID and execution latency header to every response."""
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled server exceptions cleanly without leaking internal traces."""
    logger.exception("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred."},
    )


# API routers registered before static/SPA catch-all
app.include_router(auth_router)
app.include_router(router)


# Mount compiled React static assets when present (Docker production or local build)
if STATIC_ASSETS_DIR.is_dir():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_ASSETS_DIR)),
        name="static",
    )


def _serve_index_or_api_status():
    if INDEX_HTML_PATH.is_file():
        return FileResponse(str(INDEX_HTML_PATH), headers=HTML_CACHE_HEADERS)
    return JSONResponse(
        {
            "service": "arXiv-GPT API",
            "status": "running",
            "docs": "/docs",
            "note": "Frontend bundle not built into app/static; run React dev server or Docker build.",
        }
    )


@app.api_route("/", methods=["GET", "HEAD"])
def serve_react():
    return _serve_index_or_api_status()


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.get("/{full_path:path}")
def catch_all(full_path: str):
    """Serve root static files safely and fall back to index.html for React Router paths."""
    if STATIC_DIR.is_dir():
        static_root = STATIC_DIR.resolve()
        candidate = (static_root / full_path).resolve()
        if candidate.is_relative_to(static_root) and candidate.is_file():
            return FileResponse(str(candidate))
    return _serve_index_or_api_status()
