from pathlib import Path

class Settings:
    app_name = "NLPForge API"
    app_version = "0.1.0"
    host = "127.0.0.1"
    port = 8000
    workers = 1
    debug = True
    log_level = "info"
    environment = "development"
    mongodb_url = "mongodb://localhost:27017"
    mongodb_database = "nlpforge"
    
    # Storage paths - NLPForge-Tester/storage
    @property
    def project_root(self) -> Path:
        """Get the NLPForge-Tester project root directory."""
        # Navigate from app/core/config.py to NLPForge-Tester/
        current_file = Path(__file__).resolve()  # app/core/config.py
        app_dir = current_file.parent.parent      # app/
        project_root = app_dir.parent             # NLPForge-Tester/
        return project_root
    
    @property
    def storage_path(self) -> Path:
        """Get the storage directory path: NLPForge-Tester/storage"""
        return self.project_root / "storage"
    
    @property
    def function_dictionary_path(self) -> Path:
        """Get the function dictionary file path: NLPForge-Tester/storage/function_dictionary.json"""
        return self.storage_path / "function_dictionary.json"
    
    @property
    def feedback_db_path(self) -> Path:
        """Get the feedback database file path: NLPForge-Tester/storage/feedback.db"""
        return self.storage_path / "feedback.db"
    
    @property
    def faiss_index_path(self) -> Path:
        """Get the FAISS index directory path: NLPForge-Tester/storage/faiss_index"""
        return self.storage_path / "faiss_index"
    
    def ensure_storage_directories(self):
        """Ensure all storage directories exist."""
        self.storage_path.mkdir(exist_ok=True)
        self.faiss_index_path.mkdir(exist_ok=True)
        
        # Create __init__.py in storage if it doesn't exist
        storage_init = self.storage_path / "__init__.py"
        if not storage_init.exists():
            storage_init.touch()

settings = Settings()

