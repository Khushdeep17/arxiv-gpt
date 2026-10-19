from pydantic import BaseModel
from typing import List, Dict, Optional


class Summary(BaseModel):
    tldr: str
    key_contributions: List[str]
    methods: List[str]
    results: List[str]
    why_it_matters: str
    citation: str


class Paper(BaseModel):
    title: str
    authors: List[str]
    published: str
    category: str
    url: str
    summary: Summary


class SearchRequest(BaseModel):
    query: str
    max_results: int = 3
    sort_by: str = "recent"
    generate_pdf: bool = False


class SearchResponse(BaseModel):
    papers: List[Paper]
    query: str
    pdf_filename: Optional[str]
