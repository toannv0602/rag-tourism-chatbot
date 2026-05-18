"""
The RAG chain: retriever -> prompt builder  -> LLM -> response
"""

import requests
from app.config.settings import settings
from app.rag.retriever import Retriever
from app.rag.prompt_templates import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE
from app.config.constants import DEFAULT_TOP_K
from app.rag.intent_classifier import IntentClassifier
from app.config.constants import ChunkType
from app.rag.query_parser import QueryParser

class RAGChain:
    def __init__(self):
        self.retriever = Retriever()
        self.classifier = IntentClassifier()
        self.parser = QueryParser()
    
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks
    2. Build prompt with context
    3. Call LLM
    4. Return answer with sources
    """
    def ask(self,  question: str, top_k: int = DEFAULT_TOP_K) -> dict:
        # Step 1:  Classify intent using embeddings (any language, no LLM call)
        intent = self.classifier.classify(question)

        # Step 2: Extract tour name if mentioned
        tour_name = self.parser.extract_tour_name(question)

        # Step 2: Adjust retrieval based on intent
        chunk_type = None
        if intent == "itinerary":
            chunk_type = ChunkType.ITINERARY_DAY
            top_k = 10

        # Step 3: Retrieve
        chunks = self.retriever.search(
            query=question,
            top_k=top_k,
            chunk_type=chunk_type,
            tour_name=tour_name
        )

        # Step 4: Generate answer
        context = self._format_context(chunks)
        user_prompt = RAG_PROMPT_TEMPLATE.format(
            context=context,
            question=question
        )

        # Step 5: Call Ollama
        answer = self._call_ollama(user_prompt)

        # Step 6: Return answer with sources for transparency
        sources = [
            {
                "tour_name": c["metadata"].get("tour_name", ""),
                "type": c["metadata"].get("type", ""),
                "url": c["metadata"].get("source_url", ""),
                "distance": c["distance"]
            }
            for c in chunks
        ]

        return{
            "answer": answer,
            "sources": sources,
            "intent": intent
        }
    
    """Get the most likely tour name from retrieved chunks."""
    def _extract_tour_name(self, chunks: list[dict]) -> str | None:
    
        if chunks:
            return chunks[0]["metadata"].get("tour_name")
        return None
    
    """
    Combine retrieved chunks into a single context string.
    """
    def _format_context(self, chunk: list[dict]) -> str:
        context_parts = []
        for i, chunk in enumerate(chunk, 1):
            meta = chunk["metadata"]
            header = f"[Source {i}: {meta.get('tour_name', 'Unknown')} - {meta.get('type', '')}]"
            context_parts.append(f"{header}\n{chunk['content']}")

        return "\n\n".join(context_parts)
    
    """
    Call the local Ollama LLM.
    Ollama exposes a REST API at http://localhost:11434.
    We send the system prompt + user prompt and get back generated text.
    """
    def _call_ollama(self, user_prompt: str) -> str:
        try:
            response = requests.post(
                f"{settings.ollama_base_url}/api/chat",
                json={
                    "model": settings.llm_model,
                    "messages":[
                        {"role":"system", "content":SYSTEM_PROMPT},
                        {"role":"user", "content": user_prompt}
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.3, # Low = more factual, less creative
                        "num_ctx": 4096     # Context window size
                    }
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["message"]["content"]

        except requests.ConnectionError:
            return "[Error] Cannot connect to Ollama. Make sure it's running with: ollama serve"
        except requests.Timeout:
            return "[Error] LLM took too long to respond. Try a shorter question."
        except Exception as e:
            return f"[ERROR] [CALL_OLLAMA]: {str(e)}"
        

