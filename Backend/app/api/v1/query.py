"""
Query API endpoint - Main entry point for natural language queries
Handles the complete pipeline: parse -> generate dataset -> embed -> search
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import os
from app.nlp.query_parser import parse_query
from app.nlp.dataset_generator import get_dataset_generator
from app.nlp.embedding_manager import get_embedding_manager
from app.services.template_service import get_template_service
from app.core.logger import logger
from app.core.postgres import get_db
from app.models.schemas import QueryRequest, QueryResponse

router = APIRouter()


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
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Step 1: Parse query
        parsed = parse_query(request.query)
        intent = parsed["intent"]
        slots = parsed["slots"]
        confidence = parsed["confidence"]
        
        logger.info(f"Parsed - Intent: {intent}, Confidence: {confidence:.2f}, Slots: {slots}")
        
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
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
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
