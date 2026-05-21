from pathlib import Path
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    All configurable values. Reads from .env automatically.
    Each field maps to an env variable by name (case-insensitive).
    """
    # Paths
    log_dir: Path = PROJECT_ROOT / "logs"
    data_dir: Path = PROJECT_ROOT / "data"
    vector_store_dir: Path = PROJECT_ROOT / "vector_store"

    # Scraper
    scraper_base_url: str = "https://www.intrepidtravel.com"
    scraper_user_agent: str = "RAGTravelBot/1.0"
    scraper_delay_seconds: int = 3

    # LLM
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2:3b"

    # Embeddings
    embedding_model: str = "BAAI/bge-m3"

    # ChromaDB
    chroma_collection: str = "tourism_data"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"
    
    @property
    def processed_data_dir(self) -> Path:
        return self.data_dir / "processed"

    class Config:
        env_file = PROJECT_ROOT / ".env"
        env_file_encoding = "utf-8"

# Singleton instance - import this everywhere
settings = Settings()