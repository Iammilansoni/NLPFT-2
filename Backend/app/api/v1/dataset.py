# app/api/v1/dataset.py
import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import FileResponse
from typing import Optional
from app.nlp.dataset_ingestor import ingest_csv_to_redis
from app.nlp.dataset_generator import generate_dataset_from_prompt
from app.core.config import DATASETS_DIR
from app.models.schemas import DatasetGenerateRequest, UploadResponse

router = APIRouter()
os.makedirs(DATASETS_DIR, exist_ok=True)

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Accepts CSV and starts background ingestion to Redis.
    Returns immediate response with file path and ingestion queued.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted.")
    save_path = os.path.join(DATASETS_DIR, file.filename)
    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    if background_tasks is not None:
        background_tasks.add_task(ingest_csv_to_redis, save_path)
        return {"message": "File uploaded. Ingestion started in background.", "file": save_path}
    else:
        result = ingest_csv_to_redis(save_path)
        return {"message": "File ingested", "result": result}

@router.post("/generate", response_model=UploadResponse)
async def generate_dataset(request: DatasetGenerateRequest, background_tasks: BackgroundTasks = BackgroundTasks()):
    try:
        # Use user-provided api and endpoint
        res = generate_dataset_from_prompt(
            seed_prompt=request.seed_query,
            api_name=request.api,
            endpoint=request.endpoint,
            num_examples=request.examples
        )
        csv_path = res["csv_path"]
        if not res.get("ingestion"):
            background_tasks.add_task(ingest_csv_to_redis, csv_path)
        filename = os.path.basename(csv_path)
        return UploadResponse(message="Dataset generated and ingestion started.", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
def list_datasets():
    files = [f for f in os.listdir(DATASETS_DIR) if f.endswith(".csv")]
    return {"datasets": files}

@router.get("/download")
def download_dataset(filename: str):
    path = os.path.join(DATASETS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="text/csv", filename=filename)