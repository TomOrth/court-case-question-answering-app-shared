# Run Real Preprocessing Tests (PowerShell)
# WARNING: These use REAL services and cost REAL money!

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "REAL PREPROCESSING TESTS - CASE 14919" -ForegroundColor Yellow
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "WARNING: These tests use real services:" -ForegroundColor Red
Write-Host "  - Real Clearinghouse API" -ForegroundColor Yellow
Write-Host "  - Real OpenAI embeddings (costs money)" -ForegroundColor Yellow
Write-Host "  - Real LLM summarization (costs money, takes time)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Estimated cost: ~`$0.10 - `$0.50 per full test" -ForegroundColor Yellow
Write-Host "Estimated time: 10-30 minutes per full test" -ForegroundColor Yellow
Write-Host ""

# Change to backend directory
Set-Location $PSScriptRoot

# Create output directory
New-Item -ItemType Directory -Force -Path "tests\test_preprocessing\test_outputs" | Out-Null

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "SELECT A TEST TO RUN:" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Fetch Only (Fast, Free) - Recommended first!" -ForegroundColor Green
Write-Host "2. Process Only (SLOW, EXPENSIVE - 10-30 min)" -ForegroundColor Yellow
Write-Host "3. Complete Pipeline (SLOW, EXPENSIVE - 10-30 min)" -ForegroundColor Yellow
Write-Host "4. Run All Tests (VERY SLOW, EXPENSIVE - 30-60 min)" -ForegroundColor Red
Write-Host "0. Cancel"
Write-Host ""

$choice = Read-Host "Enter choice (0-4)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "Running Test 1: Fetch Only..." -ForegroundColor Green
        python -m pytest tests\test_preprocessing\test_01_real_fetch.py -v -s
    }
    "2" {
        Write-Host ""
        Write-Host "Running Test 2: Process Only (this will take 10-30 minutes)..." -ForegroundColor Yellow
        python -m pytest tests\test_preprocessing\test_02_real_process.py -v -s
    }
    "3" {
        Write-Host ""
        Write-Host "Running Test 3: Complete Pipeline (this will take 10-30 minutes)..." -ForegroundColor Yellow
        python -m pytest tests\test_preprocessing\test_03_real_complete.py -v -s
    }
    "4" {
        Write-Host ""
        Write-Host "WARNING: Running all tests will take 30-60 minutes!" -ForegroundColor Red
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            Write-Host "Running all tests..." -ForegroundColor Yellow
            python -m pytest tests\test_preprocessing\ -v -s
        } else {
            Write-Host "Cancelled." -ForegroundColor Yellow
            exit
        }
    }
    "0" {
        Write-Host "Cancelled." -ForegroundColor Yellow
        exit
    }
    default {
        Write-Host "Invalid choice." -ForegroundColor Red
        exit
    }
}

Write-Host ""
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "TEST COMPLETE - CHECK OUTPUT FILES" -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Output files saved to: tests\test_preprocessing\test_outputs\" -ForegroundColor Green
Write-Host ""
Write-Host "View results:" -ForegroundColor Cyan
Write-Host "  code tests\test_preprocessing\test_outputs\" -ForegroundColor White
Write-Host ""
Write-Host "Or view individual files:" -ForegroundColor Cyan
Write-Host "  Get-Content tests\test_preprocessing\test_outputs\01_real_fetch_case_14919.json | ConvertFrom-Json" -ForegroundColor White
Write-Host "  Get-Content tests\test_preprocessing\test_outputs\02_initial_context_case_14919.txt" -ForegroundColor White
Write-Host ""
