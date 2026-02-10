from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="arXiv-GPT",
    description="Production Research Assistant API",
    version="2.0"
)

# CORS (safe to keep *)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API FIRST
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


# ⭐ VERY IMPORTANT
# React Router refresh fix
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
