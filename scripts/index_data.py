"""
Embeds processed chunks and stores them in ChromaDB.
Reads from data/processed/chunks.json
Writes to vector_store/
"""

import json
import time
import chromadb
from chromadb.utils import embedding_functions
from app.config.settings import settings
from app.config.constants import ChunkType

"""Load processed chunks from JSON."""
def load_chunks() -> list[dict]:
    chunks_path = settings.processed_data_dir / "chunks.json"

    if not chunks_path.exists():
        raise FileNotFoundError(
            f"{chunks_path} not found. Run process_data.py first."
        )
    
    with open(chunks_path, "r", encoding="utf-8") as f:
        return json.load(f)

"""
Create (or recreate) a ChromaDB collection with BGE-M3 embeddings.

The embedding function tells ChromaDB which model to use for converting to text vectors.
ChromaDB calls the model automatically - you just pass text in, vector come out.
"""
def create_collection(client: chromadb.PersistentClient) -> chromadb.Collection:
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name = settings.embedding_model,  # "BAAI/bge-m3"
        trust_remote_code=True
    )

    existing = [c.name for c in client.list_collections()]
    if settings.chroma_collection in existing:
        client.delete_collection(settings.chroma_collection)
        print(f"Deleted existing collection '{settings.chroma_collection}'")

    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function = ef,
        metadata={"hnsw:space": "cosine"} # Use cosine similarity
    )
    
    return collection


"""
    Add all chunks to ChromaDB.
    ChromaDB has a batch limit, so we add in batches of 100.
    For each chunk, we provide:
    - id: unique identifier
    - document: the text content (ChromaDB embeds this automatically)
    - metadata: structured fields for filtering
"""
def index_chunks(collection: chromadb.Collection, chunks: list[dict]):
    BATCH_SIZE =100
    total = len(chunks)

    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        batch = chunks[start: end]
        
        ids = [chunk["id"] for chunk in batch]
        documents = [chunk["content"] for chunk in batch]
        metadatas = [chunk["metadata"] for chunk in batch]

        collection.add(
            ids = ids,
            documents = documents,
            metadatas=metadatas
        )

        print(f"    Indexed {end}/{total} chunks")

"""
Run a quick test to verify the index works
"""
def verify_index(collection: chromadb.Collection):
    print("\n======= Verification =======")
    print(f"Total chunks in collection: {collection.count()}")

    # Test query
    results = collection.query(
        query_texts=["What tours do you have in Vietnam"],
        n_results = 3,
        where={"type": ChunkType.TOUR_OVERVIEW.value}
    )

    print("========= Results =========")
    print(results)

    print(f"\nTest query: 'What tours do you have in Vietnam?'")
    print(f"Top 3 results:")
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        print(f"\n  [{i+1}] {meta['tour_name']}")
        print(f"    Distance: {dist:.4f}")
        print(f"    Content: {doc[:100]}...")

"""
main function
"""
def main():
    print("=" * 50)
    print("Indexing chunks into ChromaDB")
    print("=" * 50)

    # load chunks
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks")

    # Initialize ChromaDB with persistent storage
    settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(
        path=str(settings.vector_store_dir)
    )

    # Create collection with embedding function
    print(f"\nLoading embedding model: {settings.embedding_model}")
    start_time = time.time()

    collection = create_collection(client=client)

    load_time = time.time() - start_time
    print(f"Model loaded in {load_time:.1f}s")

    # Index all chunks
    print(f"\n Indexing {len(chunks)} chunks...")
    start_time = time.time()

    index_chunks(collection, chunks)

    index_time = time.time() - start_time

    print(f"Indexing completed in {index_time:.1f}s")

    # Verify
    verify_index(collection)

    print("\nDone! Vector store saved to:", settings.vector_store_dir)

if __name__== "__main__":
    main()