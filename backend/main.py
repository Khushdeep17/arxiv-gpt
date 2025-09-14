import sys
import os
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agent import run_agent

# Add src/ to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Logging configuration
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/backend.log"),
        logging.StreamHandler()
    ]
)

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# FastAPI app
app = FastAPI(
    title="arXiv-GPT Backend",
    description="API for fetching and summarizing arXiv papers",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class SearchRequest(BaseModel):
    query: str
    max_results: int = 3
    generate_pdf: bool = True

# Search endpoint
@app.post("/search")
async def search_papers(request: SearchRequest):
    try:
        if len(request.query.strip()) < 3:
            raise HTTPException(status_code=400, detail="Query must be at least 3 characters.")
        if request.max_results < 1 or request.max_results > 10:
            raise HTTPException(status_code=400, detail="max_results must be between 1 and 10.")

        logging.info(f"Search request: query={request.query}, max_results={request.max_results}, generate_pdf={request.generate_pdf}")
        result, pdf_filename = run_agent(request.query, request.max_results, request.generate_pdf)

        if isinstance(result, str) and ("No papers found" in result or "Unable to process" in result):
            return {"result": result, "pdf_filename": None}

        return {"result": result, "pdf_filename": pdf_filename}
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# Download PDF endpoint
@app.get("/download_pdf")
async def download_pdf(filename: str = Query(..., description="PDF filename to download")):
    """
    Download a generated PDF report.
    """
    # Sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename.strip().replace("\\", "/"))
    file_path = os.path.join("data", safe_filename)

    if not os.path.isfile(file_path):
        logging.error(f"PDF not found: {file_path}")
        raise HTTPException(status_code=404, detail="PDF not found")

    logging.info(f"Serving PDF: {file_path}")
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_filename
    )

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
