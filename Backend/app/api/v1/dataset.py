


from typing import Optional, List, Dict, Any, cast
from pathlib import Path
from datetime import datetime
import asyncio

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.core.logger import logger


router = APIRouter(prefix="/dataset", tags=["Dataset Generation"])


# Task queue to prevent concurrent dataset generation
task_queue_lock = asyncio.Lock()
is_generation_running = False
class DatasetGenerationRequest(BaseModel):
    api_count: int = Field(default=10, ge=1, le=50, description="Number of APIs to generate")
    nl_variations_per_api: int = Field(default=20, ge=5, le=100, description="NL variations per API")
    use_llm: bool = Field(default=False, description="Use LLM for paraphrase generation")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model name")
    llm_model: str = Field(default="microsoft/Phi-3-mini-4k-instruct", description="LLM model name")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    clear_existing_embeddings: bool = Field(default=False, description="Clear existing Redis embeddings before generation")
    api_context: str = Field(default="", description="Optional context describing the domain or type of APIs to generate (e.g., 'e-commerce', 'hotel booking system')")


class DatasetGenerationResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None
    dataset_id: Optional[str] = None
    files: Optional[Dict[str, str]] = None
    statistics: Optional[Dict[str, Any]] = None


class DatasetListResponse(BaseModel):
    datasets: List[Dict[str, Any]]
    total: int


active_tasks: Dict[str, Dict[str, Any]] = {}


@router.post("/generate", response_model=DatasetGenerationResponse)
async def generate_dataset(
    request: DatasetGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate dataset in background. Only one generation task can run at a time.
    """
    global is_generation_running
    
    # Check if another generation is already running
    if is_generation_running:
        # Find the running task
        running_task = None
        for task_id, task_info in active_tasks.items():
            if task_info["status"] in ["pending", "running"]:
                running_task = task_id
                break
        
        return DatasetGenerationResponse(
            status="rejected",
            message=f"Another dataset generation is already in progress (task: {running_task}). Please wait for it to complete.",
            task_id=running_task
        )
    
    try:
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        active_tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "message": "Dataset generation queued",
            "created_at": datetime.now().isoformat(),
            "request": request.model_dump()
        }
        
        # Mark as running before starting background task
        is_generation_running = True
        
        background_tasks.add_task(
            _generate_dataset_background,
            task_id,
            request
        )
        
        logger.info(f"Dataset generation task created: {task_id}")
        
        return DatasetGenerationResponse(
            status="queued",
            message="Dataset generation started in background",
            task_id=task_id
        )
        
    except Exception as e:
        is_generation_running = False
        logger.error(f"Error creating dataset generation task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_dataset_background(task_id: str, request: DatasetGenerationRequest):
    """Background task for dataset generation with proper cleanup"""
    global is_generation_running
    
    try:
        active_tasks[task_id]["status"] = "running"
        active_tasks[task_id]["progress"] = 10
        active_tasks[task_id]["message"] = "Initializing generator..."
        
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent.parent))
        from generate_api_dataset import APIDatasetGenerator  # type: ignore
        
        active_tasks[task_id]["progress"] = 20
        active_tasks[task_id]["message"] = "Loading models (using shared cache)..."
        
        generator = APIDatasetGenerator(
            embedding_model_name=request.embedding_model,
            llm_model_name=request.llm_model,
            redis_host=request.redis_host,
            redis_port=request.redis_port,
            output_dir="./datasets",
            use_model_manager=True  # Use singleton model manager
        )
        
        
        if request.clear_existing_embeddings:
            active_tasks[task_id]["progress"] = 30
            active_tasks[task_id]["message"] = "Clearing existing Redis embeddings..."
            cleared_count = generator.clear_redis_embeddings()
            logger.info(f"Cleared {cleared_count} existing embeddings from Redis")
        
        active_tasks[task_id]["progress"] = 40
        active_tasks[task_id]["message"] = f"Generating {request.api_count} APIs..."
        
        dataset, redis_stored_count = generator.generate_dataset(
            api_count=request.api_count,
            nl_variations_per_api=request.nl_variations_per_api,
            use_llm=request.use_llm,
            api_context=request.api_context
        )
        
        active_tasks[task_id]["progress"] = 70
        active_tasks[task_id]["message"] = "Exporting to files..."
        
        dataset_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        json_path = generator.export_to_json(dataset, f"api_dataset_{dataset_id}.json")
        csv_path = generator.export_to_csv(dataset, f"api_dataset_{dataset_id}.csv")
        
        total_apis = len(dataset)
        total_nl_variations = sum(len(record['nl_inputs']) for record in dataset)
        
        active_tasks[task_id]["status"] = "completed"
        active_tasks[task_id]["progress"] = 100
        active_tasks[task_id]["message"] = "Dataset generation completed"
        active_tasks[task_id]["dataset_id"] = dataset_id
        active_tasks[task_id]["files"] = {
            "json": json_path,
            "csv": csv_path
        }
        active_tasks[task_id]["statistics"] = {
            "total_apis": total_apis,
            "total_nl_variations": total_nl_variations,
            "avg_variations_per_api": total_nl_variations / total_apis if total_apis > 0 else 0,
            "redis_stored_count": redis_stored_count,
            "redis_status": "success" if redis_stored_count > 0 else ("configured_but_failed" if generator.redis_client else "not_configured")
        }
        active_tasks[task_id]["dataset"] = dataset
        active_tasks[task_id]["completed_at"] = datetime.now().isoformat()
        
        logger.info(f"Dataset generation completed: {task_id}")
        
    except Exception as e:
        logger.error(f"Error in dataset generation background task: {e}")
        active_tasks[task_id]["status"] = "failed"
        active_tasks[task_id]["message"] = f"Error: {str(e)}"
        active_tasks[task_id]["error"] = str(e)
    finally:
        # Always release the lock when done
        is_generation_running = False
        logger.info(f"Dataset generation task completed, lock released")


@router.get("/status/{task_id}", response_model=DatasetGenerationResponse)
async def get_generation_status(task_id: str):
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task: Dict[str, Any] = active_tasks[task_id]
    
    return DatasetGenerationResponse(
        status=task["status"],
        message=task["message"],
        task_id=task_id,
        dataset_id=task.get("dataset_id"),
        files=task.get("files"),
        statistics=task.get("statistics")
    )


@router.get("/preview/{task_id}")
async def preview_dataset(
    task_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip")
) -> Dict[str, Any]:
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task: Dict[str, Any] = active_tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Dataset generation not completed yet")
    
    dataset: List[Dict[str, Any]] = cast(List[Dict[str, Any]], task.get("dataset", []))
    
    expanded_records: List[Dict[str, Any]] = []
    for record in dataset:
        for nl_input in record['nl_inputs']:
            expanded_records.append({
                "api": record['api'],
                "endpoint": record['endpoint'],
                "nl_input": nl_input,
                "definition_of_api": record['response']['definition'],
                "paraphrase_type": record['paraphrase_type'],
                "embedding_model": record['embedding_model']
            })
    
    total_records = len(expanded_records)
    start_idx = offset
    end_idx = min(offset + limit, total_records)
    
    result: Dict[str, Any] = {
        "task_id": task_id,
        "dataset_id": task.get("dataset_id"),
        "total_records": total_records,
        "showing": end_idx - start_idx,
        "offset": offset,
        "limit": limit,
        "has_more": end_idx < total_records,
        "records": expanded_records[start_idx:end_idx]
    }
    return result


@router.get("/download/{task_id}/{format}")
async def download_dataset(task_id: str, format: str):
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Dataset generation not completed yet")
    
    files = task.get("files", {})
    
    if format not in files:
        raise HTTPException(status_code=400, detail=f"Format '{format}' not available")
    
    filepath = Path(files[format])
    
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    media_types = {
        "json": "application/json",
        "jsonl": "application/x-ndjson",
        "csv": "text/csv",
        "summary": "text/plain"
    }
    
    return FileResponse(
        path=str(filepath),
        media_type=media_types.get(format, "application/octet-stream"),
        filename=filepath.name
    )


@router.get("/list", response_model=DatasetListResponse)
async def list_datasets():
    datasets: List[Dict[str, Any]] = []
    
    for task_id, task in active_tasks.items():
        task_info: Dict[str, Any] = {
            "task_id": task_id,
            "dataset_id": task.get("dataset_id"),
            "status": task["status"],
            "created_at": task.get("created_at"),
            "completed_at": task.get("completed_at"),
            "statistics": task.get("statistics"),
            "files": task.get("files")
        }
        datasets.append(task_info)
    
    datasets.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    
    return DatasetListResponse(
        datasets=datasets,
        total=len(datasets)
    )


@router.delete("/delete/{task_id}")
async def delete_dataset(task_id: str):
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task: Dict[str, Any] = active_tasks[task_id]
    
    files: Dict[str, Any] = cast(Dict[str, Any], task.get("files", {}))
    deleted_files: List[str] = []
    
    for _format_type, filepath in files.items():
        try:
            path = Path(filepath)
            if path.exists():
                path.unlink()
                deleted_files.append(filepath)
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {e}")
    
    del active_tasks[task_id]
    
    result: Dict[str, Any] = {
        "status": "success",
        "message": f"Dataset {task_id} deleted",
        "deleted_files": deleted_files
    }
    return result


@router.get("/format-api-docs/{task_id}")
async def format_api_docs(task_id: str):
    """Generate formatted API documentation from dataset"""
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task: Dict[str, Any] = active_tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Dataset generation not completed yet")
    
    dataset: List[Dict[str, Any]] = cast(List[Dict[str, Any]], task.get("dataset", []))
    
    # Generate formatted documentation
    docs: List[str] = []
    
    for record in dataset:
        api_name = record['api']
        endpoint = record['endpoint']
        definition = record['response']['definition']
        request_body = record.get('request', {})
        
        # Determine HTTP method based on API name
        method = "POST"
        if api_name in ["get-profile", "logout"]:
            method = "GET"
        elif api_name in ["update-profile", "change-password"]:
            method = "PUT"
        elif api_name == "delete-account":
            method = "DELETE"
        
        # Create formatted documentation
        doc = f"""
{method}  {endpoint}
-----------------------------------------
Description:
  {definition}

Request Body:
  {request_body if request_body else 'No request body required'}

Response (200 OK):
  {{
    "success": true,
    "message": "{api_name} successful",
    "data": {{
      "user_id": "12345",
      "timestamp": "2025-10-12T10:30:00Z"
    }}
  }}

Response (400 Bad Request):
  {{
    "success": false,
    "error": "Invalid request",
    "message": "Missing required fields"
  }}

Response (401 Unauthorized):
  {{
    "success": false,
    "error": "Unauthorized",
    "message": "Invalid or expired token"
  }}

Process Flow:
  1. Client sends request to {endpoint}
  2. Server validates the request payload
  3. Server authenticates the user (if required)
  4. Server processes the {api_name} operation
  5. Server returns success or error response

Natural Language Variations (Total: {len(record['nl_inputs'])} examples):
"""
        
        # Add ALL NL variations
        nl_inputs = record.get('nl_inputs', [])
        for i, nl_input in enumerate(nl_inputs, 1):
            doc += f"  {i}. \"{nl_input}\"\n"
        
        embedding_vec = record.get('embedding_vector', [])
        doc += f"""
Example cURL:
  curl -X {method} {endpoint} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{request_body if request_body else "{}"}'

Embedding Model: {record['embedding_model']}
Embedding Dimension: {len(embedding_vec)}

{"="*80}
"""
        docs.append(doc)
    
    
    full_docs = f"""
API DOCUMENTATION
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Dataset ID: {task.get("dataset_id", "N/A")}
Total APIs: {len(dataset)}
{"="*80}

""" + "\n\n".join(docs)
    
    return JSONResponse(
        content={
            "task_id": task_id,
            "dataset_id": task.get("dataset_id"),
            "total_apis": len(dataset),
            "documentation": full_docs,
            "format": "text"
        }
    )


@router.post("/generate-sync", response_model=DatasetGenerationResponse)
async def generate_dataset_sync(request: DatasetGenerationRequest):
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent.parent))
        from generate_api_dataset import APIDatasetGenerator  # type: ignore
        
        generator = APIDatasetGenerator(
            embedding_model_name=request.embedding_model,
            llm_model_name=request.llm_model,
            redis_host=request.redis_host,
            redis_port=request.redis_port,
            output_dir="./datasets"
        )
        
        
        if request.clear_existing_embeddings:
            cleared_count = generator.clear_redis_embeddings()
            logger.info(f"Cleared {cleared_count} existing embeddings from Redis")
        
        dataset, redis_stored_count = generator.generate_dataset(
            api_count=request.api_count,
            nl_variations_per_api=request.nl_variations_per_api,
            use_llm=request.use_llm,
            api_context=request.api_context
        )
        
        dataset_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        json_path = generator.export_to_json(dataset, f"api_dataset_{dataset_id}.json")
        csv_path = generator.export_to_csv(dataset, f"api_dataset_{dataset_id}.csv")
        
        total_apis = len(dataset)
        total_nl_variations = sum(len(record['nl_inputs']) for record in dataset)
        
        logger.info(f"Synchronous dataset generation completed: {dataset_id}")
        
        return DatasetGenerationResponse(
            status="completed",
            message="Dataset generation completed",
            dataset_id=dataset_id,
            files={
                "json": json_path,
                "csv": csv_path
            },
            statistics={
                "total_apis": total_apis,
                "total_nl_variations": total_nl_variations,
                "avg_variations_per_api": total_nl_variations / total_apis if total_apis > 0 else 0,
                "redis_stored_count": redis_stored_count,
                "redis_status": "success" if redis_stored_count > 0 else ("configured_but_failed" if generator.redis_client else "not_configured")
            }
        )
        
    except Exception as e:
        logger.error(f"Error in synchronous dataset generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Natural language query to search for")
    dataset_id: Optional[str] = Field(None, description="Specific dataset ID to search in (latest if not provided)")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of top results to return")
    min_similarity: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity threshold")


class SemanticSearchResult(BaseModel):
    api: str
    original_nl: str
    matched_variation: str
    similarity_score: float
    metadata: Dict[str, Any]


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SemanticSearchResult]
    dataset_id: str
    search_time_ms: float


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(request: SemanticSearchRequest):
    """
    Search for similar API commands using semantic similarity.
    
    This endpoint:
    1. Takes a natural language query
    2. Converts it to an embedding vector
    3. Finds the most similar APIs in your generated dataset
    4. Returns ranked results with similarity scores
    
    Example:
        Query: "press the login button"
        Results: [
            {api: "click_button", similarity: 0.92},
            {api: "tap_element", similarity: 0.85}
        ]
    """
    try:
        import json
        import numpy as np  # type: ignore
        from sentence_transformers import SentenceTransformer  # type: ignore
        import time
        
        start_time = time.time()
        
        
        datasets_dir = Path("./datasets")
        if request.dataset_id:
            json_file = datasets_dir / f"api_dataset_{request.dataset_id}.json"
        else:
           
            json_files = sorted(datasets_dir.glob("api_dataset_*.json"), reverse=True)
            if not json_files:
                raise HTTPException(status_code=404, detail="No datasets found")
            json_file = json_files[0]
            request.dataset_id = json_file.stem.replace("api_dataset_", "")
        
        if not json_file.exists():
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")
        
        
        with open(json_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
       
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        query_embedding = model.encode([request.query])[0]  # type: ignore[reportUnknownMemberType]
        
        
        results: List[Dict[str, Any]] = []
        for entry in dataset:
            api_embedding = np.array(entry['embedding_vector'])
            
            
            similarity = np.dot(query_embedding, api_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(api_embedding)
            )
            
            if similarity >= request.min_similarity:
                
                variation_similarities: List[tuple[Any, Any]] = []
                for nl_variation in entry['nl_inputs']:
                    var_embedding = model.encode([nl_variation])[0]  # type: ignore[reportUnknownMemberType]
                    var_similarity = np.dot(query_embedding, var_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(var_embedding)
                    )
                    variation_similarities.append((nl_variation, var_similarity))  # type: ignore[reportUnknownMemberType]
                
                
                best_variation, best_var_similarity = max(variation_similarities, key=lambda x: x[1])  # type: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
                
                result_entry: Dict[str, Any] = {
                    'api': entry['api'],
                    'original_nl': entry['original_nl'],
                    'matched_variation': str(best_variation),
                    'similarity_score': float(max(similarity, best_var_similarity)),  # type: ignore[reportUnknownArgumentType]
                    'metadata': entry.get('metadata', {})
                }
                results.append(result_entry)
        
        
        results = sorted(results, key=lambda x: float(x['similarity_score']), reverse=True)[:request.top_k]  # type: ignore[reportUnknownArgumentType, reportUnknownLambdaType]
        
        search_time = (time.time() - start_time) * 1000
        
        logger.info(f"Semantic search completed: query='{request.query}', results={len(results)}, time={search_time:.2f}ms")
        
        
        search_results = [SemanticSearchResult(**r) for r in results]  # type: ignore[reportUnknownArgumentType]
        
        return SemanticSearchResponse(
            query=request.query,
            results=search_results,
            dataset_id=request.dataset_id,
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))
