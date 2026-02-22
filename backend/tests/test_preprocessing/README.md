# Real Integration Tests for Case 14919

This directory contains **REAL** integration tests that fetch and process actual case 14919 from the Clearinghouse API.

⚠️ **WARNING**: These tests use REAL services and can take **10-30 minutes** to run!

## What These Tests Do

1. **Fetch real data** from Clearinghouse API
2. **Process with real services**:
   - Real chunking
   - Real OpenAI embeddings (costs $$$)
   - Real LLM summarization (costs $$$, takes time)
3. **Save to real test database**
4. **Generate detailed output files** for inspection

## Prerequisites

### 1. Environment Variables
Make sure your `.env` file has:
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://...
CLEARINGHOUSE_API_KEY=...
```

### 2. Install Dependencies
```bash
pip install pytest pytest-asyncio
```

### 3. Create Test Database
```sql
CREATE DATABASE court_qa_test_db;
```

## Running Tests

### ⚠️ IMPORTANT: Run tests ONE AT A TIME!

These tests are **expensive and slow**. Run them individually to control what you're testing.

### Test 1: Fetch Only (Fast, Free)
```bash
cd d:\Programming\court_qa_exp_v4\attempt_1\backend
python -m pytest tests/test_preprocessing/test_01_real_fetch.py -v -s
```

**Duration**: ~10 seconds  
**Cost**: Free  
**Output**:
- `01_real_fetch_case_14919.json` - Full case metadata
- `01_sample_document_text.txt` - Sample document text

---

### Test 2: Process Only (SLOW, EXPENSIVE)
```bash
python -m pytest tests/test_preprocessing/test_02_real_process.py -v -s
```

**Duration**: 10-30 minutes (depends on number of documents)  
**Cost**: $2-10 (OpenAI API for embeddings + summarization)  
**Output**:
- `02_real_process_case_14919.json` - Processing results
- `02_initial_context_case_14919.txt` - Generated initial context
- `02_doc_*_summary.txt` - Individual document summaries

⚠️ **This is the expensive test!** It generates embeddings and summaries for all documents.

---

### Test 3: Complete Pipeline (SLOW, EXPENSIVE)
```bash
python -m pytest tests/test_preprocessing/test_03_real_complete.py -v -s
```

**Duration**: 10-30 minutes  
**Cost**: $2-10 (same as Test 2)  
**Output**:
- `03_complete_pipeline_case_14919.json` - Full pipeline results
- `03_final_initial_context_case_14919.txt` - Final initial context
- `03_sample_chunks_case_14919.json` - Sample chunks with embeddings

⚠️ **This runs the complete pipeline** including saving to database!

---

## Output Files

All outputs are saved to `tests/test_preprocessing/test_outputs/`:

```
test_outputs/
├── 01_real_fetch_case_14919.json          # Raw API data
├── 01_sample_document_text.txt            # Sample document
├── 02_real_process_case_14919.json        # Processing results
├── 02_initial_context_case_14919.txt      # Generated context
├── 02_doc_*_summary.txt                   # Document summaries
├── 03_complete_pipeline_case_14919.json   # Full results
├── 03_final_initial_context_case_14919.txt
└── 03_sample_chunks_case_14919.json
```

### View Output Files

**PowerShell:**
```powershell
# List outputs
Get-ChildItem tests\test_preprocessing\test_outputs\

# View JSON
Get-Content tests\test_preprocessing\test_outputs\02_real_process_case_14919.json | ConvertFrom-Json | ConvertTo-Json

# View text
Get-Content tests\test_preprocessing\test_outputs\02_initial_context_case_14919.txt

# Open folder in VS Code
code tests\test_preprocessing\test_outputs\
```

## Verifying Database

After Test 3 completes, check the database:

```sql
-- Connect to test database
psql postgresql://user:pass@localhost/court_qa_test_db

-- Check case
SELECT case_id, case_name, status, preprocessed_at FROM cases WHERE case_id = 14919;

-- Check documents
SELECT doc_id, title, total_chunks FROM documents WHERE case_id = 14919;

-- Check chunks count
SELECT COUNT(*) FROM chunks WHERE case_id = 14919;

-- Check embeddings count
SELECT COUNT(*) FROM chunk_embeddings 
WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE case_id = 14919);

-- Check initial context
SELECT LENGTH(context_text), LEFT(context_text, 100) 
FROM initial_contexts WHERE case_id = 14919;
```

## Cost Estimates

### OpenAI API Costs
- **Embeddings**: ~$0.13 per 1M tokens
  - Typical case: ~100,000 tokens = ~$0.013
- **Summarization** (gpt-4o-mini): ~$0.15 per 1M input tokens
  - Typical case: ~200,000 tokens = ~$0.03
  
**Total per case**: ~$0.05 - $0.50 depending on document count

### Time Estimates
- **Fetch**: 10 seconds
- **Chunking**: 30 seconds
- **Embeddings**: 2-5 minutes (batched)
- **Summarization**: 10-20 minutes (sequential, with retries)
- **Persist**: 10 seconds

**Total**: 15-30 minutes for a typical case

## Troubleshooting

### "Rate limit exceeded"
The LLM service has retry logic. Just wait - it will retry automatically.

### "Connection timeout"
Increase timeout in `app/services/llm.py` or run again.

### "Database error"
Make sure test database exists:
```sql
CREATE DATABASE court_qa_test_db;
```

### "No module named 'app'"
Run from backend directory:
```bash
cd d:\Programming\court_qa_exp_v4\attempt_1\backend
```

## Recommended Workflow

1. **First time**: Run Test 1 (fetch only) to verify API works
2. **Check outputs**: Review fetched data in output files
3. **When ready**: Run Test 2 (process) - grab coffee ☕
4. **Review summaries**: Check document summaries in output files
5. **If satisfied**: Run Test 3 (complete) to save to database
6. **Verify database**: Use SQL queries above

## Testing Multiple Cases

To test a different case, modify `REAL_CASE_ID` in each test file:

```python
# In test_01_real_fetch.py, test_02_real_process.py, test_03_real_complete.py
REAL_CASE_ID = 15000  # Change to your case ID
```

## Comparing to Old vs New Pipeline

These tests verify the **NEW** 3-stage pipeline:
1. ✅ Fetch → keeps data in memory
2. ✅ Process → all computation without DB
3. ✅ Persist → single transaction

Benefits verified by these tests:
- Database never in inconsistent state
- Can inspect data before saving
- Clean error handling
- Single transaction at the end
