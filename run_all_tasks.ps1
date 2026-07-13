# PowerShell script to complete all tasks

# Set working directory
$ProjectDir = "E:\\Фото\\Мои_доки\\finance_tracker"
Set-Location $ProjectDir

Write-Host "=== PowerShell Operations Script ===" -ForegroundColor Cyan

# Step 1: List all .py files
Write-Host "\nStep 1: Listing all .py files" -ForegroundColor Green
Write-Host "Current directory: $(pwd)"

$allPyFiles = Get-ChildItem -Name "*.py"
foreach ($file in $allPyFiles) {
    Write-Host "  $($file.Name)"
}

# Step 2: Delete test_*.py and check_*.py files
Write-Host "\nStep 2: Deleting test_*.py and check_*.py files" -ForegroundColor Green

$testFilesToDelete = @(
    "check_import.py",
    "check_quick_templates.py",
    "test_env.txt",
    "test_full_import.py",
    "test_import.py",
    "test_import_app.py",
    "test_import_final.py",
    "test_import_simple.py",
    "test_runner.py",
    "test_script.py",
    "test_simple.py",
    "test_startup.py"
)

foreach ($fileName in $testFilesToDelete) {
    if (Test-Path $fileName) {
        try {
            Remove-Item $fileName -Force
            Write-Host "  ✓ Deleted: $fileName" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ Error deleting $fileName`: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  • Not found: $fileName" -ForegroundColor Yellow
    }
}

# Step 3: Verify deletion by listing remaining files
Write-Host "\nStep 3: Verifying deletion" -ForegroundColor Green
$remainingPyFiles = Get-ChildItem -Name "*.py" -ErrorAction SilentlyContinue
Write-Host "Remaining .py files:"
foreach ($file in $remainingPyFiles) {
    Write-Host "  $($file.Name)"
}

# Step 4: Show git status after deletion
Write-Host "\nStep 4: Git status after deletion" -ForegroundColor Green
$statusOutput = git status
Write-Host "$statusOutput"

# Step 5: Stage required files
Write-Host "\nStep 5: Staging required files" -ForegroundColor Green
$filesToStage = @(
    "app.py",
    "routes/__init__.py",
    "routes/quick_templates.py",
    "services/quick_template_service.py",
    "static/js/quick_templates.js",
    "templates/index.html"
)

foreach ($fileName in $filesToStage) {
    if (Test-Path $fileName) {
        $stageResult = git add $fileName
        Write-Host "  ✓ Staged: $fileName" -ForegroundColor Green
    } else {
        Write-Host "  ✗ File not found: $fileName" -ForegroundColor Red
    }
}

# Step 6: Check git status after staging
Write-Host "\nStep 6: Git status after staging" -ForegroundColor Green
$statusOutput = git status
Write-Host "$statusOutput"

# Step 7: Commit changes
Write-Host "\nStep 7: Committing changes" -ForegroundColor Green
$commitMsg = "feat: quick templates on dashboard — CRUD, quick_add, modal, fixed category iteration, click/dblclick, N+1, period reuse"
$commitResult = git commit -m "$commitMsg"
if ($commitResult) {
    Write-Host "  ✓ Commit successful" -ForegroundColor Green
} else {
    Write-Host "  ✗ Commit failed" -ForegroundColor Red
}

# Step 8: Check git status and log
Write-Host "\nStep 8: Final verification" -ForegroundColor Green

Write-Host "\nGit status:"
$statusOutput = git status
Write-Host "$statusOutput"

Write-Host "\nLast 3 commits:"
$logOutput = git log --oneline -3
Write-Host "$logOutput"

Write-Host "\n=== All tasks completed ===" -ForegroundColor Cyan
