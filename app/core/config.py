from fastapi import FastAPI

class Settings:
    app_name = "NLPForge API"
    app_version = "0.1.0"
    host = "127.0.0.1"
    port = 8000
    workers = 1
    debug = True
    log_level = "info"
    environment = "development"
    mongodb_url = "mongodb://localhost:27017"  # Default MongoDB URL
    mongodb_database = "nlpforge"  # Default MongoDB database name

settings = Settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

