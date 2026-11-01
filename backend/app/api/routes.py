import os
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.models.schemas import SearchRequest, SearchResponse
from app.models.db_models import User
from app.agent.research_agent import ResearchAgent
from app.db.session import get_db
from app.services.persistence_service import PersistenceService
from app.api.deps import get_current_user, get_optional_current_user

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(
    request: SearchRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):

    if len(request.query.strip()) < 3:
        raise HTTPException(400, "Query too short")

    user_id = current_user.id if current_user else None

    payload, pdf = ResearchAgent.run(
        request.query,
        request.max_results,
        request.generate_pdf,
        db=db,
        user_id=user_id,
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


@router.get("/history")
def get_history(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns recent searches scoped to the authenticated user.
    Client-supplied user_id is removed to eliminate IDOR vulnerabilities.
    """
    return PersistenceService.get_recent_searches(db, user_id=current_user.id, limit=limit)
