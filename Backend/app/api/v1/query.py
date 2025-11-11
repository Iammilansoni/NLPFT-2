"""
Query API endpoint - Main entry point for natural language queries
Handles the complete pipeline: parse -> generate dataset -> embed -> search
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import os
from app.nlp.query_parser import parse_query
from app.nlp.dataset_generator import get_dataset_generator
from app.nlp.embedding_manager import get_embedding_manager
from app.services.template_service import get_template_service
from app.core.logger import logger
from app.core.postgres import get_db, TestRun

router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="Natural language query", min_length=1)
    generate_dataset: bool = Field(True, description="Whether to generate dataset if needed")
    num_examples: int = Field(50, description="Number of examples to generate", ge=10, le=200)
    top_k: int = Field(5, description="Number of similar results to return", ge=1, le=20)


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    query: str
    intent: str
    slots: Dict
    confidence: float
    best_matches: List[Dict]
    dataset_generated: bool
    dataset_info: Optional[Dict] = None
    search_results: List[Dict]
    dataset_download_url: Optional[str] = None  # URL to download generated CSV


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Process natural language query through complete pipeline
    
    1. Parse query to extract intent and slots
    2. Check if dataset exists, generate if needed
    3. Embed new data to Redis
    4. Perform vector search
    5. Return best matches with confidence
    
    Example:
        Input: "Authenticate my credentials for Milan and MS3ESD"
        Output: {
            "intent": "login",
            "slots": {"username": "Milan", "password": "MS3ESD"},
            "confidence": 0.97,
            "best_matches": [...]
        }
    """
    start_time = datetime.utcnow()
    test_run_id = None
    
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Step 1: Parse query
        parsed = parse_query(request.query)
        intent = parsed["intent"]
        slots = parsed["slots"]
        confidence = parsed["confidence"]
        
        logger.info(f"Parsed - Intent: {intent}, Confidence: {confidence:.2f}, Slots: {slots}")
        
        # Create test run record with 'running' status
        try:
            test_run = TestRun(
                query=request.query,
                intent=intent if intent != "unknown" else None,
                status="running",
                confidence=confidence,
                tests_count=0,
                best_match_api=None,
                best_match_score=None,
                search_results_count=0,
                dataset_generated=False
            )
            db.add(test_run)
            await db.commit()
            await db.refresh(test_run)
            test_run_id = test_run.id
            logger.info(f"Created test run {test_run_id} with status 'running'")
        except Exception as e:
            logger.warning(f"Failed to create test run record: {e}")
            # Continue processing even if test run creation fails
        
        if intent == "unknown" or confidence < 0.3:
            # Provide helpful error with available intents
            template_service = get_template_service()
            templates = template_service.get_all_templates()
            available_intents = list(templates.keys()) if templates else []
            
            error_detail = {
                "error": "Could not determine API intent from query",
                "message": "Your query didn't match any known API patterns. Please try to be more specific.",
                "query": request.query,
                "confidence": confidence,
                "detected_intent": intent if intent != "unknown" else None,
                "available_intents": available_intents[:10],  # Show first 10
                "suggestions": [
                    "Include API-related keywords like 'login', 'signup', 'update', etc.",
                    "Provide clear action words in your query",
                    f"Try using one of these APIs: {', '.join(available_intents[:5])}"
                ] if available_intents else [
                    "No API templates are loaded. Please sync templates first."
                ]
            }
            
            raise HTTPException(status_code=400, detail=error_detail)
        
        # Step 2: Get managers
        generator = get_dataset_generator()
        embedder = get_embedding_manager()
        
        # Step 3: Check if dataset exists and generate if needed
        dataset_generated = False
        dataset_info = None
        
        if request.generate_dataset:
            # Check Redis stats for this intent
            stats = embedder.get_stats()
            existing_count = stats.get("intents", {}).get(intent, 0)
            
            logger.info(f"Existing embeddings for {intent}: {existing_count}")
            
            # Generate dataset if less than threshold
            if existing_count < 10:
                logger.info(f"Generating dataset for intent: {intent}")
                dataset_info = generator.generate_from_query(
                    query=request.query,
                    intent=intent,
                    slots=slots,
                    num_variations=request.num_examples
                )
                dataset_generated = True
                
                # Step 4: Embed the dataset to Redis
                logger.info("Embedding dataset to Redis...")
                
                # Read the generated dataset
                import pandas as pd
                import json
                csv_path = dataset_info["paths"]["csv"]
                df = pd.read_csv(csv_path)
                
                # Validate required columns (unified format: query,api,endpoint,request,response)
                if 'api' not in df.columns:
                    raise ValueError(f"Generated CSV missing 'api' column. Expected format: query,api,endpoint,request,response")
                
                # Prepare data for embedding (using unified format: query,api,endpoint,request,response)
                queries = df['query'].tolist()
                intents = df['api'].tolist()  # 'api' column contains the intent
                
                # Parse slots from 'request' column
                slots_list = []
                responses = []
                for idx, row in df.iterrows():
                    # Parse request (slots) from JSON string
                    slots = {}
                    if 'request' in df.columns and pd.notna(row['request']):
                        try:
                            if isinstance(row['request'], str):
                                request_data = json.loads(row['request'])
                                if isinstance(request_data, dict):
                                    slots = request_data
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON in request at row {idx}: {row['request']}")
                            slots = {}
                    slots_list.append(slots)
                    
                    # Get response field
                    if 'response' in df.columns and pd.notna(row['response']):
                        responses.append(row['response'])
                    else:
                        responses.append(json.dumps({"definition": f"API endpoint for {intents[idx]}"}))
                
                # Batch upsert to Redis
                upsert_result = embedder.upsert_batch(
                    queries=queries,
                    intents=intents,
                    slots_list=slots_list,
                    api_names=intents,  # Use api column value
                    endpoints=df['endpoint'].tolist() if 'endpoint' in df.columns else None,
                    responses=responses
                )
                
                dataset_info["redis_keys"] = upsert_result["total"]
                dataset_info["new_embeddings"] = upsert_result["new_count"]
                dataset_info["skipped_duplicates"] = upsert_result["skipped_count"]
                logger.info(f"Embedded {upsert_result['total']} entries to Redis ({upsert_result['new_count']} new, {upsert_result['skipped_count']} skipped)")
            else:
                logger.info(f"Sufficient embeddings exist for {intent}. Skipping generation.")
        
        # Step 5: Perform vector search
        logger.info("Performing vector search...")
        search_results = embedder.search(
            query=request.query,
            top_k=request.top_k,
            intent_filter=None  # Don't filter to allow cross-intent matches
        )
        
        # Step 6: Format best matches
        best_matches = []
        for result in search_results:
            best_matches.append({
                "api": result["intent"],
                "score": result["similarity"],
                "confidence": result.get("confidence", 1.0)
            })
        
        # Deduplicate by API
        seen_apis = set()
        unique_matches = []
        for match in best_matches:
            if match["api"] not in seen_apis:
                seen_apis.add(match["api"])
                unique_matches.append(match)
        
        logger.info(f"Found {len(unique_matches)} unique API matches")
        
        # Step 7: Build response with download URL if dataset was generated
        dataset_download_url = None
        if dataset_generated and dataset_info:
            # Create download URL for the generated CSV
            csv_filename = os.path.basename(dataset_info["paths"]["csv"])
            dataset_download_url = f"/api/v1/dataset/download-file/{csv_filename}"
        
        response = QueryResponse(
            query=request.query,
            intent=intent,
            slots=slots,
            confidence=confidence,
            best_matches=unique_matches,
            dataset_generated=dataset_generated,
            dataset_info=dataset_info,
            search_results=search_results[:request.top_k],
            dataset_download_url=dataset_download_url
        )
        
        # Step 8: Update test run with results
        if test_run_id:
            try:
                processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                best_match = unique_matches[0] if unique_matches else None
                
                test_run = await db.get(TestRun, test_run_id)
                if test_run:
                    test_run.status = "passed"
                    test_run.confidence = confidence
                    test_run.tests_count = len(unique_matches)
                    test_run.processing_time_ms = processing_time
                    test_run.best_match_api = best_match["api"] if best_match else None
                    test_run.best_match_score = best_match["score"] if best_match else None
                    test_run.search_results_count = len(search_results)
                    test_run.dataset_generated = dataset_generated
                    test_run.updated_at = datetime.utcnow()
                    
                    await db.commit()
                    logger.info(f"Updated test run {test_run_id} with status 'passed'")
            except Exception as e:
                logger.warning(f"Failed to update test run {test_run_id}: {e}")
                # Don't fail the request if test run update fails
        
        return response
        
    except HTTPException:
        # Update test run with failed status
        if test_run_id:
            try:
                test_run = await db.get(TestRun, test_run_id)
                if test_run:
                    test_run.status = "failed"
                    test_run.error_message = "Query processing failed"
                    test_run.updated_at = datetime.utcnow()
                    await db.commit()
            except Exception as e:
                logger.warning(f"Failed to update test run status: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        
        # Update test run with failed status
        if test_run_id:
            try:
                test_run = await db.get(TestRun, test_run_id)
                if test_run:
                    test_run.status = "failed"
                    test_run.error_message = str(e)[:500]  # Limit error message length
                    test_run.updated_at = datetime.utcnow()
                    await db.commit()
            except Exception as db_error:
                logger.warning(f"Failed to update test run status: {db_error}")
        
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/stats")
async def get_stats():
    """
    Get statistics about the vector database
    
    Returns:
        Database statistics including counts by intent
    """
    try:
        embedder = get_embedding_manager()
        stats = embedder.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex/{intent}")
async def reindex_intent(intent: str, background_tasks: BackgroundTasks):
    """
    Reindex a specific intent by regenerating embeddings
    
    Args:
        intent: API intent to reindex
        
    Returns:
        Status message
    """
    try:
        logger.info(f"Reindexing intent: {intent}")
        
        generator = get_dataset_generator()
        embedder = get_embedding_manager()
        
        # Delete existing embeddings
        deleted = embedder.delete_by_intent(intent)
        logger.info(f"Deleted {deleted} existing embeddings")
        
        # Regenerate dataset
        dataset_info = generator.generate_dataset(
            intent=intent,
            num_examples=100,
            use_gemini=True,
            merge_existing=False
        )
        
        # Re-embed (using unified format: query,api,endpoint,request,response)
        import pandas as pd
        import json
        csv_path = dataset_info["paths"]["csv"]
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        if 'api' not in df.columns:
            raise ValueError(f"Generated CSV missing 'api' column. Expected format: query,api,endpoint,request,response")
        
        queries = df['query'].tolist()
        intents = df['api'].tolist()  # 'api' column contains the intent
        
        # Parse slots from 'request' column
        slots_list = []
        responses = []
        for idx, row in df.iterrows():
            # Parse request (slots) from JSON string
            slots = {}
            if 'request' in df.columns and pd.notna(row['request']):
                try:
                    if isinstance(row['request'], str):
                        request_data = json.loads(row['request'])
                        if isinstance(request_data, dict):
                            slots = request_data
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in request at row {idx}: {row['request']}")
                    slots = {}
            slots_list.append(slots)
            
            # Get response field
            if 'response' in df.columns and pd.notna(row['response']):
                responses.append(row['response'])
            else:
                responses.append(json.dumps({"definition": f"API endpoint for {intents[idx]}"}))
        
        upsert_result = embedder.upsert_batch(
            queries=queries,
            intents=intents,
            slots_list=slots_list,
            api_names=intents,  # Use api column value
            endpoints=df['endpoint'].tolist() if 'endpoint' in df.columns else None,
            responses=responses
        )
        
        return {
            "message": f"Reindexed {intent}",
            "deleted": deleted,
            "generated": len(df),
            "embedded": upsert_result["total"],
            "new_embeddings": upsert_result["new_count"],
            "skipped_duplicates": upsert_result["skipped_count"]
        }
        
    except Exception as e:
        logger.error(f"Error reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
