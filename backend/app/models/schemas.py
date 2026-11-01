import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)


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


# ---------------------------------------------------------
# Authentication & User Management Schemas
# ---------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long.")
    full_name: Optional[str] = Field(default=None, max_length=255)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password cannot be empty or whitespace-only.")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, description="Plaintext password.")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    sub: Optional[str] = None
    user_id: Optional[uuid.UUID] = None

    @model_validator(mode="after")
    def sync_sub_and_user_id(self) -> "TokenData":
        if self.sub and not self.user_id:
            try:
                self.user_id = uuid.UUID(self.sub)
            except (ValueError, TypeError):
                pass
        elif self.user_id and not self.sub:
            self.sub = str(self.user_id)
        return self
