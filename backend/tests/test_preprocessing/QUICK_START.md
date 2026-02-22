# Quick Start: Real Integration Tests for Case 14919

## ⚠️ IMPORTANT: These tests use REAL services and cost REAL money!

- Real Clearinghouse API
- Real OpenAI embeddings ($$)
- Real LLM summarization ($$)
- Takes 10-30 minutes to run

## Run Tests ONE AT A TIME

### Test 1: Fetch Only (Fast, Free) ✅ Start Here!

```powershell
cd d:\Programming\court_qa_exp_v4\attempt_1\backend
python -m pytest tests/test_preprocessing/test_01_real_fetch.py -v -s
```

**Duration**: ~10 seconds  
**Cost**: Free  
**What it does**: Fetches case 14919 from Clearinghouse API  
**Output**: `test_outputs/01_real_fetch_case_14919.json`

---

### Test 2: Process Only (SLOW, EXPENSIVE) ⚠️

```powershell
python -m pytest tests/test_preprocessing/test_02_real_process.py -v -s
```

**Duration**: 10-30 minutes  
**Cost**: ~$0.10 - $0.50 in OpenAI API calls  
**What it does**: Chunks, embeds, and summarizes all documents  
**Output**: 
- `test_outputs/02_real_process_case_14919.json`
- `test_outputs/02_initial_context_case_14919.txt`
- `test_outputs/02_doc_*_summary.txt`

---

### Test 3: Complete Pipeline (SLOW, EXPENSIVE) ⚠️

```powershell
python -m pytest tests/test_preprocessing/test_03_real_complete.py -v -s
```

**Duration**: 10-30 minutes  
**Cost**: ~$0.10 - $0.50  
**What it does**: Full pipeline + saves to database  
**Output**:
- `test_outputs/03_complete_pipeline_case_14919.json`
- `test_outputs/03_final_initial_context_case_14919.txt`
- `test_outputs/03_sample_chunks_case_14919.json`

---

## View Results

```powershell
# Open output folder in VS Code
code tests\test_preprocessing\test_outputs\

# View a specific file
Get-Content tests\test_preprocessing\test_outputs\02_initial_context_case_14919.txt

# View JSON with formatting
Get-Content tests\test_preprocessing\test_outputs\02_real_process_case_14919.json | ConvertFrom-Json | ConvertTo-Json
```

## What Gets Tested

✅ **Fetch Stage**: Real API call to Clearinghouse  
✅ **Process Stage**: Real chunking, embeddings, summarization  
✅ **Persist Stage**: Single transaction save to database  
✅ **Verification**: Database state after save  

## Before Running

Make sure `.env` has:
```env
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql+asyncpg://...
CLEARINGHOUSE_API_KEY=...
```

Also create the test database:
```sql
CREATE DATABASE court_qa_test_db;
```

## Recommended Order

1. Run Test 1 (fetch) - verify API works ✅
2. Check output files - review fetched data 👀
3. Run Test 2 (process) - grab coffee ☕ (takes 15+ minutes)
4. Review summaries - check quality 👀
5. Run Test 3 (complete) - save to database 💾
6. Verify database - check data integrity ✅

See [README.md](README.md) for full documentation.
