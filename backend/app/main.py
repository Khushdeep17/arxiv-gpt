from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.core.logging import setup_logging

# initialize logging FIRST
setup_logging()

app = FastAPI(
    title="arXiv-GPT",
    description="Production Research Assistant API",
    version="2.0"
)

# CORS (tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ API ROUTES FIRST
app.include_router(router)


# ✅ SERVE REACT BUILD
app.mount(
    "/static",
    StaticFiles(directory="app/static/static"),
    name="static"
)


# ✅ ROOT → React index.html
@app.get("/")
def serve_react():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
