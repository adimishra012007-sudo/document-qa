from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str
    document_id: str
    session_id: Optional[str] = None

class SourceReference(BaseModel):
    page: Any
    content: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceReference]
    session_id: Optional[str] = None

class ProcessResponse(BaseModel):
    document_id: str
    message: str
    status: str

# Auth Schemas
class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

# Background Task Schemas
class JobStatus(BaseModel):
    job_id: str
    document_id: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: Any
    updated_at: Any
