"""
Document chunking service.

Splits long documents into smaller chunks for embedding and search.

Chunking strategy:
- Target size: ~1000 words (configurable)
- Respects paragraph boundaries when possible
- Each chunk gets a unique citation ID
- Preserves document metadata (title, date) with each chunk"""

import re
from typing import List
from dataclasses import dataclass

DEFAULT_CHUNK_SIZE = 1000


@dataclass
class Chunk:
    """
    Represents a chunk of a document.
    
    Attributes:
        citation_id: Unique ID like "doc_78643_chunk_00001"
        document_id: The source document's ID
        document_title: Title of the source document
        document_date: Date of the source document
        chunk_index: 0-based index of this chunk within the document
        text: The actual chunk content
        word_count: Number of words in this chunk
    """
    citation_id: str
    document_id: int
    document_title: str
    document_date: str
    chunk_index: int
    text: str
    word_count: int


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs.
    
    Paragraphs are separated by:
    - Double newlines (\n\n)
    - Single newlines followed by indentation
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs


def chunk_document(
    document_id: int,
    document_title: str,
    document_date: str,
    text: str,
    target_chunk_size: int = DEFAULT_CHUNK_SIZE
) -> List[Chunk]:
    """
    Split a document into chunks.
    
    Algorithm:
    1. Split text into paragraphs
    2. Accumulate paragraphs until reaching target size
    3. Start new chunk, repeat
    4. Handle edge cases (very long paragraphs, short documents)
    
    Args:
        document_id: Source document ID
        document_title: Document title (for context)
        document_date: Document date (for context)
        text: Full document text
        target_chunk_size: Target words per chunk
    
    Returns:
        List of Chunk objects
    """
    if not text or not text.strip():
        return []
    
    paragraphs = split_into_paragraphs(text)

    chunks = []
    current_chunk_text = []
    current_word_count = 0
    chunk_index = 0

    for paragraph in paragraphs:
        para_word_count = count_words(paragraph)

        if current_word_count + para_word_count > target_chunk_size and current_chunk_text:
            chunk_text = '\n\n'.join(current_chunk_text)

            citation_id = f"doc_{document_id}_chunk_{chunk_index:05d}"

            chunks.append(Chunk(
                citation_id=citation_id,
                document_id=document_id,
                document_title=document_title,
                document_date=document_date or "",
                chunk_index=chunk_index,
                text=chunk_text,
                word_count=current_word_count,
            ))

            current_chunk_text = []
            current_word_count = 0
            chunk_index += 1

        current_chunk_text.append(paragraph)
        current_word_count += para_word_count

    if current_chunk_text:
        chunk_text = '\n\n'.join(current_chunk_text)
        citation_id = f"doc_{document_id}_chunk_{chunk_index:05d}"

        chunks.append(Chunk(
            citation_id=citation_id,
            document_id=document_id,
            document_title=document_title,
            document_date=document_date or "",
            chunk_index=chunk_index,
            text=chunk_text,
            word_count=current_word_count,
        ))

    return chunks


# def chunk_all_documents(documents: List[dict], target_chunk_size: int = DEFAULT_CHUNK_SIZE) -> List[Chunk]:
#     """
#     Chunk all documents from API response.
    
#     Args:
#         documents: List of document dicts from Clearinghouse API
#         target_chunk_size: Target words per chunk

#     Returns:
#         List of all Chunk objects across all documents
#     """
#     all_chunks = []
#     for doc in documents:
#         doc_id = doc.get('id')
#         doc_title = doc.get('title', 'Untitled')
#         doc_date = doc.get('date', '')
#         doc_text = doc.get('text', '')

#         if not doc_text:
#             continue

#         doc_chunks = chunk_document(
#             document_id=doc_id,
#             document_title=doc_title,
#             document_date=doc_date,
#             text=doc_text,
#             target_chunk_size=target_chunk_size,
#         )

#     return all_chunks