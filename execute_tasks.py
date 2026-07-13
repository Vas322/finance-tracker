#!/usr/bin/env python3
"""
Script to perform all requested tasks:
1. Check for test files in root
2. Delete test_*.py and check_*.py files from root (not tests/)
3. Check git status after deletion
4. Stage specific files
5. Make a commit
6. Verify the result
"""

import os
import subprocess
import sys

# Set project directory
project_dir = "E:/Фото/Мои_доки/finance_tracker"
os.chdir(project_dir)

def run_git_command(command, cwd=None):
    """Run a git command and return output"""
    result = subprocess.run(
        command, 
        shell=True, 
        capture_output=True, 
        text=True,
        cwd=cwd
    )
    return result

def log_step(step_num, description):
    """Log a step to console"""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print(f"{'='*60}")

def main():
    print(f"Working directory: {os.getcwd()}")
    print("Running all tasks...")
    
    # Step 1: Check for test files in root
    log_step("1", "Check for test files in root directory")
    
    # List all .py files in root
    all_files = [f for f in os.listdir('.') if f.endswith('.py')]
    print(f"\nAll .py files in root:")
    for f in sorted(all_files):
        print(f"  {f}")
    
    print(f"\nTotal .py files: {len(all_files)}")
    
    # Step 2: Delete test_*.py and check_*.py files from root
    log_step("2", "Delete test_*.py and check_*.py files from root")
    
    target_files = [
        'check_import.py',
        'check_quick_templates.py',
        'test_env.txt',
        'test_full_import.py',
        'test_import.py',
        'test_import_app.py',
        'test_import_final.py',
        'test_import_simple.py',
        'test_runner.py',
        'test_script.py',
        'test_simple.py',
        'test_startup.py'
    ]
    
    deleted_files = []
    for f in target_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                deleted_files.append(f)
                print(f"✓ Deleted: {f}")
            except Exception as e:
                print(f"✗ Error deleting {f}: {e}")
        else:
            print(f"• Not found: {f}")
    
    print(f"\nSuccessfully deleted {len(deleted_files)} files: {deleted_files}")
    
    # Step 3: Check git status after deletion
    log_step("3", "Check git status after deletion")
    
    status_result = run_git_command('git status')
    print(f"\nGit status output:")
    print(status_result.stdout)
    if status_result.returncode != 0:
        print(f"Error: {status_result.stderr}")
    
    # Step 4: Stage specific files
    log_step("4", "Stage required files")
    
    files_to_add = [
        'app.py',
        'routes/__init__.py',
        'routes/quick_templates.py',
        'services/quick_template_service.py',
        'static/js/quick_templates.js',
        'templates/index.html'
    ]
    
    for f in files_to_add:
        if os.path.exists(f):
            result = run_git_command(f'git add {f}')
            if result.returncode == 0:
                print(f"✓ Staged: {f}")
            else:
                print(f"✗ Error staging {f}: {result.stderr}")
        else:
            print(f"✗ File not found: {f}")
    
    # Step 5: Make a commit
    log_step("5", "Commit changes")
    
    commit_msg = 'feat: quick templates on dashboard — CRUD, quick_add, modal, fixed category iteration, click/dblclick, N+1, period reuse'
    
    commit_result = run_git_command(f'git commit -m "{commit_msg}"')
    if commit_result.returncode == 0:
        print("✓ Commit successful")
    else:
        print("✗ Commit failed:")
        print(commit_result.stdout)
        print(commit_result.stderr)
    
    # Step 6: Verify git status and log
    log_step("6", "Verify git status and commit log")
    
    print("\nGit status:")
    status_result = run_git_command('git status')
    print(status_result.stdout)
    
    if status_result.returncode == 0:
        print("\nLast 3 commits:")
        log_result = run_git_command('git log --oneline -3')
        print(log_result.stdout)
    
    print("\n=== All tasks completed successfully ===")

if __name__ == "__main__":
    main()
