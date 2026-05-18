"""
Searches ChromaDB for relevant chunks based on user query.
"""
import chromadb
from chromadb.utils import embedding_functions
from app.config.settings import settings
from app.config.constants import ChunkType, DEFAULT_TOP_K

class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=str(settings.vector_store_dir)
        )

        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name= settings.embedding_model,
            trust_remote_code=True
        )

        self.collection = self.client.get_collection(
            name=settings.chroma_collection,
            embedding_function=ef
        )
    

    """
    Search for relevant chunks.

    Args:
        - query: user's question
        - top_k: number of results to return
        - chunk_type: filter by chunk type (overview, Itinerary, practical)
        - destination: filter by destination country
        - max_price: filter tours under this price
        - style: filter by tour style (Basix, Original, ..)
    
    Returns: List of dicts with 'content', 'metadata', and 'distance' keys
    """
    def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        chunk_type: ChunkType | None = None,
        destination: str | None = None,
        max_price: int | None = None,
        style: str | None = None,
        tour_name: str | None = None,
    ) -> list[dict]:
        
        #Build metadata filter
        where = self._build_filter(chunk_type, destination, max_price, style, tour_name)

        # Query ChromaDB
        query_params ={
            "query_texts": [query],
            "n_results": top_k,
        }

        if where:
            query_params["where"] = where
        
        results = self.collection.query(**query_params)

        # Format results into a clean list
        formatted = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            formatted.append({
                "content": doc,
                "metadata": meta,
                "distance": dist
            })

        return formatted
    
    """
    Build ChromaDB where filter from optional parameters.
    """
    def _build_filter(
        self,
        chunk_type: ChunkType | None,
        destination: str | None,
        max_price: int | None,
        style: str | None,
        tour_name: str | None,
    ) -> dict | None:
        
        conditions = []

        if chunk_type:
            conditions.append({"type": chunk_type.value})
        if destination:
            conditions.append({"destination": destination.lower()})
        if max_price:
            conditions.append({"price_usd": {"$lte": max_price}})
        if style:
            conditions.append({"style": style})
        if tour_name:
            conditions.append({"tour_name": tour_name})
        
        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}
        
