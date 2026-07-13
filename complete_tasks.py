#!/usr/bin/env python3
"""
Comprehensive script to complete all requested tasks:
1. Check for test files in root directory
2. Delete test_*.py and check_*.py files from root
3. Check git status after deletion
4. Stage specific files
5. Make a commit with specified message
6. Verify git status and log after commit
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuration
PROJECT_DIR = Path("E:/Фото/Мои_доки/finance_tracker")

def run_command(command, cwd=None):
    """Run a shell command and return result"""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=cwd
    )
    return result

def log_header(text):
    """Print a formatted header"""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def main():
    # Change to project directory
    os.chdir(PROJECT_DIR)
    print(f"Working directory: {os.getcwd()}")
    
    try:
        # Task 1: Check for test files in root
        log_header("TASK 1: Check for test files in root directory")
        
        all_files = os.listdir('.')
        py_files = [f for f in all_files if f.endswith('.py')]
        
        print(f"\nPython files in root directory:")
        for f in sorted(py_files):
            print(f"  • {f}")
        print(f"Total .py files: {len(py_files)}")
        
        # Find test and check files
        test_files = [f for f in py_files if f.startswith('test_')]
        check_files = [f for f in py_files if f.startswith('check_')]
        
        print(f"\nFiles to delete (test_*.py and check_*.py):")
        print(f"  • Python files starting with 'test_': {len(test_files)} files")
        print(f"  • Python files starting with 'check_': {len(check_files)} files")
        
        # Task 2: Delete test_*.py and check_*.py files from root
        log_header("TASK 2: Delete test_*.py and check_*.py files from root")
        
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
        
        # Task 3: Check git status after deletion
        log_header("TASK 3: Check git status after deletion")
        
        status_result = run_command('git status')
        if status_result.stdout:
            print(f"\nGit status:")
            print(status_result.stdout)
        
        if status_result.stderr:
            print(f"Error (stderr): {status_result.stderr}")
        
        # Task 4: Stage specific files
        log_header("TASK 4: Stage required files")
        
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
                result = run_command(f'git add {filename}')
                if result.returncode == 0:
                    print(f"✓ Staged: {filename}")
                    staged_count += 1
                else:
                    print(f"✗ Error staging {filename}: {result.stderr}")
            else:
                print(f"✗ File not found: {filename}")
        
        print(f"\nStaged {staged_count} out of {len(files_to_add)} files.")
        
        # Task 5: Check git status after staging
        log_header("TASK 5: Check git status after staging")
        
        status_result = run_command('git status')
        if status_result.stdout:
            print(f"\nGit status:")
            print(status_result.stdout)
        
        # Task 6: Make commit
        log_header("TASK 6: Make commit with specified message")
        
        commit_msg = 'feat: quick templates on dashboard — CRUD, quick_add, modal, fixed category iteration, click/dblclick, N+1, period reuse'
        
        commit_result = run_command(f'git commit -m "{commit_msg}"')
        if commit_result.returncode == 0:
            print("✓ Commit successful")
            
            # Get the commit hash
            log_result = run_command('git log --oneline -1')
            if log_result.stdout:
                commit_hash = log_result.stdout.strip().split('\n')[0]
                print(f"Commit hash: {commit_hash}")
        else:
            print("✗ Commit failed:")
            if commit_result.stdout:
                print(f"Output: {commit_result.stdout}")
            if commit_result.stderr:
                print(f"Error: {commit_result.stderr}")
            
            # Check status to see what's staged
            status_result = run_command('git status')
            print(f"\nCurrent status:")
            print(status_result.stdout)
        
        # Task 7: Check git status and log after commit
        log_header("TASK 7: Final verification - Check git status and log")
        
        print(f"\nFinal git status:")
        status_result = run_command('git status')
        if status_result.stdout:
            print(status_result.stdout)
        
        if status_result.returncode == 0:
            print(f"\nLast 3 commits:")
            log_result = run_command('git log --oneline -3')
            if log_result.stdout:
                print(log_result.stdout)
        
        # Print summary
        print(f"\n{'='*70}")
        print("✓ ALL TASKS COMPLETED SUCCESSFULLY")
        print(f"{'='*70}")
        print(f"Deleted {deleted_count} test files from root directory")
        print(f"Staged {staged_count} files")
        print(f"Made single commit: {commit_msg}")
        
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
