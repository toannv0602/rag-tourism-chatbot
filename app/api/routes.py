"""
FastAPI route definitions.
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse, SourceInfo
from app.rag.chain import RAGChain
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize once, reuse for all requests
rag_chain = RAGChain()



"""
Main chat endpoint - send a message, get a RAG powered response.
"""
@router.post("/chat", response_model= ChatResponse)
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = rag_chain.ask(
        question=request.message,
    )

    logging_answer(request, result)

    return ChatResponse(
        answer=result["answer"]
    )

@router.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}

def logging_answer(request: ChatRequest, result: dict):
    ## Logging response
    logger.info(f"[API][/CHAT] question: {request.message}")
    logger.info(f"[API][/CHAT] Intent of question: {result.get('intent')}")
    logger.info(f"[API][/CHAT] question: {result.get('detected_tour')}")
    for s in result["sources"]:
        logger.info(f"  Source: {s['tour_name']} ({s['type']}) [distance: {s['distance']:.4f}]")
