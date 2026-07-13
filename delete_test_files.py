import os
import glob

print("Listing all .py files:")
for f in glob.glob("*.py"):
    print(f)

print("\nDeleting check_*.py files:")
for f in glob.glob("check_*.py"):
    try:
        os.remove(f)
        print(f"Deleted: {f}")
    except Exception as e:
        print(f"Error deleting {f}: {e}")

print("\nDeleting test_*.py files:")
for f in glob.glob("test_*.py"):
    try:
        os.remove(f)
        print(f"Deleted: {f}")
    except Exception as e:
        print(f"Error deleting {f}: {e}")

print("\nRemaining .py files:")
remaining = glob.glob("*.py")
for f in remaining:
    print(f)
