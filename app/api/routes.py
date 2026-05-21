"""
FastAPI route definitions.
"""

import asyncio
import threading
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from app.models.schemas import ChatRequest, ChatResponse, SourceInfo
from app.rag.chain import RAGChain
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize once, reuse for all requests
rag_chain = RAGChain()


"""
Main chat endpoint - send a message, get a RAG powered response.
"""
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = rag_chain.ask(question=request.message)
    logging_answer(request, result)
    return ChatResponse(answer=result["answer"])


"""WebSocket endpoint - streams response token by token."""
@router.websocket("/ws/chat")
async def chat_stream(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            question = json.loads(data).get("message", "")
            if not question.strip():
                await websocket.send_text(json.dumps({"type": "error", "content": "Empty message"}))
                continue

            logger.info(f"[WS] Question: {question}")

            loop = asyncio.get_event_loop()
            #Create a queue for thread-safe communication
            queue: asyncio.Queue = asyncio.Queue()

            # Run the blocking Ollama stream in a thread so the event loop
            # stays free for WebSocket keep-alive pings.
            def run_stream():
                try:
                    for token in rag_chain.ask_stream(question):
                        # logger.info(f"[WS] token: {token}")
                        loop.call_soon_threadsafe(queue.put_nowait, ("token", token))
                except Exception as e:
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", str(e)))
                finally:
                    loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

            threading.Thread(target=run_stream, daemon=True).start()

            token_count = 0
            while True:
                event_type, content = await queue.get()
                if event_type == "token":
                    token_count += 1
                    await websocket.send_text(json.dumps({"type": "token", "content": content}))
                elif event_type == "error":
                    logger.error(f"[WS] Stream error: {content}")
                    await websocket.send_text(json.dumps({"type": "error", "content": content}))
                    break
                elif event_type == "done":
                    # Collect sources with URLs from the last query
                    sources = []
                    for chunk in rag_chain.last_sources:
                        url = chunk["metadata"].get("source_url", "")
                        name = chunk["metadata"].get("tour_name", "")
                        if url and name and {"name": name, "url": url} not in sources:
                            sources.append({"name": name, "url": url})

                    await websocket.send_text(
                        json.dumps({
                            "type": "done",
                            "sources": sources
                        })
                    )
                    logger.info(f"[WS] Done — {token_count} tokens sent")
                    break

    except WebSocketDisconnect:
        logger.info("[WS] Client disconnected")
    except Exception as e:
        logger.error(f"[ERROR] [WS]: {e}")

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
