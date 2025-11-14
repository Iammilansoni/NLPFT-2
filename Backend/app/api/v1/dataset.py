# app/api/v1/dataset.py
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Form
from fastapi.responses import FileResponse
from typing import Optional
from app.nlp.dataset_ingestor import ingest_csv_to_redis
from app.nlp.dataset_generator import get_dataset_generator
from app.core.config import DATASETS_DIR
from app.models.schemas import DatasetGenerateRequest, UploadResponse
from app.services.dataset_task_manager import get_task_manager
from app.core.logger import logger

router = APIRouter()
os.makedirs(DATASETS_DIR, exist_ok=True)

def process_upload_task(task_id: str, file_path: str, clear_existing: bool = False):
    """Background task to process uploaded CSV"""
    from datetime import datetime
    task_manager = get_task_manager()
    try:
        task_manager.update_task(task_id, status="running", message="Processing CSV file...")
        
        result = ingest_csv_to_redis(file_path, clear_existing=clear_existing)
        
        if result["success"]:
            task_manager.update_task(
                task_id,
                status="completed",
                message=f"Successfully ingested {result['count']} entries",
                completed_at=datetime.utcnow().isoformat(),
                statistics={
                    "total_apis": len(result.get("intents", [])),
                    "total_nl_variations": result["count"],
                    "avg_variations_per_api": result["count"] / max(len(result.get("intents", [])), 1),
                    "new_embeddings": result.get("new_embeddings", result["count"]),
                    "skipped_duplicates": result.get("skipped_duplicates", 0)
                },
                files={"csv": file_path}
            )
        else:
            task_manager.update_task(
                task_id,
                status="failed",
                message=f"Failed to ingest: {result.get('error', 'Unknown error')}",
                error=result.get("error", "Unknown error")
            )
    except Exception as e:
        logger.error(f"Error processing upload task {task_id}: {e}", exc_info=True)
        task_manager.update_task(
            task_id,
            status="failed",
            message=f"Error: {str(e)}",
            error=str(e)
        )

def process_generation_task(
    task_id: str,
    api_context: str,
    num_apis: int,
    nl_variations_per_api: int,
    use_llm: bool,
    clear_existing: bool
):
    """Background task to generate dataset from plain English query"""
    from datetime import datetime
    task_manager = get_task_manager()
    try:
        task_manager.update_task(task_id, status="running", message="Generating dataset with Gemini...")
        
        generator = get_dataset_generator()
        
        # Generate dataset from plain English query
        result = generator.generate_from_plain_english(
            plain_english_query=api_context or "Generate a diverse set of API test cases",
            api_context=api_context,
            num_apis=num_apis,
            nl_variations_per_api=nl_variations_per_api,
            use_gemini=use_llm
        )
        
        csv_path = result["paths"]["csv"]
        
        # Ingest to Redis
        task_manager.update_task(task_id, message="Storing embeddings in Redis...")
        ingest_result = ingest_csv_to_redis(csv_path, clear_existing=clear_existing)
        
        task_manager.update_task(
            task_id,
            status="completed",
            message=f"Dataset generated with {result['total_examples']} examples",
            completed_at=datetime.utcnow().isoformat(),
            dataset_id=result.get("dataset_id"),
            statistics={
                "total_apis": result["total_apis"],
                "total_nl_variations": result["total_examples"],
                "avg_variations_per_api": result["total_examples"] / max(result["total_apis"], 1),
                "redis_stored_count": ingest_result.get("count", 0),
                "redis_status": "stored" if ingest_result.get("success") else "failed"
            },
            files={
                "csv": csv_path,
                "json": result["paths"]["json"]
            }
        )
    except Exception as e:
        logger.error(f"Error processing generation task {task_id}: {e}", exc_info=True)
        task_manager.update_task(
            task_id,
            status="failed",
            message=f"Error: {str(e)}",
            error=str(e)
        )

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Accepts CSV and starts background ingestion to Redis.
    Returns immediate response with task_id for tracking.
    Existing embeddings are always preserved (never cleared).
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted.")
    
    # Validate file size (max 50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB"
        )
    
    # Create task
    task_manager = get_task_manager()
    task_id = task_manager.create_task()
    
    # Save file
    save_path = os.path.join(DATASETS_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(content)
    
    # Start background processing (always preserve existing embeddings)
    background_tasks.add_task(process_upload_task, task_id, save_path, False)
    
    return {
        "task_id": task_id,
        "message": "File uploaded. Processing started in background.",
        "file": save_path
    }

@router.post("/generate")
async def generate_dataset(
    request: DatasetGenerateRequest,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate dataset from plain English query using Gemini.
    Supports both new format (api_context) and legacy format (seed_query).
    """
    try:
        task_manager = get_task_manager()
        task_id = task_manager.create_task()
        
        # Determine if using new format or legacy format
        if request.api_context or (not request.seed_query and not request.api):
            # New format: generate from plain English query
            plain_english_query = request.api_context or "Generate a diverse set of API test cases"
            
            background_tasks.add_task(
                process_generation_task,
                task_id,
                plain_english_query,
                request.api_count or 10,
                request.nl_variations_per_api or 20,
                request.use_llm if request.use_llm is not None else True,
                False  # Always preserve existing embeddings
            )
            
            return {
                "task_id": task_id,
                "message": "Dataset generation started in background",
                "status": "running"
            }
        else:
            # Legacy format: generate for specific API
            generator = get_dataset_generator()
            
            result = generator.generate_dataset(
                intent=request.api or "unknown",
                num_examples=request.examples or 50,
                use_gemini=True,
                merge_existing=False
            )
            
            csv_path = result["paths"]["csv"]
            
            # Ingest to Redis in background (always preserve existing embeddings)
            background_tasks.add_task(
                ingest_csv_to_redis,
                csv_path,
                False  # Always preserve existing embeddings
            )
            
            filename = os.path.basename(csv_path)
            return {
                "task_id": task_id,
                "message": f"Dataset generated with {result['total_examples']} examples. Ingestion started.",
                "filename": filename
            }
    except Exception as e:
        logger.error(f"Error generating dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    """Get status of a dataset generation/upload task"""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@router.get("/preview/{task_id}")
def preview_dataset(task_id: str, limit: int = 100, offset: int = 0):
    """Preview dataset records from a completed task"""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    csv_path = task.get("files", {}).get("csv")
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    try:
        import pandas as pd
        import json
        df = pd.read_csv(csv_path)
        
        total = len(df)
        showing = min(limit, total - offset)
        
        # Map CSV columns to frontend interface format
        records = []
        for idx in range(offset, min(offset + limit, total)):
            try:
                row = df.iloc[idx]
                
                # Extract definition from response field if available
                definition = ""
                if 'response' in df.columns and pd.notna(row.get('response', None)):
                    try:
                        response_val = row['response']
                        if isinstance(response_val, str):
                            response_data = json.loads(response_val)
                        else:
                            response_data = response_val
                        if isinstance(response_data, dict):
                            definition = response_data.get('definition', '')
                        else:
                            definition = str(response_val)
                    except (json.JSONDecodeError, TypeError, AttributeError):
                        definition = str(row.get('response', ''))
                
                # Map to frontend interface
                record = {
                    "api": str(row.get('api', '')),
                    "endpoint": str(row.get('endpoint', '')),
                    "nl_input": str(row.get('query', '')),  # Map 'query' to 'nl_input'
                    "definition_of_api": definition,  # Extract from 'response'
                    "paraphrase_type": "user_uploaded" if 'paraphrase_type' not in df.columns else str(row.get('paraphrase_type', '')),
                    "embedding_model": "BAAI/bge-small-en-v1.5"
                }
                records.append(record)
            except Exception as row_error:
                logger.warning(f"Error processing row {idx}: {row_error}")
                continue
    except Exception as e:
        logger.error(f"Error reading CSV for preview: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading dataset file: {str(e)}")
    
    return {
        "task_id": task_id,
        "dataset_id": task.get("dataset_id"),
        "total_records": total,
        "showing": showing,
        "offset": offset,
        "limit": limit,
        "has_more": offset + showing < total,
        "records": records
    }

@router.get("/download/{task_id}/{format}")
def download_dataset(task_id: str, format: str):
    """Download dataset file from a completed task"""
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    file_path = task.get("files", {}).get(format)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    media_type = "text/csv" if format == "csv" else "application/json"
    filename = os.path.basename(file_path)
    
    return FileResponse(file_path, media_type=media_type, filename=filename)

@router.get("/list")
def list_datasets():
    """List all dataset generation tasks"""
    try:
        task_manager = get_task_manager()
        tasks = task_manager.list_tasks()
        return {"datasets": tasks}
    except Exception as e:
        logger.error(f"Error listing datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing datasets: {str(e)}")

@router.get("/download")
def download_dataset_by_filename(filename: str):
    """Download dataset by filename (legacy endpoint)"""
    path = os.path.join(DATASETS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="text/csv", filename=filename)


@router.get("/download-file/{filename}")
def download_dataset_file(filename: str):
    """
    Download dataset file by filename
    Used for downloading CSVs generated from queries
    """
    # Check in datasets directory first
    path = os.path.join(DATASETS_DIR, filename)
    
    # If not found, check in backend root directory (for csv_dataset.csv)
    if not os.path.exists(path):
        backend_dir = Path(__file__).parent.parent.parent
        path = backend_dir / filename
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on extension
    if filename.endswith('.csv'):
        media_type = "text/csv"
    elif filename.endswith('.json'):
        media_type = "application/json"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(str(path), media_type=media_type, filename=filename)