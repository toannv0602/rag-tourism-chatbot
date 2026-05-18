"""
Quick test of the full RAG pipeline.
"""
from app.rag.chain import RAGChain

chain = RAGChain()

test_questions = [
    "What tours do you have in Vietnam?",
    "Nói cho tôi về lịch trình của tour Vietnam Express Southbound"
]

for q in test_questions:
    print(f"\n{'='*50}")
    print(f"Q: {q}")
    print(f"{'='*50}")
    
    result = chain.ask(q)
    
    print(f"\nA: {result['answer']}")
    print(f"\n=======Sources:")
    for s in result["sources"]:
        print(f"  - {s['tour_name']} ({s['type']}) [distance: {s['distance']:.4f}]")