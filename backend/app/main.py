from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.logging import setup_logging

# initialize logging FIRST
setup_logging()

app = FastAPI(
    title="arXiv-GPT",
    description="Production Research Assistant API",
    version="2.0"
)

# CORS (tighten later for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routes
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}
