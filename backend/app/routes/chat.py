from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class Query(BaseModel):
    query: str


@router.post("/query")
async def query_chat(q: Query):
    # Replace with retrieval + LLM pipeline
    return {"answer": "This is a placeholder response.", "query": q.query}
