import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.nlp.dataset_generator import EnterpriseDatasetGenerator
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
