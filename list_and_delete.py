import os
import glob

# Set current directory
project_dir = "E:/Фото/Мои_доки/finance_tracker"
os.chdir(project_dir)

print(f"Working in: {project_dir}")
print(f"Files in root before deletion:")
for f in sorted(os.listdir('.')):
    print(f"  {f}")

# Find and delete test_*.py and check_*.py files
test_files = []
check_files = []

for f in os.listdir('.'):
    if f.startswith('test_') and f.endswith('.py'):
        test_files.append(f)
    elif f.startswith('check_') and f.endswith('.py'):
        check_files.append(f)

print(f"\nFound test_*.py files: {test_files}")
print(f"Found check_*.py files: {check_files}")

# Delete files
deleted_count = 0
for f in test_files + check_files:
    try:
        os.remove(f)
        print(f"✓ Deleted: {f}")
        deleted_count += 1
    except Exception as e:
        print(f"✗ Error deleting {f}: {e}")

print(f"\nTotal files deleted: {deleted_count}")

# Check remaining files
print("\nRemaining files in root:")
remaining = sorted([f for f in os.listdir('.') if os.path.isfile(f)])
for f in remaining:
    print(f"  {f}")
