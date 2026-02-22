# Quick test runner for preprocessing pipeline tests (Windows PowerShell)

Write-Host "======================================================================"
Write-Host "PREPROCESSING PIPELINE TEST SUITE"
Write-Host "======================================================================"
Write-Host ""

# Change to backend directory
Set-Location $PSScriptRoot

# Create output directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "tests\test_preprocessing\test_outputs" | Out-Null

Write-Host "Running all preprocessing tests..."
Write-Host ""

# Run tests with verbose output
python -m pytest tests\test_preprocessing\ -v -s --tb=short

Write-Host ""
Write-Host "======================================================================"
Write-Host "TEST RESULTS"
Write-Host "======================================================================"
Write-Host ""
Write-Host "Output files saved to: tests\test_preprocessing\test_outputs\"
Write-Host ""
Write-Host "View results in PowerShell:"
Write-Host "  Get-Content tests\test_preprocessing\test_outputs\01_fetch_result.json | ConvertFrom-Json | ConvertTo-Json"
Write-Host "  Get-Content tests\test_preprocessing\test_outputs\02_process_result.json | ConvertFrom-Json | ConvertTo-Json"
Write-Host "  Get-Content tests\test_preprocessing\test_outputs\03_persist_verification.json | ConvertFrom-Json | ConvertTo-Json"
Write-Host "  Get-Content tests\test_preprocessing\test_outputs\04_integration_result.json | ConvertFrom-Json | ConvertTo-Json"
Write-Host ""
Write-Host "Or open in VS Code:"
Write-Host "  code tests\test_preprocessing\test_outputs\"
Write-Host ""
