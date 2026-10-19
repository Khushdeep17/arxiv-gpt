from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os

from app.models.schemas import SearchRequest, SearchResponse
from app.agent.research_agent import ResearchAgent

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):

    if len(request.query.strip()) < 3:
        raise HTTPException(400, "Query too short")

    payload, pdf = ResearchAgent.run(
        request.query,
        request.max_results,
        request.generate_pdf
    )

    return {
        **payload,
        "pdf_filename": pdf
    }


@router.get("/download_pdf")
def download_pdf(filename: str = Query(...)):

    safe = os.path.basename(filename)
    path = os.path.join("data", safe)

    if not os.path.exists(path):
        raise HTTPException(404, "PDF not found")

    return FileResponse(path, media_type="application/pdf", filename=safe)
