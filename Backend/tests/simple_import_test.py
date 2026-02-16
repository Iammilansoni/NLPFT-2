import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
