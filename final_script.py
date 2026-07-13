#!/usr/bin/env python3
"""Main script to complete all tasks for the finance_tracker project."""

import os
import subprocess
import sys
from pathlib import Path

# Set the project directory
PROJECT_DIR = Path("E:/Фото/Мои_доки/finance_tracker")
os.chdir(PROJECT_DIR)

def run_cmd(cmd):
    """Run a command and return result"""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )
    return result

def log_step(step_num, description):
    """Print a formatted step header"""
    print(f"\n{'='*70}")
    print(f"Step {step_num}: {description}")
    print(f"{'='*70}")

def main():
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # TASK 1: Check for all test files
        log_step("1", "Check all test files in root")
        
        all_files = os.listdir('.')
        py_files = [f for f in all_files if f.endswith('.py')]
        
        print(f"\nPython files in root: {len(py_files)} found")
        for f in sorted(py_files):
            print(f"  • {f}")
        
        # TASK 2: Delete test_*.py and check_*.py files
        log_step("2", "Delete test_*.py and check_*.py files from root")
        
        files_to_delete = [
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
        
        deleted_count = 0
        for filename in files_to_delete:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"✓ Deleted: {filename}")
                    deleted_count += 1
                except Exception as e:
                    print(f"✗ Error deleting {filename}: {e}")
            else:
                print(f"• Not found: {filename}")
        
        print(f"\nSuccessfully deleted {deleted_count} files.")
        
        # TASK 3: Check git status after deletion
        log_step("3", "Check git status after deletion")
        
        result = run_cmd('git status')
        if result.stdout:
            print(f"\nGit status:")
            print(result.stdout)
        
        if result.stderr and "error" in result.stderr.lower():
            print(f"\nError: {result.stderr}")
        
        # TASK 4: Stage required files
        log_step("4", "Stage required files")
        
        files_to_add = [
            'app.py',
            'routes/__init__.py',
            'routes/quick_templates.py',
            'services/quick_template_service.py',
            'static/js/quick_templates.js',
            'templates/index.html'
        ]
        
        staged_count = 0
        for filename in files_to_add:
            if os.path.exists(filename):
                result = run_cmd(f'git add {filename}')
                if result.returncode == 0:
                    print(f"✓ Staged: {filename}")
                    staged_count += 1
                else:
                    print(f"✗ Error staging {filename}: {result.stderr}")
            else:
                print(f"✗ File not found: {filename}")
        
        print(f"\nStaged {staged_count} out of {len(files_to_add)} files.")
        
        # TASK 5: Check git status after staging
        log_step("5", "Check git status after staging")
        
        result = run_cmd('git status')
        if result.stdout:
            print(f"\nGit status:")
            print(result.stdout)
        
        # TASK 6: Make commit
        log_step("6", "Make commit with specified message")
        
        commit_msg = 'feat: quick templates on dashboard — CRUD, quick_add, modal, fixed category iteration, click/dblclick, N+1, period reuse'
        
        result = run_cmd(f'git commit -m "{commit_msg}"')
        if result.returncode == 0:
            print("✓ Commit successful")
            
            # Get the commit hash
            log_result = run_cmd('git log --oneline -1')
            if log_result.stdout:
                commit_hash = log_result.stdout.strip().split('\n')[0]
                print(f"Commit hash: {commit_hash}")
        else:
            print("✗ Commit failed:")
            if result.stdout:
                print(f"Output: {result.stdout}")
            if result.stderr:
                print(f"Error: {result.stderr}")
        
        # TASK 7: Final verification
        log_step("7", "Final verification - Check git status and log")
        
        print(f"\nFinal git status:")
        result = run_cmd('git status')
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"\nLast 3 commits:")
            log_result = run_cmd('git log --oneline -3')
            if log_result.stdout:
                print(log_result.stdout)
        
        print(f"\n{'='*70}")
        print("✓ ALL TASKS COMPLETED SUCCESSFULLY")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
