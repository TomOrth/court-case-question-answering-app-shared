"""
Document QA Service - Map-Reduce for long documents.

This service enables the planner to ask detailed questions about a specific document. It uses a Map-Reduce pattern to handle documents that are too long to fit in a single LLM context window.

Map-Reduce Flow:
1. MAP: Compile document chunks (from preprocessing) into parts that fit in context window
2. MAP: Ask questions on each part independently
3. REDUCE: Combine all part answers into final coherent answer
"""

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Chunk, Document
from app.services.llm import get_llm_service
from app.utils.llm_logger import get_llm_logger


class DocumentQAService:
    """
    Service for asking questions about specific documents.
    
    This is used when the Planner has identified a relevant document and needs detailed information from it.
    """
    MAX_TOKENS_PER_PART = 75000
    MAX_TOKENS_FOR_COMBINE = 50000

    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        """
        self.db = db
        self.llm_service = get_llm_service()
        # self.llm_logger = get_llm_logger()

    async def ask_questions_on_document(
        self,
        doc_id: int,
        questions: List[str],
        planners_context: str,
        case_id: int,
        logger=None
    ) -> str:
        """
        Ask a set of questions about a specific document.
        
        This method implements the Map-Reduce pattern:
        1. Fetch all chunks for the document
        2. Split chunks into "parts" based on token budget
        3. Ask questions on each part (MAP phase)
        4. Combine all answers (REDUCE phase)
        
        Args:
            doc_id: The document to analyze
            questions: List of questions to answer
            planners_context: Context from the Planner about why these questions matter
            case_id: Case ID (for validation)
        
        Returns:
            Formatted Q&A string with inline citations
        
        Example:
            result = await service.ask_questions_on_document(
                doc_id=78342,
                questions=[
                    "What was the date of this ruling?",
                    "Who was the presiding judge?"
                ],
                planners_context="User is asking about the preliminary injunction.",
                case_id=14919
            )        
        """
        # Fetch document metadata and all chunks
        doc_data = await self._fetch_document_with_chunks(doc_id, case_id)

        if not doc_data:
            return f"Error: Document {doc_id} not found or not in case {case_id}"
        
        doc_title = doc_data['title']
        chunks = doc_data['chunks']

        if len(chunks) == 0:
            return f"Error: Document {doc_id} has no chunks"
        
        # Split chunks into "parts" that fit in context window
        parts = self._split_into_parts(chunks)

        # MAP Phase - Ask questions on each part
        part_answers = []
        for i, part_chunks in enumerate(parts, 1):
            answer = await self._ask_questions_on_part(
                part_chunks=part_chunks,
                questions=questions,
                doc_id=doc_id,
                doc_title=doc_title,
                planners_context=planners_context,
                part_number=i,
                total_parts=len(parts),
                case_id=case_id,
                logger=logger
            )            
            part_answers.append(answer)

        # REDUCE Phase - Combine all part answers
        if len(parts) == 1:
            # Only one part, no need to combine
            final_answer = part_answers[0]
        else:
            final_answer = await self._combine_part_answers(
                part_answers=part_answers,
                questions=questions,
                doc_id=doc_id,
                doc_title=doc_title,
                case_id=case_id,
                logger=logger
            )

        # Format the final result
        result = (
            f"[Tool: ask_questions_document]\n"
            f"[Document: doc_id={doc_id}, title=\"{doc_title}\"]\n"
            f"[Questions: {len(questions)}, Document Chunks: {len(chunks)}, Parts Processed: {len(parts)}]\n\n"
            f"{final_answer}"
        )
        return result        

    async def _fetch_document_with_chunks(
        self,
        doc_id: int,
        case_id: int
    ) -> Dict[str, Any]:        
        """
        Fetch document metadata and all its chunks, ordered by position
        
        Uses explicit joins.
        
        Returns:
            Dict with 'title', 'doc_date', and 'chunks' (list of Chunk objects)
            Returns None if document not found      """
        # First, verify document exists and get metadata
        doc_stmt = select(Document).where(
            Document.doc_id == doc_id,
            Document.case_id == case_id
        )
        doc_result = await self.db.execute(doc_stmt)
        doc = doc_result.scalar_one_or_none()

        if not doc:
            return None

        # Fetch all chunks for this document, ordered by position
        chunks_stmt = (
            select(Chunk)
            .where(
                Chunk.doc_id == doc_id,
                Chunk.case_id == case_id
            )
            .order_by(Chunk.chunk_index)
        )
        chunks_result = await self.db.execute(chunks_stmt)
        chunks = chunks_result.scalars().all()

        return {
            'title': doc.title,
            'doc_date': doc.doc_date,
            'chunks': chunks
        }

            

    def _split_into_parts(self, chunks: List[Chunk]) -> List[List[Chunk]]:
        """
        Split chunks into "parts" that fit within token budget.
        
        We count tokens for each chunk and group them until we hit MAX_TOKENS_PER_PART. This ensures each LLM call stays within the context window.

        Args:
            chunks: All chunks for the document, in order
        
        Returns:
            List of lists, where each inner list is a "part"        
        """
        parts = []
        current_part = []
        current_tokens = 0

        for chunk in chunks:
            # Count tokens in this chunk
            chunk_tokens = self.llm_service.count_tokens(chunk.chunk_text)

            # Check if adding this chunk would exceed the budget
            if current_tokens + chunk_tokens > self.MAX_TOKENS_PER_PART and current_part:
                # Save current part and start a new one
                parts.append(current_part)
                current_part = [chunk]
                current_tokens = chunk_tokens
            else:
                # Add to current part
                current_part.append(chunk)
                current_tokens += chunk_tokens

        # Don't forget the last part
        if current_part:
            parts.append(current_part)
        
        return parts
        
    def _build_citable_text(self, chunks: List[Chunk]) -> str:
        """
        Build text where each chunk has an inline citation marker.
        
        Format: chunk text followed by [CITE:chunk_id] at the end. This makes it easy for the LLM to cite its sources.
        
        Args:
            chunks: List of chunks to format
            
        Returns:
            String with all chunks and citations

        Example output:
            "
            --- CHUNK: doc_123_chunk_00005 ---
            The court ruled in favor... [CITE:doc_123_chunk_00005]
            
            --- CHUNK: doc_123:chunk_00006 ---
            The reasoning was based on... [CITE:doc_123_chunk_00006]"
        """
        formatted_chunks = []
        for chunk in chunks:
            # Each chunk gets tagged with citation maker
            formatted_chunks.append(
                f"--- CHUNK: {chunk.chunk_id} ---\n"
                f"{chunk.chunk_text}\n"
                f"[CITE:{chunk.chunk_id}]\n"
            )
        return "\n\n".join(formatted_chunks)

    async def _ask_questions_on_part(
        self,
        part_chunks: List[Chunk],
        questions: List[str],
        doc_id: int,
        doc_title: str,
        planners_context: str,
        part_number: int,
        total_parts: int,
        case_id: int,
        logger=None
    ) -> str:
        """
        Ask questions on a single "part" of the document (MAP phase).
        
        This constructs a prompt that:
        - Provides the planner's context
        - Shows the document text with citation markers
        - Lists the questions to answer
        - Instructs the LLM to use inline citations
        
        Args:
            part_chunks: The chunks for this part
            questions: Questions to answer
            planners_context: Why these questions matter
            part_number: Which part this is (1, 2, 3...)
            total_parts: How many parts total
            case_id: Case ID for logging
        
        Returns:
            The LLM's answer in Q&A format with inline citations
        """
        # Build the citable document text
        document_text = self._build_citable_text(part_chunks)

        # Format the questions as a numbered list
        questions_text = "\n".join(
            f"{i}. {q}" for i, q in enumerate(questions, 1)
        )

        # Construct the prompt
        prompt = f"""
You are analyzing a legal document to answer specific questions.

Document: {doc_title} (ID: {doc_id})

Context from Planner:
{planners_context}

Document Section (Part {part_number} of {total_parts}):
{document_text}

Questions:
{questions_text}

Instructions:
- Answer each question based ONLY on the document text provided above
- Use direct quotes from the chunks, when possible, to support your answers.
- ALWAYS cite using inline format: place [CITE:chunk_id] immediately after the relevant statement
- You can use multiple citations in one answer: "Statement A [CITE:id1] and Statement B [CITE:id2]"
- If the answer is not in this section, be honest and acknowledge, "Not found in this part"
- Be concise but complete
- You are strictly forbidden from generating Chunk IDs that are not present in the input list. Be very careful not to mistake, for example, "Page 14" or other numbers for chunk IDs.
- Please cite each chunk separately in each [CITE:chunk_id], especially when there are multiple chunks being referenced. For example, this citation is WRONG: "[CITE:doc_78277_chunk_00007; doc_78281_chunk_00005; doc_78340_chunk_00001]". The correct format should be "[CITE:doc_78277_chunk_00007][CITE:doc_78281_chunk_00005][CITE:doc_78340_chunk_00001]" so that the frontend can parse and convert into links correctly; but in general, please try to put citations directly after their corresponding details, so they don't get clustered together like that - which would make it confusing for the user to know a citation pertains to which detail.

Format your response as:
Q: [question 1 - repeated verbatim]
A: [answer with inline citations]

Q: [question 2 - repeated verbatim]
A: [answer with inline citations]

Example citation: "The court ruled in favor [CITE:doc_123_chunk_00005] based on precedent [CITE:doc_123_chunk_00012]."
        """

        # Call the LLM
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # Determine log source
        if total_parts == 1:
            log_source = f"Executor - Document QA (doc_{doc_id})"
        else:
            log_source = f"Executor - Document QA (doc_{doc_id}, part_{part_number}of{total_parts})"
        
        answer = await self.llm_service.complete(
            messages=messages,
            model="gpt-5-mini",
            # temperature=0.1,  # Not supported by gpt-5-mini (Low temperature for factual Q&A)
            # max_tokens=10000,  # Not supported by gpt-5-mini
            log_source=log_source,
            case_id=case_id,
            logger=logger
        )

        return answer
    
    async def _combine_part_answers(
        self,
        part_answers: List[str],
        questions: List[str],
        doc_id: int,
        doc_title: str,
        case_id: int,
        logger=None
    ) -> str:
        """
        Combine answers from multiple parts into final coherent answers (REDUCE phase).
        
        This is necessary when the document was too long to process in one pass. The LLM needs to synthesize information from all parts.
        
        Args:
            part_answers: Answers from each part (from MAP phase)
            questions: Original questions (for context)
            case_id: Case ID for logging
        
        Returns:
            Combined Q&A with inline citations preserved
        """
        # Format part answers for the combining prompt
        formatted_parts = []
        for i, answer in enumerate(part_answers, 1):
            formatted_parts.append(f"=== Part {i} Answers ===\n{answer}")

        parts_text = "\n\n".join(formatted_parts)

        questions_text = "\n".join(
            f"{i}. {q}" for i, q in enumerate(questions, 1)
        )

        # Construct combining prompt
        prompt = f"""
You have received answers to the same questions from multiple sections of a legal document.

Your task is to combine them into coherent final answers.

Document: {doc_title} (ID: {doc_id})

Original Questions:
{questions_text}

{parts_text}

Instructions:
- Synthesize all information into coherent, complete answers for each question
- Remove duplicate information
- When you incorporate information from a part answer, preserve the inline citations [CITE:chunk_id] that support that specific information
- If answers from different parts conflict, mention both perspectives with their respective citations
- Maintain the inline citation format: "Statement [CITE:id1] and another statement [CITE:id2]"
- Keep the Q: and A: format

Format your response as:
Q: [question 1]
A: [combined answer with inline citations]

Q: [question 2]
A: [combined answer with inline citations]
        """

        # Call the LLM to combine
        messages = [
            {"role": "user", "content": prompt}
        ]
        combined = await self.llm_service.complete(
            messages=messages,
            model="gpt-5-mini",
            # temperature=0.1,  # Not supported by gpt-5-mini
            # max_tokens=10000,  # Not supported by gpt-5-mini
            log_source=f"Executor - Document QA Combine (doc_{doc_id})",
            case_id=case_id,
            logger=logger
        )
        return combined