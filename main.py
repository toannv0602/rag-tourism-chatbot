"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config.settings import settings
from app.utils.logger import setup_logging

setup_logging()  # Call before creating the app

app = FastAPI(
    title="Tourism RAG Chatbot",
    description="AI-powered travel consultant using RAG with local LLM",
    version="0.1.0"
)

# CORS - allows frontend to call this api
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True  # Auto-reload on code changes during development
    )