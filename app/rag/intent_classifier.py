from sentence_transformers import SentenceTransformer
import numpy as np
from app.config.settings import settings

"""
    Language-agnostic intent classification using embeddings.
    No LLM call needed - uses the same embedding model you already have.
"""
class IntentClassifier:
    INTENT_EXAMPLES = {
        "itinerary": [
            "What happens on day 3?",
            "Show me the daily schedule",
            "What activities are on day 5?",
            "Tell me about the itinerary",
        ],
        "tour_info": [
            "What tours do you have?",
            "How much does this tour cost?",
            "How long is the tour?",
            "What's included in the price?",
        ],
        "comparison": [
            "Compare these two tours",
            "What's the difference between Original and Comfort?",
            "Which tour is cheaper?",
        ],
        "general": [
            "Do I need a visa?",
            "What's the weather like?",
            "How do I book?",
            "What's your cancellation policy?",
        ],
    }

    def __init__(self):
        self.model = SentenceTransformer(settings.embedding_model)
        self.intent_embeddings = {}

        # Embed all examples once at startup
        for intent, examples in self.INTENT_EXAMPLES.items():
            embeddings = self.model.encode(examples)
            # Average all examples into one vector per intent
            self.intent_embeddings[intent] = np.mean(embeddings, axis=0)

    """
        Classify a query into an intent.
        Works in any language because embeddings capture meaning, not words (hard code).
    """
    def classify(self, query: str):
        """
        Classify a query into an intent.
        Works in any language because embeddings capture meaning, not words.
        """
        query_embedding = self.model.encode(query)
        best_intent = "general"
        best_score = -1

        for intent, intent_embedding in self.intent_embeddings.items():
            score = np.dot(query_embedding, intent_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(intent_embedding)
            )
            if score > best_score:
                best_score = score
                best_intent = intent
        
        return best_intent
