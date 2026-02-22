# """
# Embedding Generation Service.

# Uses OpenAI's text-embedding-3-small model to create vector embeddings.

# Why text-embedding-3-small?
# - 1536 dimensions (good balance of quality and storage)
# - Cheaper than text-embedding-3-large
# - Better performance than ada-002
# - Optimized for semantic search
# """

# from typing import List
# from openai import AsyncOpenAI

# from app.core.config import get_settings

# EMBEDDING_MODEL = "text-embedding-3-small"
# EMBEDDING_DIMENSIONS = 1536


# class EmbeddingService:
#     """
#     Async service for generating embeddings.
    
#     Usage:
#         service = EmbeddingService()
#         vectors = await service.embed_texts(["Hello", "World"])
#     """

#     def __init__(self):
#         settings = get_settings()
#         self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

#     async def embed_text(self, text: str) -> List[float]:
#         """
#         Generate embedding for a single text.
#         """
#         response = await self.client.embeddings.create(
#             model=EMBEDDING_MODEL,
#             input=text,
#         )
#         return response.data[0].embedding
    
#     async def embed_texts(self, texts: List[str]) -> List[List[float]]:
#         """
#         Generate embeddings for multiple texts in a single API call.
        
#         More efficient than calling embed_text() multiple times. OpenAI allows up to 2048 inputs per request.
#         """
#         if not texts:
#             return []
        
#         batch_size = 100
#         all_embeddings = []
#         for i in range(0, len(texts), batch_size):
#             batch = texts[i: i + batch_size]
#             response = await self.client.embeddings.create(
#                 model=EMBEDDING_MODEL,
#                 input=batch
#             )
#             batch_embeddings = [item.embedding for item in response.data]
#             all_embeddings.extend(batch_embeddings)
#         return all_embeddings