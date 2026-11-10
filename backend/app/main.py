from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.api.auth import router as auth_router
from app.core.logging import setup_logging
from app.core.config import settings

setup_logging()

app = FastAPI(
    title="arXiv-GPT",
    description="Production Research Assistant API",
    version="2.0"
)

# Explicit CORS allowlist based on settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# ✅ API FIRST
app.include_router(auth_router)
app.include_router(router)

# ✅ Serve React static files
app.mount(
    "/static",
    StaticFiles(directory="app/static/static"),
    name="static"
)

# ✅ Root
@app.get("/")
def serve_react():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


# React Router refresh fix
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    return FileResponse("app/static/index.html")
