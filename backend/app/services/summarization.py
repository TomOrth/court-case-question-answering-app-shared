"""
Document summarization service.

Handles summarization of court documents using chunks. Preserves citation IDs for traceability.
"""

from typing import List, Tuple, Dict, TYPE_CHECKING
from app.services.llm import get_llm_service
import textwrap

if TYPE_CHECKING:
    from app.services.preprocessing_types import ProcessedDocketEntry

MAX_TOKENS_PER_PART = 80000


class SummarizationService:
    """
    Service for summarizing court documents using in-memory chunks.

    + Group chunks by doc_id and sort by chunk_index
    + Recombine into "parts" with citation markers: [CITE:doc_78643_chunk_00001]
    + Each part < 80K tokens
    + Summarize each part with LLM
    + Combine part summaries if multiple parts
    + Return summaries dict
    """
    def __init__(self):
        self.llm = get_llm_service()

    async def summarize_documents_from_chunks(
        self,
        chunks: List[Tuple],
        documents: list
    ) -> Dict[int, str]:
        """
        Summarize all documents using chunk.

        Args:
            chunks: List of (ChunkModel, chunk_text) tuples from _process_documents()
            documents: List of document dicts from Clearinghouse API (for metadata)

        Returns:
            Dict mapping doc_id -> summary_text
        """
        print(f"\n{'='*80}")
        print(f"📝 DOCUMENT SUMMARIZATION")
        print(f"{'='*80}")
        print(f"Total documents to summarize: {len(documents)}")
        print(f"Total chunks available: {len(chunks)}\n")

        # Step 1: Group chunks by doc_id and sort by chunk_index
        print("📊 Grouping chunks by document...")
        chunks_by_doc = {}
        for chunk_model, chunk_text in chunks:
            doc_id = chunk_model.doc_id
            if doc_id not in chunks_by_doc:
                chunks_by_doc[doc_id] = []
            chunks_by_doc[doc_id].append((chunk_model.chunk_index, chunk_model.chunk_id, chunk_text))

        # Sort each document's chunks by chunk_index to maintain correct order
        for doc_id in chunks_by_doc:
            chunks_by_doc[doc_id].sort(key=lambda x: x[0])  # Sort by chunk index
            # Remove chunk_index after sorting, keep only (chunk_id, chunk_text)
            chunks_by_doc[doc_id] = [(chunk_id, text) for _, chunk_id, text in chunks_by_doc[doc_id]]
        
        print(f"✅ Grouped into {len(chunks_by_doc)} documents\n")

        # Step 2: Summarize each document
        summaries = {}
        for i, doc_data in enumerate(documents, start=1):
            doc_id = doc_data['id']
            doc_title = doc_data.get('title', 'Untitled')
            doc_date = doc_data.get('date', '')
            
            print(f"📄 Document {i}/{len(documents)}: {doc_title}")
            print(f"   ID: {doc_id}, Date: {doc_date}")

            doc_chunks = chunks_by_doc.get(doc_id, [])

            if not doc_chunks:
                print(f"   ⚠️  No chunks available for this document")
                summaries[doc_id] = "_No chunks available._"
                continue
            
            print(f"   📦 {len(doc_chunks)} chunks to process")

            try:
                summary = await self._summarize_document_from_chunk_list(
                    chunks=doc_chunks,
                    doc_title=doc_title,
                    doc_date=doc_date,
                )
                summaries[doc_id] = summary
                print(f"   ✅ Summary generated ({len(summary)} chars)\n")
            
            except Exception as e:
                print(f"   ❌ Error summarizing: {e}")
                summaries[doc_id] = f"_Error generating summary: {str(e)}_"
                print(f"   ⚠️  Continuing with next document...\n")
        
        print(f"{'='*80}")
        print(f"✅ SUMMARIZATION COMPLETE")
        print(f"   Successfully summarized: {sum(1 for s in summaries.values() if not s.startswith('_'))} documents")
        print(f"   Failed/Skipped: {sum(1 for s in summaries.values() if s.startswith('_'))} documents")
        print(f"{'='*80}\n")

        return summaries
    
    async def summarize_single_document(
        self,
        chunks: List[Tuple[str, str]],  # List of (chunk_id, chunk_text)
        doc_title: str,
        doc_date: str
    ) -> str:
        """
        Summarize a single document using its chunks.
        
        This is a standalone method for use in the new staged pipeline.
        
        Args:
            chunks: List of (chunk_id, chunk_text) tuples (already sorted)
            doc_title: Document title
            doc_date: Document date
            
        Returns:
            Summary text with [CITE:...] citations
        """
        return await self._summarize_document_from_chunk_list(
            chunks=chunks,
            doc_title=doc_title,
            doc_date=doc_date
        )
    
    async def _summarize_document_from_chunk_list(
        self,
        chunks: List[Tuple[str, str]],  # List of (chunk_id, chunk_text)
        doc_title: str,
        doc_date: str
    ) -> str:
        """
        Summarize a single document using its chunks
        
        Args:
            chunks: List of (chunk_id, chunk_text) tuples (already sorted)
            doc_title: Document title from API
            doc_date: Document date from API
            
        Returns:
            Summary text with [CITE:...] citations
        """
        # Step 1: Recombine chunks into parts (respecting context limit)
        print(f"   🔄 Recombining chunks into parts...")
        parts = self._recombine_chunks_into_parts(chunks)
        print(f"   ✅ Created {len(parts)} part(s) for summarization")

        # Step 2: If single part, summarize 
        if len(parts) == 1:
            print(f"   📝 Summarizing single part...")
            return await self._summarize_single_part(
                part_text=parts[0],
                doc_title=doc_title,
                doc_date=doc_date
            )

        # Step 3: If multiple parts, summarize each, then combine
        print(f"   📝 Summarizing {len(parts)} parts separately...")
        part_summaries = []
        for i, part_text in enumerate(parts, start=1):
            print(f"      Part {i}/{len(parts)}...")
            part_summary = await self._summarize_single_part(
                part_text=part_text,
                doc_title=doc_title,
                doc_date=doc_date,
                part_number=i,
                total_parts=len(parts),
            )
            part_summaries.append(part_summary)
            print(f"      ✅ Part {i} done ({len(part_summary)} chars)")

        # Step 4: Combine part summaries
        print(f"   🔗 Combining {len(part_summaries)} part summaries...")
        combined_summary = await self._combine_part_summaries(
            part_summaries=part_summaries,
            doc_title=doc_title,
            doc_date=doc_date
        )

        return combined_summary
    
    def _recombine_chunks_into_parts(
        self,
        chunks: List[Tuple[str, str]]  # (chunk_id, chunk_text)
    ) -> List[str]:
        """
        Recombine chunks into parts with citation markers.
        Each part < MAX_TOKENS_PER_PART.
        
        Format: [CITE:doc_78643_chunk_00001] followed by chunk text."""
        parts = []
        current_part_lines = []
        current_token_count = 0
        for chunk_id, chunk_text in chunks:
            # Format: [CITE:doc_78643_chunk_00001]
            citation = f"[CITE:{chunk_id}]"
            # Estimate tokens (roughly 1 token is 4 chars)
            chunk_tokens = len(citation + chunk_text) // 4

            # Check if adding this chunk exceeds limit
            if current_token_count + chunk_tokens > MAX_TOKENS_PER_PART and current_part_lines:
                # Save current part and start new one
                part_text = "\n\n".join(current_part_lines)
                parts.append(part_text)
                print(f"      Part {len(parts)}: ~{current_token_count:,} tokens, {len(current_part_lines)} chunks")
                current_part_lines = []
                current_token_count = 0

            # Add chunk with citation marker
            current_part_lines.append(f"{citation}\n{chunk_text}")
            current_token_count += chunk_tokens

        # Add final part
        if current_part_lines:
            part_text = "\n\n".join(current_part_lines)
            parts.append(part_text)            
            print(f"      Part {len(parts)}: ~{current_token_count:,} tokens, {len(current_part_lines)} chunks")
        return parts
    
    async def _summarize_single_part(
        self,
        part_text: str,
        doc_title: str,
        doc_date: str,
        part_number: int = 1,
        total_parts: int = 1,
    ) -> str:
        """
        Summarize a single part using LLM.
        
        LLM must preserve [CITE:...] markers in output!"""
        part_info = f" (Part {part_number} of {total_parts})" if total_parts > 1 else ""


        system_prompt = """You are a legal document summarizer. Your task is to create concise factual summaries of court documents.
        
        CITATION RULES:
        1. The input text contains citation markers (using chunk_id) like [CITE:doc_78643_chunk_00001]
        2. These mark the source of each text segment
        3. In your summary, include these [CITE:...] markers to show sources if you choose to include details from the corresponding chunks
        4. Format: "The plaintiff filed a motion [CITE:doc_78543_chunk_00003] on April 15."
        5. NEVER omit or modify the citation format - always use [CITE:chunk_id] - for the details included in the summary

        IMPORTANT: Please note that the format of the chunk ID provided to you should always have the 5 digits after "doc_X_chunk_". Do not change that format. (note that document ID does not need to be 5 digits). In any case, DO NOT CHANGE THE provided ID.

        Your summary should:
        - Capture key facts, parties, claims and holdings
        - Preserve chronology when relevant
        - Be concise but comprehensive (~800 words per part)              
        - Include [CITE:...] markers for all factual claims
        """
        
        user_prompt = f"""Summarize this court document {part_info}:
        **Title:** {doc_title}
        **Date:** {doc_date}

        **Document Text with Citations:**

        {part_text}

        Remember: Include [CITE:...] markers in your summary to cite sources!
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        summary = await self.llm.complete(
            messages=messages,
            model="gpt-5-mini",
            # temperature=0.3,  # Not supported by gpt-5-mini
            # max_tokens=1000   # Not supported by gpt-5-mini
        )

        return summary.strip()
    
    async def _combine_part_summaries(
        self,
        part_summaries: List[str],
        doc_title: str,
        doc_date: str
    ) -> str:
        """
        Combine multiple part summaries into a single coherent summary.
        """
        combined_parts = "\n\n---\n\n".join([
            f"**Part {i} Summary:**\n{summary}"
            for i, summary in enumerate(part_summaries, start=1)
        ])

        system_prompt = """You are a legal document summarizer. Your task is to combine multiple part summaries into a single coherent summary.
        
        CITATION RULES:
        1. Each part summary contains [CITE:doc_X_chunk_Y] markers
        2. These MUST be preserved in the combined summary if you choose to mention those details in the combined summary
        3. Format: "The plaintiff filed a motion [CITE:doc_78643_chunk_00003] on April 15."
        4. NEVER omit or modify citation markers for the detials mentioned in combined summary

        IMPORTANT: Please note that the format of the chunk ID / docket entry ID provided to you should always have the 5 digits after "case_..._docket_entry_" or "doc_X_chunk_". Do not change that format. (note that case ID or document ID does not need to be 5 digits). In any case, DO NOT CHANGE THE provided ID.
        
        Your combined summary should:
        - Synthesize key points from all parts
        - Remove redundancy
        - Maintain logical flow
        - Keep [CITE:...] markers intact
        """

        user_prompt = f"""Combine these part summaries into a single coherent summary:

        **Document:** {doc_title} ({doc_date})

        **Part Summaries:**

        {combined_parts}

        Remember: Preserve [CITE:...] markers if you choose to keep corresponding details in the combined summary.
        """

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        combined_summary = await self.llm.complete(
            messages=messages,
            model="gpt-5-mini",
            # temperature=0.3,  # Not supported by gpt-5-mini
            # max_tokens=1500,  # Not supported by gpt-5-mini
        )
        return combined_summary.strip()

    async def summarize_docket_entries(
        self,
        docket_entries: List['ProcessedDocketEntry']
    ) -> str:
        """
        Summarize a list of docket entries.
        
        1. Convert entries to text format
        2. Split into parts (reuse _recombine_chunks_into_parts)
        3. Summarize parts (new prompt)
        4. Combine summaries (new prompt)
        """
        print(f"\n{'='*80}")
        print(f"📅 DOCKET SUMMARIZATION")
        print(f"{'='*80}")
        
        if not docket_entries:
            return "No docket entries available."

        # 1. Convert to (id, text) tuples for the splitter
        docket_chunks = []
        for entry in docket_entries:
            text = f"Date: {entry.date_filed}\nDescription: {entry.description}"
            docket_chunks.append((entry.docket_entry_id, text))
            
        # 2. Split into parts (Reusing existing logic!)
        parts = self._recombine_chunks_into_parts(docket_chunks)
        print(f"   ✅ Created {len(parts)} docket parts")

        # 3. Summarize parts
        part_summaries = []
        for i, part_text in enumerate(parts, start=1):
            print(f"      Summarizing docket part {i}/{len(parts)}...")
            summary = await self._summarize_docket_part(part_text)
            part_summaries.append(summary)

        # 4. Combine if needed
        if len(part_summaries) == 1:
            return part_summaries[0]
        
        return await self._combine_docket_summaries(part_summaries)

    async def _summarize_docket_part(self, part_text: str) -> str:
        """Summarize a chunk of docket entries."""
        system_prompt = """You are a legal case analyst. Summarize the procedural history from these docket entries.
        
        CITATION RULES:
        1. Input contains markers like [CITE:case_12345_docket_entry_00123]
        2. You MUST include these citations for key events (filings, orders, judgments).
        3. Format: "Complaint filed by Plaintiff [CITE:case_12345_docket_entry_00001]."
        4. Keep the [CITE:case_..._docket_entry_...] markers if you plan to include the corresponding details in the summary.

        IMPORTANT: Please note that the format of the docket entry ID provided to you should always have the 5 digits after "case_..._docket_entry_". Do not change that format. (note that case ID does not need to be 5 digits). In any case, DO NOT CHANGE THE provided docket entry ID.
        """
        
        user_prompt = f"""Summarize these docket entries into a coherent timeline:
        
        {part_text}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return await self.llm.complete(
            messages=messages,
            model="gpt-5-mini",
            # max_tokens=2000  # Not supported by gpt-5-mini
        )

    async def _combine_docket_summaries(self, summaries: List[str]) -> str:
        """Combine multiple docket summaries."""
        combined_text = "\n\n".join(summaries)
        
        system_prompt = """You are a legal case analyst. Combine these partial docket summaries into a single coherent procedural history.
        
        Keep the [CITE:case_..._docket_entry_...] markers if you plan to include the corresponding details in the summary.
        """
        
        user_prompt = f"""Combine these summaries:
        
        {combined_text}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return await self.llm.complete(
            messages=messages,
            model="gpt-5-mini",
            # max_tokens=3000  # Not supported by gpt-5-mini
        )
