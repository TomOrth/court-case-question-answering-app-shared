"""
Stage 2: Process raw data into structured format.

This stage performs heavy computation:
- Chunks documents
- Generates embeddings
- Summarizes documents (SLOW!)
- Builds initial context

All data stays in memory. No database interaction.
"""

from typing import List, Dict, Optional
from datetime import date

from app.services.preprocessing_types import (
    RawCaseData, ProcessedCaseData, ProcessedDocument,
    ProcessedChunk, ProcessedDocketEntry
)
from app.services.chunking import chunk_document
# from app.services.embeddings import EmbeddingService
from app.services.summarization import SummarizationService


class ProcessStage:
    """Stage 2: Process raw data into structured format"""
    
    def __init__(self):
        # self.embeddings = EmbeddingService()
        self.summarization = SummarizationService()
    
    async def process_case_data(
        self, 
        raw_data: RawCaseData
    ) -> ProcessedCaseData:
        """
        Process raw case data into structured format.
        
        This is the heavy computation stage:
        - Chunks documents
        - Generates embeddings
        - Summarizes documents (SLOW!)
        - Builds initial context
        
        All data stays in memory. No database interaction.
        
        Returns:
            ProcessedCaseData ready for persistence
        """
        print(f"[PROCESS] Processing case {raw_data.case_id}...")
        
        # Process documents (includes chunking, embedding, and summarization)
        processed_docs = await self._process_documents(
            raw_data.case_id,
            raw_data.documents
        )
        
        # Process docket entries (fast, no LLM calls)
        docket_entries = self._process_docket_entries(
            raw_data.case_id,
            raw_data.dockets
        )
        
        # Summarize docket entries
        print(f"[PROCESS] Summarizing {len(docket_entries)} docket entries...")
        docket_summary = await self.summarization.summarize_docket_entries(docket_entries)
        
        # Build initial context
        initial_context = self._build_initial_context(
            raw_data.case_meta,
            processed_docs,
            docket_entries,
            docket_summary
        )
        
        print(f"[PROCESS] ✓ Processing complete!")
        
        return ProcessedCaseData(
            case_id=raw_data.case_id,
            case_name=raw_data.case_meta.get('name', 'Unknown'),
            court=raw_data.case_meta.get('court'),
            filing_date=self._parse_date(raw_data.case_meta.get('filing_date')),
            raw_json={
                'case': raw_data.case_meta,
                'documents': raw_data.documents,
                'dockets': raw_data.dockets
            },
            documents=processed_docs,
            docket_entries=docket_entries,
            initial_context=initial_context
        )
    
    async def _process_documents(
        self,
        case_id: int,
        documents: List[Dict]
    ) -> List[ProcessedDocument]:
        """Process all documents: chunk, embed, summarize"""
        print(f"[PROCESS] Processing {len(documents)} documents...")
        
        processed_docs = []
        
        for i, doc_data in enumerate(documents, start=1):
            if not doc_data.get('text'):
                print(f"[PROCESS] ⚠️  Skipping document {i}/{len(documents)}: No text")
                continue
            
            doc_id = doc_data['id']
            title = doc_data.get('title', 'Untitled')
            
            print(f"[PROCESS] Document {i}/{len(documents)}: {title}")
            
            # 1. Chunk the document
            chunks = chunk_document(
                document_id=doc_id,
                document_title=title,
                document_date=doc_data.get('date', ''),
                text=doc_data.get('text', '')
            )
            
            print(f"[PROCESS]   ✓ Created {len(chunks)} chunks")
            
            # 2. Generate embeddings for all chunks
            # chunk_texts = [c.text for c in chunks]
            # embeddings = await self.embeddings.embed_texts(chunk_texts)
            
            # print(f"[PROCESS]   ✓ Generated {len(embeddings)} embeddings")
            
            # 3. Create ProcessedChunk objects
            processed_chunks = [
                ProcessedChunk(
                    chunk_id=chunk.citation_id,
                    doc_id=doc_id,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.text,
                    # embedding=embedding
                )
                # for chunk, embedding in zip(chunks, embeddings)
                for chunk in chunks
            ]
            
            # 4. Summarize this document using its chunks
            print(f"[PROCESS]   → Summarizing document...")
            summary = await self.summarization.summarize_single_document(
                chunks=[(c.chunk_id, c.chunk_text) for c in processed_chunks],
                doc_title=title,
                doc_date=doc_data.get('date', '')
            )
            
            print(f"[PROCESS]   ✓ Summary generated ({len(summary)} chars)")
            
            # 5. Create ProcessedDocument
            processed_doc = ProcessedDocument(
                doc_id=doc_id,
                case_id=case_id,
                title=title,
                doc_date=self._parse_date(doc_data.get('date')),
                file_url=doc_data.get('file'),
                clearinghouse_link=doc_data.get('clearinghouse_link'),
                summary=summary,
                chunks=processed_chunks
            )
            
            processed_docs.append(processed_doc)
        
        print(f"[PROCESS] ✓ Processed {len(processed_docs)} documents")
        return processed_docs
    
    def _process_docket_entries(
        self,
        case_id: int,
        dockets: List[Dict]
    ) -> List[ProcessedDocketEntry]:
        """Process docket entries (fast, no LLM calls)"""
        entries = []
        entry_index = 0
        
        for docket in dockets:
            if not docket.get('is_main_docket'):
                continue
            
            for entry_data in docket.get('docket_entries', []):
                entry = ProcessedDocketEntry(
                    docket_entry_id=f"case_{case_id}_docket_entry_{entry_index:05d}",
                    case_id=case_id,
                    entry_number=entry_data.get('entry_number'),
                    date_filed=self._parse_date(entry_data.get('date_filed')),
                    description=entry_data.get('description', ''),
                    url=entry_data.get('url'),
                    recap_pdf_url=entry_data.get('recap_pdf_url'),
                    pacer_doc_id=entry_data.get('pacer_doc_id')
                )
                entries.append(entry)
                entry_index += 1
        
        print(f"[PROCESS] ✓ Processed {len(entries)} docket entries")
        return entries
    
    def _build_initial_context(
        self,
        case_meta: Dict,
        documents: List[ProcessedDocument],
        docket_entries: List[ProcessedDocketEntry],
        docket_summary: str = ""
    ) -> str:
        """Build initial context text"""
        context_parts = [
            f"# Case: {case_meta.get('name', 'Unknown')}",
            f"\n## Basic Information",
            f"- Court: {case_meta.get('court', 'Unknown')}",
            f"- State: {case_meta.get('state', 'Unknown')}",
            f"- Filing Date: {case_meta.get('filing_date', 'Unknown')}",
            f"- Case Status: {case_meta.get('case_ongoing', 'Unknown')}",
        ]
        
        if case_meta.get('summary'):
            context_parts.append(f"\n## Case Summary\n{case_meta['summary']}")
        
        if documents:
            context_parts.append(f"\n## Document Summaries\n")
            context_parts.append(
                f"This case has {len(documents)} documents. "
                f"Below are AI-generated summaries with citations.\n"
            )
            
            for doc in documents:
                context_parts.append(
                    f"### [Document ID: {doc.doc_id}] {doc.title} "
                    f"({doc.doc_date or 'no date'})\n"
                )
                context_parts.append(f"{doc.summary}\n")
        
        if docket_entries:
            context_parts.append(
                f"\n## Docket Entries\n"
                f"{len(docket_entries)} docket entries available.\n"
            )
            if docket_summary:
                context_parts.append(f"\n### Procedural History Summary\n{docket_summary}\n")
        
        print(f"[PROCESS] ✓ Built initial context ({len(''.join(context_parts))} chars)")
        return '\n'.join(context_parts)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string"""
        if not date_str:
            return None
        try:
            return date.fromisoformat(date_str)
        except (ValueError, AttributeError):
            return None
