"""
Tests for Stage 2: Process raw data (chunking, embeddings, summarization).
"""

import pytest
import json
import dataclasses
from pathlib import Path
from unittest.mock import AsyncMock, patch

from app.services.stages.process import ProcessStage
from app.services.preprocessing_types import RawCaseData, ProcessedCaseData


# Output directory for test results
OUTPUT_DIR = Path(__file__).parent / "test_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def dataclass_to_dict(obj):
    """Convert dataclass to dict for JSON serialization."""
    if dataclasses.is_dataclass(obj):
        return {k: dataclass_to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    elif isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}
    else:
        return obj


class TestProcessStage:
    """Test the process stage."""
    
    @pytest.mark.asyncio
    async def test_process_case_data_full_pipeline(self, mock_raw_case_data):
        """Test processing raw case data through full pipeline."""
        # Create RawCaseData from mock
        raw_data = RawCaseData(
            case_id=mock_raw_case_data['case']['id'],
            case_meta=mock_raw_case_data['case'],
            documents=mock_raw_case_data['documents'],
            dockets=mock_raw_case_data['dockets']
        )
        
        # Mock embeddings service
        with patch('app.services.stages.process.EmbeddingService') as MockEmbeddings, \
             patch('app.services.stages.process.SummarizationService') as MockSummarization:
            
            # Mock embeddings to return fake vectors
            mock_embeddings = MockEmbeddings.return_value
            mock_embeddings.embed_texts = AsyncMock(
                side_effect=lambda texts: [[0.1] * 1536 for _ in texts]
            )
            
            # Mock summarization
            mock_summarization = MockSummarization.return_value
            mock_summarization.summarize_single_document = AsyncMock(
                return_value="[CITE:doc_88888_chunk_00001] This is a test summary of the document."
            )
            
            # Process the data
            process_stage = ProcessStage()
            result = await process_stage.process_case_data(raw_data)
            
            # Verify result structure
            assert isinstance(result, ProcessedCaseData)
            assert result.case_id == 99999
            assert result.case_name == 'Test Case v. Defendant'
            assert len(result.documents) == 2  # 2 documents with text
            assert len(result.docket_entries) == 2  # 2 docket entries
            
            # Verify first document processing
            first_doc = result.documents[0]
            assert first_doc.doc_id == 88888
            assert first_doc.title == 'Test Complaint'
            assert len(first_doc.chunks) > 0
            assert first_doc.summary.startswith("[CITE:")
            
            # Verify chunks have embeddings
            first_chunk = first_doc.chunks[0]
            assert first_chunk.chunk_id.startswith("doc_88888_chunk_")
            assert len(first_chunk.embedding) == 1536
            assert first_chunk.chunk_text != ""
            
            # Verify initial context was built
            assert result.initial_context != ""
            assert "Test Case v. Defendant" in result.initial_context
            assert "Document Summaries" in result.initial_context
            
            # Save detailed result to file
            output_file = OUTPUT_DIR / "02_process_result.json"
            result_dict = {
                'case_id': result.case_id,
                'case_name': result.case_name,
                'documents_count': len(result.documents),
                'docket_entries_count': len(result.docket_entries),
                'documents': [
                    {
                        'doc_id': doc.doc_id,
                        'title': doc.title,
                        'chunks_count': len(doc.chunks),
                        'summary_preview': doc.summary[:200] + '...' if len(doc.summary) > 200 else doc.summary,
                        'first_chunk': {
                            'chunk_id': doc.chunks[0].chunk_id if doc.chunks else None,
                            'text_preview': doc.chunks[0].chunk_text[:100] + '...' if doc.chunks else None,
                            'has_embedding': len(doc.chunks[0].embedding) > 0 if doc.chunks else False
                        }
                    }
                    for doc in result.documents
                ],
                'initial_context_preview': result.initial_context[:500] + '...'
            }
            
            with open(output_file, 'w') as f:
                json.dump(result_dict, f, indent=2)
            
            # Save full initial context
            context_file = OUTPUT_DIR / "02_initial_context.txt"
            with open(context_file, 'w') as f:
                f.write(result.initial_context)
            
            print(f"\n✓ Process result saved to: {output_file}")
            print(f"✓ Initial context saved to: {context_file}")
    
    @pytest.mark.asyncio
    async def test_process_skips_documents_without_text(self, mock_raw_case_data):
        """Test that documents without text are skipped."""
        # Modify mock data to have document without text
        raw_data_dict = mock_raw_case_data.copy()
        raw_data_dict['documents'] = [
            {'id': 11111, 'title': 'No Text Doc', 'date': '2023-01-01'},  # No 'text' field
            raw_data_dict['documents'][0]  # Has text
        ]
        
        raw_data = RawCaseData(
            case_id=raw_data_dict['case']['id'],
            case_meta=raw_data_dict['case'],
            documents=raw_data_dict['documents'],
            dockets=raw_data_dict['dockets']
        )
        
        with patch('app.services.stages.process.EmbeddingService') as MockEmbeddings, \
             patch('app.services.stages.process.SummarizationService') as MockSummarization:
            
            mock_embeddings = MockEmbeddings.return_value
            mock_embeddings.embed_texts = AsyncMock(
                side_effect=lambda texts: [[0.1] * 1536 for _ in texts]
            )
            
            mock_summarization = MockSummarization.return_value
            mock_summarization.summarize_single_document = AsyncMock(
                return_value="Test summary"
            )
            
            process_stage = ProcessStage()
            result = await process_stage.process_case_data(raw_data)
            
            # Should only process 1 document (the one with text)
            assert len(result.documents) == 1
            assert result.documents[0].doc_id == 88888
    
    @pytest.mark.asyncio
    async def test_process_builds_correct_initial_context(self, mock_raw_case_data):
        """Test that initial context is built correctly."""
        raw_data = RawCaseData(
            case_id=mock_raw_case_data['case']['id'],
            case_meta=mock_raw_case_data['case'],
            documents=mock_raw_case_data['documents'],
            dockets=mock_raw_case_data['dockets']
        )
        
        with patch('app.services.stages.process.EmbeddingService') as MockEmbeddings, \
             patch('app.services.stages.process.SummarizationService') as MockSummarization:
            
            mock_embeddings = MockEmbeddings.return_value
            mock_embeddings.embed_texts = AsyncMock(
                side_effect=lambda texts: [[0.1] * 1536 for _ in texts]
            )
            
            mock_summarization = MockSummarization.return_value
            mock_summarization.summarize_single_document = AsyncMock(
                return_value="Mock summary with [CITE:doc_123_chunk_001]"
            )
            
            process_stage = ProcessStage()
            result = await process_stage.process_case_data(raw_data)
            
            context = result.initial_context
            
            # Verify context structure
            assert "# Case: Test Case v. Defendant" in context
            assert "## Basic Information" in context
            assert "U.S. District Court for the Test District" in context
            assert "## Case Summary" in context
            assert "This is a test case summary." in context
            assert "## Document Summaries" in context
            assert "2 documents" in context
            assert "## Docket Entries" in context
            assert "2 docket entries" in context
