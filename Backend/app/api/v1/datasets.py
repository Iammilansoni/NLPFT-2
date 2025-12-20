"""
Datasets API - Consolidated endpoint for dataset lifecycle management
Handles: generation, upload, embedding, search, and management

Replaces: dataset.py + dataset_embeddings.py

KEY DESIGN: ONE EMBEDDING MODEL PER DATASET
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
from app.models.database_models import User, UserSettings, Template, Metadata, Parameter, ExpectedResponse, Dataset, CSVData
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
from app.models.schemas.embedding_schemas import (
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
    
    NEW: Template-aware generation with high variation
    """
    # REQUIRED: Approved template ID
    template_id: str = Field(..., description="UUID of approved template (REQUIRED)")
    
    # Dataset generation parameters
    num_examples: Optional[int] = Field(
        default=None,
        ge=10,
        le=50000,
        description="Number of test cases to generate (10-50000). Large datasets use partition mode."
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


# ============= HELPER FUNCTIONS FOR POSTGRESQL STORAGE =============

async def store_csv_to_postgresql(
    csv_path: str,
    user_id: UUID,
    template_id: Optional[UUID],
    db: AsyncSession,
    dataset_name: Optional[str] = None,
    generated_with_llm: Optional[str] = None,
    generation_prompt: Optional[str] = None,
    scenario_distribution: Optional[dict] = None
) -> Dataset:
    """
    Store CSV rows in PostgreSQL and create a Dataset entry.
    
    Args:
        csv_path: Path to CSV file
        user_id: User UUID
        template_id: Template UUID (optional for uploads)
        db: Database session
        dataset_name: Optional name for the dataset
        generated_with_llm: LLM model used for generation
        generation_prompt: User's prompt for generation
        scenario_distribution: Distribution of scenarios
    
    Returns:
        Dataset: The created Dataset entry
    """
    import json
    
    # Read CSV
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['query']) if 'query' in df.columns else df
    total_rows = len(df)
    
    logger.info(f"Storing {total_rows} CSV rows to PostgreSQL...")
    
    # Create Dataset entry
    dataset = Dataset(
        dataset_id=uuid.uuid4(),
        u_id=user_id,
        t_id=template_id,
        name=dataset_name or os.path.basename(csv_path),
        csv_path=csv_path,
        total_rows=total_rows,
        embedding_status="pending",
        embedding_progress=0,
        embedded_rows=0,
        generated_with_llm=generated_with_llm,
        generation_prompt=generation_prompt,
        scenario_distribution=scenario_distribution,
        created_at=datetime.utcnow()
    )
    db.add(dataset)
    await db.flush()  # Get the dataset_id
    
    # Store each row in csv_data table
    csv_rows = []
    for idx, row in df.iterrows():
        # Parse request/response JSON if present
        request_data = None
        response_data = None
        
        if 'request' in df.columns and pd.notna(row.get('request')):
            try:
                request_data = json.loads(row['request']) if isinstance(row['request'], str) else row['request']
            except (json.JSONDecodeError, TypeError):
                request_data = {"raw": str(row['request'])}
        
        if 'response' in df.columns and pd.notna(row.get('response')):
            try:
                response_data = json.loads(row['response']) if isinstance(row['response'], str) else row['response']
            except (json.JSONDecodeError, TypeError):
                response_data = {"raw": str(row['response'])}
        
        csv_row = CSVData(
            csv_id=uuid.uuid4(),
            u_id=user_id,
            t_id=template_id,
            dataset_id=dataset.dataset_id,
            query=str(row.get('query', '')) if pd.notna(row.get('query')) else None,
            api_name=str(row.get('api', '')) if pd.notna(row.get('api')) else None,
            endpoint=str(row.get('endpoint', '')) if pd.notna(row.get('endpoint')) else None,
            request=request_data,
            response=response_data,
            description=str(row.get('notes', '')) if pd.notna(row.get('notes')) else None,
            data_category=str(row.get('scenario_type', 'valid')) if pd.notna(row.get('scenario_type')) else 'valid',
            variation_type=str(row.get('test_category', '')) if pd.notna(row.get('test_category')) else None,
            generated_with_llm=generated_with_llm,
            generation_prompt=generation_prompt,
            is_embedded=0,
            created_at=datetime.utcnow()
        )
        csv_rows.append(csv_row)
        
        # Batch insert every 100 rows
        if len(csv_rows) >= 100:
            db.add_all(csv_rows)
            await db.flush()
            csv_rows = []
    
    # Insert remaining rows
    if csv_rows:
        db.add_all(csv_rows)
    
    await db.commit()
    await db.refresh(dataset)
    
    logger.info(f"Stored {total_rows} rows in PostgreSQL (dataset_id={dataset.dataset_id})")
    return dataset
    statistics: Optional[dict] = None
    error: Optional[str] = None


# ============= BACKGROUND TASKS =============

def process_upload_task(task_id: str, file_path: str, user_id: str = None, template_id: str = None, clear_existing: bool = False):
    """Background task to process uploaded CSV with auto-embedding"""
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
            
            # =====================================================================
            # AUTO-EMBED CSV DATASET (Using sync function - no Celery needed)
            # =====================================================================
            if user_id and result["count"] > 0:
                try:
                    from app.services.embedding_service import create_embedding_task
                    
                    # Use template_id if provided, otherwise generate a unique one for this upload
                    embed_template_id = template_id or f"upload-{task_id}"
                    
                    logger.info(f"Auto-embedding started for uploaded CSV: {file_path}")
                    
                    # Run embedding synchronously (within BackgroundTask context)
                    embedding_result = create_embedding_task(
                        csv_path=file_path,
                        user_id=str(user_id),
                        template_id=str(embed_template_id)
                    )
                    
                    if embedding_result.get("status") == "completed":
                        logger.info(f"Embedding completed: {embedding_result.get('task_id')}")
                        task_manager.update_task(
                            task_id,
                            embedding_task_id=embedding_result.get("task_id"),
                            auto_embed_status="completed"
                        )
                    else:
                        logger.warning(f"Embedding failed: {embedding_result.get('message')}")
                        task_manager.update_task(
                            task_id,
                            auto_embed_status="failed",
                            auto_embed_error=embedding_result.get("message")
                        )
                except Exception as embed_error:
                    logger.warning(f"Auto-embedding for upload failed: {embed_error}")
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
    template_id: Optional[str] = Query(None, description="Associate with template (optional)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload CSV dataset and store in PostgreSQL + Redis
    
    User Isolation: Dataset is associated with the authenticated user.
    Data Storage: CSV rows saved to PostgreSQL, embeddings to Redis.
    
    Returns dataset_id and task_id for tracking progress
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    
    task_manager = get_task_manager()
    # Associate task with current user
    task_id = task_manager.create_task(user_id=current_user.u_id)
    
    # Save file to disk
    save_path = os.path.join(DATASETS_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(content)
    
    # ========== STORE CSV TO POSTGRESQL ==========
    try:
        t_id = UUID(template_id) if template_id else None
        
        # Validate template belongs to user if provided
        if t_id:
            template_result = await db.execute(
                select(Template).where(
                    Template.t_id == t_id,
                    Template.u_id == current_user.u_id
                )
            )
            if not template_result.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Template not found or access denied")
        
        dataset = await store_csv_to_postgresql(
            csv_path=save_path,
            user_id=current_user.u_id,
            template_id=t_id,
            db=db,
            dataset_name=file.filename
        )
        
        logger.info(f"CSV stored in PostgreSQL: {file.filename} (dataset_id={dataset.dataset_id})")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store CSV in PostgreSQL: {e}", exc_info=True)
        # Continue with Redis ingestion even if PostgreSQL fails
        dataset = None
    
    # ========== BACKGROUND: INGEST TO REDIS + EMBED ==========
    # Pass user_id and dataset_id for auto-embedding (ensures multi-tenant isolation)
    background_tasks.add_task(
        process_upload_task, 
        task_id, 
        save_path, 
        user_id=str(current_user.u_id),
        template_id=str(t_id) if t_id else None,
        clear_existing=False
    )
    
    logger.info(f"CSV upload started: {file.filename} for user {current_user.u_id}")
    
    return {
        "task_id": task_id,
        "dataset_id": str(dataset.dataset_id) if dataset else None,
        "message": "File uploaded and stored in PostgreSQL. Embedding started in background.",
        "file": save_path,
        "total_rows": dataset.total_rows if dataset else None
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
    
    NEW REQUIREMENT: Template must be 'approved' before dataset generation
    RATE LIMIT: 10 generations per minute per IP to prevent API abuse
    
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
                    Template.u_id == current_user.u_id  # Prevent cross-tenant access
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
            
            logger.info(f"Template {dataset_request.template_id} approved by {metadata.approved_by} at {metadata.approved_at}")
            
            # Create task for tracking
            task_manager = get_task_manager()
            # Associate task with current user
            task_id = task_manager.create_task(user_id=current_user.u_id)
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
            
            # Get CSV path from result
            csv_path = result["paths"]["csv"]
            
            # ========== STORE GENERATED CSV TO POSTGRESQL ==========
            dataset = None
            try:
                dataset = await store_csv_to_postgresql(
                    csv_path=csv_path,
                    user_id=current_user.u_id,
                    template_id=UUID(dataset_request.template_id),
                    db=db,
                    dataset_name=f"{result['template_name']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    generated_with_llm=result.get("model_used"),
                    generation_prompt=dataset_request.user_prompt,
                    scenario_distribution=result.get("scenario_distribution")
                )
                logger.info(f"Generated dataset stored in PostgreSQL (dataset_id={dataset.dataset_id})")
            except Exception as store_error:
                logger.error(f"Failed to store generated dataset in PostgreSQL: {store_error}", exc_info=True)
                task_manager.update_task(task_id, status="failed", message=f"Failed to store dataset: {store_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to store generated dataset: {store_error}"
                )
            
            
            # ========== EMBEDDING IS NOW MANUAL ==========
            # Dataset is created and stored, embedding can be done later via the Embed button
            from app.models.schemas.embedding_schemas import EmbeddingStatus
            if dataset:
                dataset.embedding_status = EmbeddingStatus.PENDING
                await db.commit()
            
            task_manager.update_progress(task_id, 95, "Finalizing...", "finalize")
            
            # Audit log
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
                    "embedding_status": "pending",
                    "embedded_to_redis": False
                },
                request=request
            )
            
            # Mark task as completed
            task_manager.update_task(
                task_id, 
                status="completed", 
                message=f"Generated {result['total_generated']} test cases. Click 'Embed to Redis' to create vectors.",
                result={
                    "total_generated": result["total_generated"],
                    "csv_path": csv_path,
                    "embedded_to_redis": False,
                    "embedding_status": "pending"
                },
                files={
                    "csv": csv_path
                }
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "dataset_id": str(dataset.dataset_id) if dataset else None,
                "embedding_status": "pending",
                "embedded_to_redis": False,
                "message": f"Dataset generated ({result['total_generated']} rows) - Stored in PostgreSQL. Click 'Embed to Redis' to create vectors.",
                "template_name": result["template_name"],
                "template_id": result["template_id"],
                "total_generated": result["total_generated"],
                "requested": result["requested"],
                "scenario_distribution": result["scenario_distribution"],
                "category_distribution": result["category_distribution"],
                "csv_path": csv_path,
                "csv_preview": result["csv_preview"],
                "user_prompt": result["user_prompt"],
                "focus_areas": result["focus_areas"],
                "timestamp": result["timestamp"],
                "download_url": f"/v1/datasets/download/{os.path.basename(csv_path)}",
                "stored_in_postgresql": dataset is not None
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
        except Exception as update_error:
            logger.debug(f"Could not update task status: {update_error}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
@router.get("/list")
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all datasets for the current user from PostgreSQL.
    
    User Isolation: Only returns datasets belonging to the authenticated user.
    
    Returns persistent dataset information including:
    - Dataset metadata (name, rows, status)
    - Embedding status
    - Template association
    
    Available at both:
    - GET /api/v1/datasets/
    - GET /api/v1/datasets/list
    """
    try:
        from sqlalchemy import func
        
        # Query datasets from PostgreSQL
        result = await db.execute(
            select(Dataset)
            .where(Dataset.u_id == current_user.u_id)
            .order_by(Dataset.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        datasets = result.scalars().all()
        
        # Get total count
        count_result = await db.execute(
            select(func.count(Dataset.dataset_id))
            .where(Dataset.u_id == current_user.u_id)
        )
        total = count_result.scalar()
        
        # Get template names for each dataset
        template_ids = [d.t_id for d in datasets if d.t_id]
        template_names = {}
        if template_ids:
            templates_result = await db.execute(
                select(Template.t_id, Template.api_name)
                .where(Template.t_id.in_(template_ids))
            )
            for t_id, api_name in templates_result:
                template_names[str(t_id)] = api_name
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "datasets": [
                {
                    "dataset_id": str(d.dataset_id),
                    "name": d.name,
                    "template_id": str(d.t_id) if d.t_id else None,
                    "template_name": template_names.get(str(d.t_id)) if d.t_id else None,
                    "total_rows": d.total_rows,
                    "embedded_rows": d.embedded_rows,
                    "embedding_status": d.embedding_status,
                    "embedding_model": d.embedding_model,
                    "source_type": "AI_GENERATED" if d.generated_with_llm else "CSV_UPLOAD",
                    "generated_with_llm": d.generated_with_llm,
                    "created_at": d.created_at.isoformat() + "Z" if d.created_at else None,
                    "updated_at": d.updated_at.isoformat() + "Z" if d.updated_at else None
                }
                for d in datasets
            ]
        }
    except Exception as e:
        logger.error(f"Error listing datasets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get status of a dataset generation/upload task
    
    User Isolation: Only returns task if it belongs to the authenticated user.
    
    Returns progress information including:
    - status: pending, running, completed, failed
    - progress: 0-100 percentage
    - message: current status message
    - current_step: what's happening now
    - steps: history of completed steps
    """
    task_manager = get_task_manager()
    # Pass user_id for access control
    task = task_manager.get_task(task_id, user_id=current_user.u_id)
    
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

# ============= POSTGRESQL DATA RETRIEVAL =============

@router.get("/db/list")
async def list_datasets_from_db(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all datasets stored in PostgreSQL for the current user.
    
    Returns dataset metadata with row counts.
    """
    try:
        result = await db.execute(
            select(Dataset)
            .where(Dataset.u_id == current_user.u_id)
            .order_by(Dataset.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        datasets = result.scalars().all()
        
        # Count total
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count(Dataset.dataset_id))
            .where(Dataset.u_id == current_user.u_id)
        )
        total = count_result.scalar()
        
        return {
            "total": total,
            "datasets": [
                {
                    "dataset_id": str(d.dataset_id),
                    "name": d.name,
                    "template_id": str(d.t_id) if d.t_id else None,
                    "csv_path": d.csv_path,
                    "total_rows": d.total_rows,
                    "embedded_rows": d.embedded_rows,
                    "embedding_status": d.embedding_status,
                    "embedding_model": d.embedding_model,
                    "generated_with_llm": d.generated_with_llm,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                }
                for d in datasets
            ]
        }
    except Exception as e:
        logger.error(f"Error listing datasets from DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/{dataset_id}")
async def get_dataset_from_db(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dataset metadata and summary from PostgreSQL.
    """
    try:
        result = await db.execute(
            select(Dataset).where(
                Dataset.dataset_id == UUID(dataset_id),
                Dataset.u_id == current_user.u_id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        return {
            "dataset_id": str(dataset.dataset_id),
            "name": dataset.name,
            "description": dataset.description,
            "template_id": str(dataset.t_id) if dataset.t_id else None,
            "csv_path": dataset.csv_path,
            "total_rows": dataset.total_rows,
            "embedded_rows": dataset.embedded_rows,
            "embedding_status": dataset.embedding_status,
            "embedding_progress": dataset.embedding_progress,
            "embedding_model": dataset.embedding_model,
            "embedding_dimension": dataset.embedding_dimension,
            "generated_with_llm": dataset.generated_with_llm,
            "generation_prompt": dataset.generation_prompt,
            "scenario_distribution": dataset.scenario_distribution,
            "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
            "embedding_started_at": dataset.embedding_started_at.isoformat() if dataset.embedding_started_at else None,
            "embedding_completed_at": dataset.embedding_completed_at.isoformat() if dataset.embedding_completed_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset from DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/db/{dataset_id}/rows")
async def get_dataset_rows(
    dataset_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    scenario_type: Optional[str] = Query(None, description="Filter by scenario_type: valid, edge_case, extreme_scenario"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get CSV rows from PostgreSQL for a dataset.
    
    User Isolation: Only returns rows for datasets owned by the current user.
    
    Supports pagination and filtering by scenario_type.
    """
    try:
        # Verify dataset ownership
        dataset_result = await db.execute(
            select(Dataset).where(
                Dataset.dataset_id == UUID(dataset_id),
                Dataset.u_id == current_user.u_id
            )
        )
        dataset = dataset_result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Build query for rows
        query = select(CSVData).where(CSVData.dataset_id == UUID(dataset_id))
        
        if scenario_type:
            query = query.where(CSVData.data_category == scenario_type)
        
        query = query.order_by(CSVData.created_at).offset(skip).limit(limit)
        
        result = await db.execute(query)
        rows = result.scalars().all()
        
        # Count total with filter
        from sqlalchemy import func
        count_query = select(func.count(CSVData.csv_id)).where(CSVData.dataset_id == UUID(dataset_id))
        if scenario_type:
            count_query = count_query.where(CSVData.data_category == scenario_type)
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return {
            "dataset_id": dataset_id,
            "total": total,
            "skip": skip,
            "limit": limit,
            "filter": {"scenario_type": scenario_type} if scenario_type else None,
            "rows": [
                {
                    "csv_id": str(r.csv_id),
                    "query": r.query,
                    "api_name": r.api_name,
                    "endpoint": r.endpoint,
                    "request": r.request,
                    "response": r.response,
                    "description": r.description,
                    "scenario_type": r.data_category,
                    "variation_type": r.variation_type,
                    "is_embedded": r.is_embedded == 1,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in rows
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dataset rows: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/db/{dataset_id}")
async def delete_dataset_from_db(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a dataset and all its rows from PostgreSQL.
    
    WARNING: This also deletes all associated CSV rows and embeddings.
    """
    try:
        # Verify dataset ownership
        result = await db.execute(
            select(Dataset).where(
                Dataset.dataset_id == UUID(dataset_id),
                Dataset.u_id == current_user.u_id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Delete dataset (cascade will delete csv_rows)
        await db.delete(dataset)
        await db.commit()
        
        logger.info(f"Deleted dataset {dataset_id} for user {current_user.u_id}")
        
        return {
            "success": True,
            "message": f"Dataset {dataset_id} and all its rows deleted",
            "deleted_rows": dataset.total_rows
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class RenameDatasetRequest(BaseModel):
    """Request to rename a dataset"""
    name: str = Field(..., min_length=1, max_length=255, description="New dataset name")


@router.patch("/db/{dataset_id}/rename")
async def rename_dataset(
    dataset_id: str,
    request: RenameDatasetRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Rename a dataset.
    
    User Isolation: Only allows renaming datasets owned by the current user.
    
    This ONLY updates the name - does NOT affect:
    - Dataset rows
    - Embeddings
    - Template mapping
    """
    try:
        # Verify dataset ownership
        result = await db.execute(
            select(Dataset).where(
                Dataset.dataset_id == UUID(dataset_id),
                Dataset.u_id == current_user.u_id
            )
        )
        dataset = result.scalar_one_or_none()
        
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        old_name = dataset.name
        dataset.name = request.name
        dataset.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(dataset)
        
        logger.info(f"Renamed dataset {dataset_id}: '{old_name}' -> '{request.name}'")
        
        return {
            "success": True,
            "dataset_id": str(dataset.dataset_id),
            "old_name": old_name,
            "new_name": dataset.name,
            "message": f"Dataset renamed to '{request.name}'"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error renaming dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/db/{dataset_id}/embed")
async def embed_dataset_to_redis(
    dataset_id: str,
    force_reembed: bool = Query(False, description="Force re-embed even if already embedded"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Embed a dataset to Redis for vector search.
    
    User Isolation: Only allows embedding datasets owned by the current user.
    
    Uses multi_model_embedding_service which:
    1. Gets embedding model from user's Settings
    2. Stores vectors in model-specific Redis index
    3. Uses proper key format: vector:{model_namespace}:{user_id}:{dataset_id}:{row_id}
    
    This ensures vectors are stored in the same location that semantic search looks.
    """
    from app.services.multi_model_embedding_service import get_multi_model_embedding_service
    
    try:
        embedding_service = get_multi_model_embedding_service()
        
        result = await embedding_service.embed_dataset(
            db=db,
            user_id=current_user.u_id,
            dataset_id=UUID(dataset_id),
            force_reembed=force_reembed,
            batch_size=32
        )
        
        if not result.get("success"):
            # Return error response with appropriate status code
            error_code = result.get("error")
            if error_code == "MODEL_MISMATCH":
                raise HTTPException(status_code=409, detail=result)
            elif error_code == "DATASET_NOT_FOUND":
                raise HTTPException(status_code=404, detail=result.get("message", "Dataset not found"))
            elif error_code == "OLLAMA_UNAVAILABLE":
                raise HTTPException(status_code=503, detail=result.get("message", "Ollama not available"))
            else:
                raise HTTPException(status_code=500, detail=result.get("message", "Embedding failed"))
        
        return {
            "success": True,
            "dataset_id": result.get("dataset_id"),
            "embedding_status": result.get("status", "completed"),
            "model": result.get("model_id"),
            "dimension": result.get("dimension"),
            "redis_index": result.get("redis_index"),
            "total_rows": result.get("total_rows"),
            "embedded_count": result.get("embedded_count"),
            "failed_count": result.get("failed_count"),
            "message": f"Embedded {result.get('embedded_count', 0)} rows successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error embedding dataset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preview/{task_id}")
async def preview_dataset(
    task_id: str, 
    limit: int = 100, 
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """
    Preview dataset records from a completed task
    
    AUTHENTICATION REQUIRED - Only returns task if owned by current user
    """
    task_manager = get_task_manager()
    # Pass user_id for ownership check
    task = task_manager.get_task(task_id, user_id=current_user.u_id)
    
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
async def download_dataset(
    task_id: str, 
    format: str,
    current_user: User = Depends(get_current_user)
):
    """
    Download dataset file from a completed task
    
    AUTHENTICATION REQUIRED - Only allows download if owned by current user
    """
    task_manager = get_task_manager()
    # Pass user_id for ownership check
    task = task_manager.get_task(task_id, user_id=current_user.u_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    file_path = task.get("files", {}).get(format)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    media_type = "text/csv"  # Only CSV format supported
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
    
    NOTE: Use POST /datasets/{dataset_id}/search for model-validated search
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
    - Task ID
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
    
    This will:
    1. Delete ALL existing embeddings for this dataset
    2. Start a background task to embed with the specified model
    3. Track progress (poll GET /{dataset_id}/embedding-status)
    
    Use Cases:
    - User changed their default embedding model
    - Frontend showed MODEL_MISMATCH error and user chose "Re-Embed"
    - Upgrading to a higher-quality model
    
    Args:
        model: New embedding model (uses user's default if None)
        force: Force re-embed even if already embedded with same model
        chunk_size: Rows per batch (10-500, default 100)
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
    
    MODEL VALIDATION:
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
