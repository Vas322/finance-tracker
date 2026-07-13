"""
PowerShell script to clean up test files and prepare for commit
"""

# Set working directory
$script:ProjectDir = "E:\\Фото\\Мои_доки\\finance_tracker"
Set-Location $script:ProjectDir

Write-Host "Working in: $(Get-Location)" -ForegroundColor Green
Write-Host "``================ Listing .py files================``" -ForegroundColor Cyan

# List all .py files
$allPyFiles = Get-ChildItem -Name "*.py"
$allPyFiles | ForEach-Object { 
    Write-Host "  $_" 
}
Write-Host "Total: $($allPyFiles.Count)"

# Find test_*.py and check_*.py files
$testFiles = Get-ChildItem -Name "test_*.py" -ErrorAction SilentlyContinue
$checkFiles = Get-ChildItem -Name "check_*.py" -ErrorAction SilentlyContinue

Write-Host "\ntest_*.py files found:"
$testFiles | ForEach-Object { Write-Host "  $($_.Name)" }
Write-Host "\ncheck_*.py files found:"
$checkFiles | ForEach-Object { Write-Host "  $($_.Name)" }

# Delete files
$filesToDelete = @($testFiles + $checkFiles)
if ($filesToDelete.Count -gt 0) {
    Write-Host "\nDeleting files..." -ForegroundColor Yellow
    $deleted = @()
    $failed = @()
    
    foreach ($file in $filesToDelete) {
        try {
            Remove-Item -Path $file.FullName -Force
            $deleted += $file.Name
            Write-Host "✓ Deleted: $($file.Name)" -ForegroundColor Green
        } catch {
            $failed += $file.Name
            Write-Host "✗ Error deleting $($file.Name): $_" -ForegroundColor Red
        }
    }
    
    Write-Host "\nSuccessfully deleted: $($deleted.Count) files"
    if ($deleted.Count -gt 0) { Write-Host "  $($deleted -join ', ')" }
    Write-Host "Failed to delete: $($failed.Count) files" 
    if ($failed.Count -gt 0) { Write-Host "  $($failed -join ', ')" }
} else {
    Write-Host "\nNo test_*.py or check_*.py files found to delete." -ForegroundColor Yellow
}

# Verify
Write-Host "\n=== Remaining .py files ==="
$remaining = Get-ChildItem -Name "*.py"
$remaining | Sort-Object Name | ForEach-Object { Write-Host "  $_.Name" }
Write-Host "Count: $($remaining.Count)"
