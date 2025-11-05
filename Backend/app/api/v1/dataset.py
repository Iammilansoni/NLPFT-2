# app/api/v1/dataset.py
import os
import shutil
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import FileResponse
from typing import Optional
from nlp.dataset_ingestor import ingest_csv_to_redis
from nlp.dataset_generator import generate_dataset_from_prompt
from core.config import DATASETS_DIR

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

    # Run ingestion in background to avoid blocking the request
    if background_tasks is not None:
        background_tasks.add_task(ingest_csv_to_redis, save_path)
        return {"message": "File uploaded. Ingestion started in background.", "file": save_path}
    else:
        # fallback synchronous
        result = ingest_csv_to_redis(save_path)
        return {"message": "File ingested", "result": result}

@router.post("/generate")
async def generate_dataset(
    seed_prompt: str = Form(...),
    examples: Optional[int] = Form(50),
    api_name: Optional[str] = Form("login"),
    endpoint: Optional[str] = Form("<base_url>/api/login"),
    background_tasks: BackgroundTasks = None
):
    """
    Generate dataset via LLM and ingest it. If BackgroundTasks provided,
    ingestion runs in background and CSV path is returned immediately.
    """
    res = generate_dataset_from_prompt(seed_prompt, examples=int(examples), api_name=api_name, endpoint=endpoint)
    csv_path = res["csv_path"]
    # If ingestion done inside generator already, res includes ingestion summary.
    return {"message": "Dataset generated and ingested", "csv_path": csv_path, "ingestion": res.get("ingestion")}

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
