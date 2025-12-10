"""
Datasets API - Consolidated endpoint for dataset lifecycle management
Handles: generation, upload, embedding, search, and management

Replaces: dataset.py + dataset_embeddings.py

🔒 KEY DESIGN: ONE EMBEDDING MODEL PER DATASET
- Once embedded, a dataset is locked to that model
- Search with different model returns MODEL_MISMATCH error
- Re-embedding requires explicit user action via POST /datasets/{dataset_id}/reembed
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Depends, status, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
import uuid

from app.core.postgres import get_db
from app.api.v1.auth import get_current_user
from app.core.config import DATASETS_DIR
from app.core.logger import logger
from app.services.audit_service import get_audit_service
from app.models.database_models import User, UserSettings, Template, Metadata, Parameter, ExpectedResponse, Dataset
from app.nlp.dataset_ingestor import ingest_csv_to_redis
from app.nlp.dataset_generator import get_enterprise_dataset_generator
from app.services.dataset_task_manager import get_task_manager
from app.services.embedding_service import get_enhanced_embedding_service
from app.core.models_config import (
    get_all_embedding_models,
    get_all_llms,
    get_embedding_model_info,
    EMBEDDING_TOOLTIP,
    MODEL_MISMATCH_WARNING
)
from app.schemas.embedding_schemas import (
    ReembedDatasetRequest,
    ReembedDatasetResponse,
    SearchDatasetRequest,
    SearchDatasetResponse,
    DatasetEmbeddingStatus,
    EmbeddingStatus,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])
os.makedirs(DATASETS_DIR, exist_ok=True)


# ============= SCHEMAS =============

class DatasetGenerateRequest(BaseModel):
    """
    Request to generate enterprise dataset from approved template
    
    🎯 NEW: Template-aware generation with high variation
    """
    # REQUIRED: Approved template ID
    template_id: str = Field(..., description="UUID of approved template (REQUIRED)")
    
    # Dataset generation parameters
    num_examples: Optional[int] = Field(
        default=None,
        ge=10,
        le=1000,
        description="Number of test cases to generate (10-1000). If not provided, inferred from query or defaults to 100."
    )
    
    # User prompt for specific scenarios
    user_prompt: str = Field(
        ...,
        description="User instructions for LLM (e.g., 'Generate edge cases with pilot disabled and low SNR conditions')"
    )
    
    # Focus areas for targeted generation
    focus_areas: Optional[List[str]] = Field(
        default=None,
        description="Specific areas to focus on (e.g., ['security', 'performance', 'error_handling'])"
    )
    
    # Scenario distribution override
    scenario_distribution: Optional[Dict[str, float]] = Field(
        default=None,
        description="Custom distribution: {'valid': 0.7, 'edge': 0.2, 'extreme': 0.1}"
    )
    
    # Legacy support (deprecated)
    api_context: Optional[str] = None
    api_count: Optional[int] = None
    nl_variations_per_api: Optional[int] = None
    use_llm: Optional[bool] = True
    seed_query: Optional[str] = None
    api: Optional[str] = None
    examples: Optional[int] = None


class EmbedDatasetRequest(BaseModel):
    """Request to embed a dataset"""
    dataset_id: str
    model: Optional[str] = None
    batch_size: Optional[int] = 32


class EmbedDatasetResponse(BaseModel):
    """Response for embedding request"""
    task_id: str
    status: str
    message: str
    model: str
    is_reembed: bool


class SearchDatasetRequest(BaseModel):
    """Request to search dataset vectors"""
    dataset_id: str
    query: str
    model: str  # REQUIRED: Must match dataset's embedded_with_model
    top_k: Optional[int] = 5


class SearchSimilarTestCasesRequest(BaseModel):
    """Request to search similar test cases"""
    template_id: str = Field(..., description="Template ID to search within")
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results")


class EmbeddingStatusResponse(BaseModel):
    """Response for embedding status"""
    task_id: str
    status: str
    message: str
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    statistics: Optional[dict] = None
    error: Optional[str] = None


# ============= BACKGROUND TASKS =============

def process_upload_task(task_id: str, file_path: str, clear_existing: bool = False):
    """Background task to process uploaded CSV"""
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
        task_manager.update_task(task_id, status="failed", message=str(e), error=str(e))


# Note: Legacy process_generation_task removed - use template-based generation


# ============= DATASET GENERATION & UPLOAD =============

@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload CSV dataset and start background ingestion to Redis
    Returns task_id for tracking progress
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
    task_manager = get_task_manager()
    task_id = task_manager.create_task()
    
    save_path = os.path.join(DATASETS_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(content)
    
    background_tasks.add_task(process_upload_task, task_id, save_path, False)
    
    return {
        "task_id": task_id,
        "message": "File uploaded. Processing started in background.",
        "file": save_path
    }


@router.post("/generate")
# Rate limiting temporarily disabled - use app-level limiter instead
async def generate_dataset(
    request: Request,
    dataset_request: DatasetGenerateRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate dataset from plain English query using LLM
    
    🔒 NEW REQUIREMENT: Template must be 'approved' before dataset generation
    ⏱️ RATE LIMIT: 10 generations per minute per IP to prevent API abuse
    
    Workflow:
    1. If template_id provided → Check approval status
    2. If not approved → Return 403 Forbidden
    3. If approved → Proceed with dataset generation
    
    Supports both new format (api_context + template_id) and legacy format (seed_query)
    """
    try:
        # ============== TEMPLATE APPROVAL CHECK ==============
        if dataset_request.template_id:
            # Query template and metadata (ENFORCE MULTI-TENANT ISOLATION)
            result = await db.execute(
                select(Template).where(
                    Template.t_id == dataset_request.template_id,
                    Template.u_id == current_user.u_id  # 🔒 Prevent cross-tenant access
                )
            )
            template = result.scalar_one_or_none()
            if not template:
                raise HTTPException(
                    status_code=404,
                    detail=f"Template {dataset_request.template_id} not found or you don't have permission to access it"
                )
            
            # Check metadata approval status
            metadata_result = await db.execute(
                select(Metadata).where(Metadata.t_id == dataset_request.template_id)
            )
            metadata = metadata_result.scalar_one_or_none()
            if not metadata:
                raise HTTPException(
                    status_code=500,
                    detail=f"Metadata missing for template {dataset_request.template_id}"
                )
            
            # Enforce approval requirement
            if metadata.status != "approved":
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Template Not Approved",
                        "message": f"Dataset generation is only allowed for approved templates. Current status: '{metadata.status}'",
                        "template_id": str(dataset_request.template_id),
                        "template_name": template.name,
                        "current_status": metadata.status,
                        "required_status": "approved",
                        "workflow": "Submit template for review → Expert approves → Dataset generation enabled",
                        "actions": {
                            "draft": "Submit for review using POST /templates/{id}/submit-review",
                            "review": "Wait for expert approval or contact administrator",
                            "rejected": "Fix issues and resubmit for review"
                        }
                    }
                )
            
            logger.info(f"✅ Template {dataset_request.template_id} approved by {metadata.approved_by} at {metadata.approved_at}")
            
            # Create task for tracking
            task_manager = get_task_manager()
            task_id = task_manager.create_task()
            task_manager.update_task(task_id, status="running", message="Starting dataset generation...", progress=0)
            
            # ============== ENTERPRISE DATASET GENERATION ==============
            # Load full template data with all related information
            task_manager.update_progress(task_id, 5, "Loading template data...", "load_template")
            
            params_result = await db.execute(
                select(Parameter).where(Parameter.t_id == dataset_request.template_id)
            )
            parameters = params_result.scalars().all()
            exp_resp_result = await db.execute(
                select(ExpectedResponse).where(ExpectedResponse.t_id == dataset_request.template_id)
            )
            expected_responses = exp_resp_result.scalars().all()
            
            # Build comprehensive template data dictionary
            template_data = {
                "id": str(template.t_id),
                "name": template.api_name,
                "description": template.description,
                "base_url": template.base_url,
                "endpoint": template.endpoint,
                "method": template.method,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "required": p.required,
                        "example": p.example,
                        "description": p.description
                    }
                    for p in parameters
                ],
                "sample_requests": template.sample_requests or [],
                "sample_responses": template.sample_responses or [],
                "json_schema": template.json_schema or {},
                "response_schema": template.response_schema or {},
                "domain_tags": template.domain_tags or [],
                "security_classification": metadata.security_classification or "internal",
                "auth_config": template.auth_config or {},
                "headers": template.headers or {},
                "rate_limit": template.rate_limit or {},
                "assertions": template.assertions or []
            }
            
            # Use enterprise generator
            enterprise_generator = get_enterprise_dataset_generator()
            
            # Generate dataset with full template context (pass task_id for progress tracking)
            result = await enterprise_generator.generate_dataset_from_template(
                template_data=template_data,
                num_examples=dataset_request.num_examples,
                user_prompt=dataset_request.user_prompt,
                focus_areas=dataset_request.focus_areas,
                scenario_distribution=dataset_request.scenario_distribution,
                task_id=task_id
            )
            
            if not result.get("success"):
                task_manager.update_task(task_id, status="failed", message=f"Dataset generation failed: {result.get('error')}", progress=0)
                raise HTTPException(
                    status_code=500,
                    detail=f"Dataset generation failed: {result.get('error')}"
                )
            
            # Start automatic embedding after generation
            csv_path = result["paths"]["csv"]
            
            # Start automatic embedding in background (optional - Celery may not be running)
            embedding_task_id = None
            try:
                from app.services.embedding_service import create_embedding_async
                
                # Dispatch to Celery worker
                # Note: We pass IDs as strings for JSON serialization
                celery_task = create_embedding_async.delay(
                    csv_path=csv_path,
                    user_id=str(current_user.u_id),
                    template_id=str(dataset_request.template_id)
                )
                embedding_task_id = celery_task.id
                logger.info(f"🚀 Started automatic embedding: task_id={embedding_task_id}")
            except Exception as celery_error:
                logger.warning(f"⚠️ Celery embedding task not dispatched (worker may not be running): {celery_error}")
                embedding_task_id = "skipped"
            
            # 📝 Audit log
            audit_service = get_audit_service()
            await audit_service.log_dataset_generated(
                db=db,
                user_id=current_user.u_id,
                template_id=UUID(dataset_request.template_id),
                dataset_path=csv_path,
                num_examples=result['total_generated'],
                metadata_={
                    "template_name": result["template_name"],
                    "user_prompt": dataset_request.user_prompt[:200],
                    "scenario_distribution": result["scenario_distribution"],
                    "embedding_task_id": embedding_task_id
                },
                request=request
            )
            
            # ✅ Mark task as completed
            task_manager.update_task(
                task_id, 
                status="completed", 
                message=f"✅ Generated {result['total_generated']} test cases",
                result={
                    "total_generated": result["total_generated"],
                    "csv_path": csv_path
                },
                files={
                    "csv": csv_path,
                    "json": result["paths"]["json"]
                }
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "embedding_task_id": embedding_task_id,
                "message": f"✅ Enterprise dataset generated with {result['total_generated']} test cases. Automatic embedding started.",
                "template_name": result["template_name"],
                "template_id": result["template_id"],
                "total_generated": result["total_generated"],
                "requested": result["requested"],
                "scenario_distribution": result["scenario_distribution"],
                "category_distribution": result["category_distribution"],
                "csv_path": csv_path,
                "json_path": result["paths"]["json"],
                "csv_preview": result["csv_preview"],
                "user_prompt": result["user_prompt"],
                "focus_areas": result["focus_areas"],
                "timestamp": result["timestamp"],
                "download_url": f"/v1/datasets/download/{os.path.basename(csv_path)}"
            }
        
        # ============== LEGACY SUPPORT (DISABLED - REQUIRES template_id) ==============
        # Legacy paths are disabled because they relied on deprecated generator functions
        # Use template_id for all dataset generation
        else:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Template ID Required",
                    "message": "Dataset generation requires a template_id. Legacy generation is no longer supported.",
                    "required_field": "template_id",
                    "workflow": "1. Create a template → 2. Submit for review → 3. Get approved → 4. Generate dataset with template_id"
                }
            )
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error generating dataset: {e}", exc_info=True)
        # Try to update task status if task was created
        try:
            task_manager = get_task_manager()
            if 'task_id' in locals():
                task_manager.update_task(task_id, status="failed", message=str(e), error=str(e))
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
@router.get("/list")
def list_datasets():
    """List all dataset generation tasks
    
    Available at both:
    - GET /api/v1/datasets/
    - GET /api/v1/datasets/list
    """
    try:
        task_manager = get_task_manager()
        tasks = task_manager.list_tasks()
        return {"datasets": tasks}
    except Exception as e:
        logger.error(f"Error listing datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
def get_task_status(task_id: str):
    """
    Get status of a dataset generation/upload task
    
    Returns progress information including:
    - status: pending, running, completed, failed
    - progress: 0-100 percentage
    - message: current status message
    - current_step: what's happening now
    - steps: history of completed steps
    """
    task_manager = get_task_manager()
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task.get("task_id"),
        "status": task.get("status"),
        "progress": task.get("progress", 0),
        "message": task.get("message", ""),
        "current_step": task.get("current_step", ""),
        "steps": task.get("steps", []),
        "created_at": task.get("created_at"),
        "completed_at": task.get("completed_at"),
        "statistics": task.get("statistics"),
        "files": task.get("files"),
        "error": task.get("error")
    }


# ============= DATASET EMBEDDING =============
# NOTE: These endpoints are temporarily disabled due to missing Dataset model
# Embedding happens automatically after dataset generation via auto_embed_generated_dataset()

# @router.post("/embed", response_model=EmbedDatasetResponse)
# async def embed_dataset(
#     request: EmbedDatasetRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Start background job to embed all rows in a dataset
#     
#     NOTE: Currently disabled - embedding happens automatically after generation
#     """
#     raise HTTPException(
#         status_code=501,
#         detail="Manual embedding endpoint not implemented. Embedding happens automatically after dataset generation."
#     )


# @router.get("/embed/status/{task_id}", response_model=EmbeddingStatusResponse)
# async def get_embedding_status(
#     task_id: str,
#     current_user: User = Depends(get_current_user)
# ):
#     """Get status of embedding job"""
#     raise HTTPException(
#         status_code=501,
#         detail="Embedding status endpoint not implemented. Check dataset generation task status instead."
#     )


# ============= DATASET SEARCH =============
# NOTE: Search functionality temporarily disabled - will be re-enabled with proper Dataset model

# @router.post("/search")
# async def search_dataset(
#     request: SearchDatasetRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Search vectors in a dataset using semantic similarity
#     
#     NOTE: Currently disabled - will be re-enabled with proper Dataset model
#     """
#     raise HTTPException(
#         status_code=501,
#         detail="Search endpoint not implemented yet."
#     )


# ============= DATASET INFO & MANAGEMENT =============
# NOTE: Info endpoint temporarily disabled - will be re-enabled with proper Dataset model

# @router.get("/{dataset_id}/info")
# async def get_dataset_info(
#     dataset_id: str,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get dataset embedding information"""
#     raise HTTPException(
#         status_code=501,
#         detail="Dataset info endpoint not implemented yet."
#     )


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
        
        records = []
        for idx in range(offset, min(offset + limit, total)):
            try:
                row = df.iloc[idx]
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
                
                record = {
                    "api": str(row.get('api', '')),
                    "endpoint": str(row.get('endpoint', '')),
                    "nl_input": str(row.get('query', '')),
                    "definition_of_api": definition,
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


@router.get("/download-file/{filename}")
def download_dataset_file(filename: str):
    """Download dataset file by filename"""
    path = os.path.join(DATASETS_DIR, filename)
    
    if not os.path.exists(path):
        backend_dir = Path(__file__).parent.parent.parent
        path = backend_dir / filename
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="File not found")
    
    if filename.endswith('.csv'):
        media_type = "text/csv"
    elif filename.endswith('.json'):
        media_type = "application/json"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(str(path), media_type=media_type, filename=filename)


@router.get("/embeddings/stats/{template_id}")
async def get_embedding_statistics(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get embedding statistics for a template
    
    Returns:
    - Total number of embedded vectors
    - Embedding model used
    - Dimension
    - HNSW index name
    - Redis namespace
    """
    from app.services.embedding_service import get_enhanced_embedding_service
    
    embedding_service = get_enhanced_embedding_service()
    stats = embedding_service.get_embedding_stats(
        user_id=current_user.u_id,
        template_id=UUID(template_id)
    )
    
    return {
        "template_id": template_id,
        "user_id": str(current_user.u_id),
        "embedding_stats": stats
    }


@router.post("/embeddings/search")
async def search_similar_test_cases(
    request: SearchSimilarTestCasesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for similar test cases using vector similarity
    
    Uses HNSW index for high-speed semantic search.
    Returns test cases most similar to the query.
    
    🔒 NOTE: Use POST /datasets/{dataset_id}/search for model-validated search
    """
    from app.services.embedding_service import get_enhanced_embedding_service
    
    embedding_service = get_enhanced_embedding_service()
    
    # Get dataset for the template (legacy support)
    dataset_result = await db.execute(
        select(Dataset).where(
            Dataset.t_id == UUID(request.template_id),
            Dataset.u_id == current_user.u_id
        )
    )
    dataset = dataset_result.scalar_one_or_none()
    
    if dataset:
        # Use new dataset-based search with model validation
        results = await embedding_service.search_similar_test_cases(
            user_id=current_user.u_id,
            dataset_id=dataset.dataset_id,
            query=request.query,
            top_k=request.top_k,
            db=db
        )
        return results
    else:
        # Legacy: No dataset found, return empty results
        return {
            "query": request.query,
            "template_id": request.template_id,
            "total_results": 0,
            "results": [],
            "warning": "No dataset found for this template. Generate a dataset first."
        }


@router.get("/preview/{filename}")
def preview_dataset(
    filename: str,
    limit: int = Query(default=10, ge=1, le=100, description="Number of rows to preview")
):
    """
    Preview CSV dataset (first N rows)
    
    Returns JSON with:
    - rows: First N rows of CSV
    - total_rows: Total number of rows in CSV
    - columns: List of column names
    - statistics: Distribution statistics (scenario_type, test_category)
    """
    path = os.path.join(DATASETS_DIR, filename)
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset file not found")
    
    if not filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files can be previewed")
    
    try:
        # Read CSV
        df = pd.read_csv(path)
        total_rows = len(df)
        
        # Get preview rows
        preview_df = df.head(limit)
        preview_rows = preview_df.to_dict(orient='records')
        
        # Calculate statistics if columns exist
        statistics = {}
        if 'scenario_type' in df.columns:
            statistics['scenario_distribution'] = df['scenario_type'].value_counts().to_dict()
        if 'test_category' in df.columns:
            statistics['category_distribution'] = df['test_category'].value_counts().to_dict()
        
        return {
            "filename": filename,
            "total_rows": total_rows,
            "preview_rows": len(preview_rows),
            "columns": df.columns.tolist(),
            "rows": preview_rows,
            "statistics": statistics,
            "download_url": f"/v1/datasets/download-file/{filename}"
        }
    
    except Exception as e:
        logger.error(f"Error previewing dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading CSV: {str(e)}")


# ============= SETTINGS =============

@router.get("/settings/models")
async def get_available_models():
    """
    Get list of available embedding models and LLMs with metadata
    
    Returns:
        - embedding_models: List with dimension, context, speed info
        - llms: List of LLMs for dataset generation
        - tooltip: Explanation text for users
    """
    return {
        "embedding_models": get_all_embedding_models(),
        "llms": get_all_llms(),
        "tooltip": EMBEDDING_TOOLTIP,
        "info": {
            "dimension_explanation": "Dimension = vector length. Larger usually = more accurate but slower & memory-heavy.",
            "recommendation": "For most use cases, 384-dim models provide good balance of speed and accuracy."
        }
    }


@router.get("/settings")
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's embedding settings"""
    result = await db.execute(
        select(UserSettings).where(UserSettings.u_id == current_user.u_id)
    )
    settings = result.scalar_one_or_none()
    
    from app.core.models_config import DEFAULT_EMBEDDING_MODEL, DEFAULT_DATASET_LLM
    
    return {
        "user_id": str(current_user.u_id),
        "default_embedding_model": settings.default_embedding_model if settings else DEFAULT_EMBEDDING_MODEL,
        "preferred_llm": settings.preferred_llm if settings else DEFAULT_DATASET_LLM
    }


@router.post("/settings/embedding-model")
async def set_default_embedding_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set user's default embedding model"""
    result = await db.execute(
        select(UserSettings).where(UserSettings.u_id == current_user.u_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserSettings(
            u_id=current_user.u_id,
            default_embedding_model=model_name
        )
        db.add(settings)
    else:
        settings.default_embedding_model = model_name
    
    await db.commit()
    logger.info(f"Updated embedding model for user {current_user.u_id}: {model_name}")
    
    return {
        "user_id": str(current_user.u_id),
        "default_embedding_model": model_name,
        "message": "Default embedding model updated"
    }


@router.post("/settings/llm")
async def set_preferred_llm(
    llm_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set user's preferred LLM for dataset generation"""
    try:
        from app.core.models_config import get_llm_info
        llm_info = get_llm_info(llm_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unknown LLM: {llm_id}")
    
    result = await db.execute(
        select(UserSettings).where(UserSettings.u_id == current_user.u_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = UserSettings(
            u_id=current_user.u_id,
            preferred_llm=llm_id
        )
        db.add(settings)
    else:
        settings.preferred_llm = llm_id
    
    await db.commit()
    logger.info(f"Updated preferred LLM for user {current_user.u_id}: {llm_id}")
    
    return {
        "user_id": str(current_user.u_id),
        "preferred_llm": llm_id,
        "llm_info": llm_info.dict(),
        "message": "Preferred LLM updated"
    }


# ============= DATASET-SPECIFIC OPERATIONS =============
# These endpoints operate on individual datasets (not templates)

@router.get("/{dataset_id}/info")
async def get_dataset_info(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dataset information including embedding status
    
    Returns:
    - Dataset metadata (name, csv_path, total_rows)
    - Embedding model and dimension
    - Embedding status and progress
    - Timestamps
    """
    result = await db.execute(
        select(Dataset).where(
            Dataset.dataset_id == UUID(dataset_id),
            Dataset.u_id == current_user.u_id
        )
    )
    dataset = result.scalar_one_or_none()
    
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    return {
        "dataset_id": str(dataset.dataset_id),
        "name": dataset.name,
        "template_id": str(dataset.t_id),
        "user_id": str(dataset.u_id),
        "csv_path": dataset.csv_path,
        "total_rows": dataset.total_rows,
        "embedding_model": dataset.embedding_model,
        "embedding_dimension": dataset.embedding_dimension,
        "embedding_status": dataset.embedding_status,
        "embedding_progress": dataset.embedding_progress,
        "embedded_rows": dataset.embedded_rows,
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
        "embedding_started_at": dataset.embedding_started_at.isoformat() if dataset.embedding_started_at else None,
        "embedding_completed_at": dataset.embedding_completed_at.isoformat() if dataset.embedding_completed_at else None,
        "generated_with_llm": dataset.generated_with_llm,
        "scenario_distribution": dataset.scenario_distribution
    }


@router.get("/{dataset_id}/embedding-status")
async def get_dataset_embedding_status(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed embedding status for a dataset
    
    Useful for polling progress during embedding operations.
    
    Returns:
    - status: pending | in_progress | completed | failed
    - progress: 0-100%
    - Row counts (total, embedded, failed)
    - Timing info (started_at, estimated_completion)
    - Celery task ID
    """
    embedding_service = get_enhanced_embedding_service()
    return await embedding_service.get_dataset_embedding_status(
        user_id=current_user.u_id,
        dataset_id=UUID(dataset_id),
        db=db
    )


@router.post("/{dataset_id}/reembed", response_model=ReembedDatasetResponse)
async def reembed_dataset(
    dataset_id: str,
    request: ReembedDatasetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Re-embed a dataset with a new embedding model
    
    🔒 This will:
    1. Delete ALL existing embeddings for this dataset
    2. Start a new Celery task to embed with the specified model
    3. Track progress (poll GET /{dataset_id}/embedding-status)
    
    Use Cases:
    - User changed their default embedding model
    - Frontend showed MODEL_MISMATCH error and user chose "Re-Embed"
    - Upgrading to a higher-quality model
    
    Args:
        model: New embedding model (uses user's default if None)
        force: Force re-embed even if already embedded with same model
        chunk_size: Rows per Celery task chunk (10-500, default 100)
    """
    embedding_service = get_enhanced_embedding_service()
    result = await embedding_service.reembed_dataset(
        user_id=current_user.u_id,
        dataset_id=UUID(dataset_id),
        db=db,
        new_model=request.model,
        force=request.force,
        chunk_size=request.chunk_size
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )
    
    return result


@router.post("/{dataset_id}/search")
async def search_dataset(
    dataset_id: str,
    request: SearchDatasetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for similar test cases within a specific dataset
    
    🔒 MODEL VALIDATION:
    - Validates that user's current embedding model matches dataset's model
    - Returns MODEL_MISMATCH structured error if mismatch detected
    - Frontend should display modal with "Use Previous" / "Re-Embed" options
    
    Args:
        query: Search query text
        top_k: Number of results (1-100, default 10)
        filter_scenario_type: Optional filter (valid, edge_case, extreme_scenario)
        filter_test_category: Optional filter
    
    Returns:
        Success: List of similar test cases with similarity scores
        Mismatch: MODEL_MISMATCH error with embedded_model, current_model, actions
    """
    embedding_service = get_enhanced_embedding_service()
    result = await embedding_service.search_similar_test_cases(
        user_id=current_user.u_id,
        dataset_id=UUID(dataset_id),
        query=request.query,
        top_k=request.top_k,
        db=db,
        filter_scenario_type=request.filter_scenario_type,
        filter_test_category=request.filter_test_category
    )
    
    # If result contains an error, return it with appropriate status code
    if "error" in result:
        error_code = result.get("error")
        if error_code == "MODEL_MISMATCH":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result
            )
        elif error_code in ["DATASET_NOT_FOUND", "NOT_EMBEDDED"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result
            )
        elif error_code == "EMBEDDING_IN_PROGRESS":
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result
            )
    
    return result


@router.get("/by-template/{template_id}")
async def list_datasets_by_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all datasets for a specific template
    
    Returns list of datasets with their embedding status.
    """
    result = await db.execute(
        select(Dataset).where(
            Dataset.t_id == UUID(template_id),
            Dataset.u_id == current_user.u_id
        ).order_by(Dataset.created_at.desc())
    )
    datasets = result.scalars().all()
    
    return {
        "template_id": template_id,
        "total_datasets": len(datasets),
        "datasets": [
            {
                "dataset_id": str(d.dataset_id),
                "name": d.name,
                "csv_path": d.csv_path,
                "total_rows": d.total_rows,
                "embedding_model": d.embedding_model,
                "embedding_status": d.embedding_status,
                "embedding_progress": d.embedding_progress,
                "embedded_rows": d.embedded_rows,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in datasets
        ]
    }
