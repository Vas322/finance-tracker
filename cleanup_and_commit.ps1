# PowerShell script to complete all tasks
# Save as C:\\photo\\Мои_доки\\finance_tracker\\cleanup_and_commit.ps1

$ProjectDir = "E:\\Фото\\Мои_доки\\finance_tracker"
Set-Location $ProjectDir

Write-Host "Working in: $(Get-Location)" -ForegroundColor Green
Write-Host "=== Task 1: List all .py files ===" -ForegroundColor Yellow

$allPyFiles = Get-ChildItem -Name "*.py"
$allPyFiles | ForEach-Object { Write-Host "  $($_.Name)" }
Write-Host "Total: $($allPyFiles.Count)"

Write-Host "\n=== Task 2: Delete test_*.py and check_*.py files ===" -ForegroundColor Yellow

$filesToDelete = @(
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

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        try {
            Remove-Item $file -Force
            Write-Host "✓ Deleted: $file" -ForegroundColor Green
        } catch {
            Write-Host "✗ Error deleting $file`: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "• Not found: $file" -ForegroundColor Yellow
    }
}

Write-Host "\n=== Task 3: Check git status after deletion ===" -ForegroundColor Yellow

$statusOutput = git status
Write-Host "$statusOutput"

Write-Host "\n=== Task 4: Stage required files ===" -ForegroundColor Yellow

$filesToStage = @(
    "app.py",
    "routes/__init__.py",
    "routes/quick_templates.py",
    "services/quick_template_service.py",
    "static/js/quick_templates.js",
    "templates/index.html"
)

foreach ($file in $filesToStage) {
    if (Test-Path $file) {
        git add $file
        Write-Host "✓ Staged: $file" -ForegroundColor Green
    } else {
        Write-Host "✗ File not found: $file" -ForegroundColor Red
    }
}

Write-Host "\n=== Task 5: Check git status after staging ===" -ForegroundColor Yellow

$statusOutput = git status
Write-Host "$statusOutput"

Write-Host "\n=== Task 6: Commit changes ===" -ForegroundColor Yellow

$commitMsg = "feat: quick templates on dashboard — CRUD, quick_add, modal, fixed category iteration, click/dblclick, N+1, period reuse"

$commitResult = git commit -m "$commitMsg"
if ($commitResult) {
    Write-Host "✓ Commit successful" -ForegroundColor Green
} else {
    Write-Host "✗ Commit failed" -ForegroundColor Red
    git status
}

Write-Host "\n=== Task 7: Check git status and log ===" -ForegroundColor Yellow

$statusOutput = git status
Write-Host "Git status:"
Write-Host "$statusOutput"

Write-Host "\nLast 3 commits:"
$logOutput = git log --oneline -3
Write-Host "$logOutput"

Write-Host "\n=== All tasks completed ===" -ForegroundColor Green
