from app.config.settings import settings
import chromadb
from chromadb.utils import embedding_functions

"""
    Extracts tour name from user query by matching against
    known tour names in the database.
"""

class QueryParser:
    """
    Extracts tour name from user query by matching against
    known tour names in the database.
    """

    def __init__(self):
        client = chromadb.PersistentClient(path=str(settings.vector_store_dir))
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.embedding_model,
            trust_remote_code=True
        )
        collection = client.get_collection(
            name=settings.chroma_collection,
            embedding_function=ef
        )

        # Get all unique tour names from metadata
        all_data = collection.get(include=["metadatas"])
        self.tour_names = list(set(
            m["tour_name"] for m in all_data["metadatas"]
            if m.get("tour_name")
        ))
    
    """
        Check if the query mentions a known tour name.
        Simple string matching - fast and accurate.
    """
    def extract_tour_name(self, query: str) -> str | None:
        query_lower = query.lower()
        best_match = None
        best_length = 0
        for name in self.tour_names:
            if name.lower() in query_lower:
                # Pick the longest match to avoid partial matches
                # "Vietnam Express Southbound" beats "Vietnam Express"
                if len(name) > best_length:
                    best_match = name
                    best_length = len(name)
        return best_match