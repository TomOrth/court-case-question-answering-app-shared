"""
Test embedding service.
"""

import asyncio
from app.services.embeddings import EmbeddingService, EMBEDDING_DIMENSIONS


async def main():
    print("Testing embedding service...")

    service = EmbeddingService()

    text = "The court granted a preliminary injunction."
    embedding = await service.embed_text(text)

    print(f"\n✅ Single embedding generated")
    print(f"    Dimensions: {len(embedding)} (expected {EMBEDDING_DIMENSIONS})")
    print(f"    First 5 values: {embedding[:5]}")

    texts = [
        "The plaintiff filed a motion for summary judgment.",
        "The defendant responded with an opposition brief.",
        "The court scheduled oral argument for next month.",
    ]
    embeddings = await service.embed_texts(texts)

    print(f"\n✅ Batch embeddings generated: {len(embeddings)}")

    # Test semantic similarity
    import numpy as np
    similar_texts = [
        "I know he did it but I just can't prove it",
        "I know that there's a special place where everyone can be queen",  
        "A line in Roan's lyrics",
    ]
    similar_embeddings = await service.embed_texts(similar_texts)

    # Cosine similarity
    def cosine_similarity(a, b):
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_1_2 = cosine_similarity(similar_embeddings[0], similar_embeddings[1])
    sim_1_3 = cosine_similarity(similar_embeddings[0], similar_embeddings[2])

    print(f"\n Semantic similarity test:")
    print(f"   '{similar_texts[0][:30]}...'")
    print(f"   vs '{similar_texts[1][:30]}...' = {sim_1_2:.3f}")
    print(f"   vs '{similar_texts[2][:30]}...' = {sim_1_3:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
