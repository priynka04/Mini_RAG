from pydantic import BaseModel
from typing import List, Optional


class DocumentUploadResponse(BaseModel):
    id: str
    status: str


class ChatRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
