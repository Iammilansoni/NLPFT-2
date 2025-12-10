"""
Query API endpoint - Main entry point for natural language queries
Handles the complete pipeline: embed -> search
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from datetime import datetime
import os
from app.nlp.embedding_manager import get_embedding_manager
from app.core.logger import logger
from app.core.postgres import get_db
from app.models.schemas.query_schemas import QueryRequest, QueryResponse
from app.models.database_models import TestRun

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Process natural language query through vector search pipeline
    
    1. Perform vector search
    2. Return best matches with confidence
    
    Example:
        Input: "Authenticate my credentials for Milan and MS3ESD"
        Output: {
            "query": "...",
            "best_matches": [...]
        }
    """
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Get embedding manager
        embedder = get_embedding_manager()
        
        # Perform vector search
        logger.info("Performing vector search...")
        search_results = embedder.search(
            query=request.query,
            top_k=request.top_k,
            intent_filter=None  # Don't filter to allow cross-intent matches
        )
        
        # Format best matches
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
        
        response = QueryResponse(
            query=request.query,
            intent=None,
            slots={},
            confidence=0.0,
            best_matches=unique_matches,
            dataset_generated=False,
            dataset_info=None,
            search_results=search_results[:request.top_k],
            dataset_download_url=None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    Get statistics about the vector database and test runs
    
    Returns:
        Database statistics including counts by intent and execution metrics
    """
    try:
        embedder = get_embedding_manager()
        stats = embedder.get_stats()
        
        # Get execution stats from DB
        # Total runs
        result = await db.execute(select(func.count(TestRun.run_id)))
        total_runs = result.scalar() or 0
        
        # Success rate
        result = await db.execute(select(func.count(TestRun.run_id)).where(TestRun.status == 'passed'))
        passed_runs = result.scalar() or 0
        success_rate = (passed_runs / total_runs * 100) if total_runs > 0 else 0
        
        # Avg response time (duration_seconds)
        result = await db.execute(select(func.avg(TestRun.duration_seconds)).where(TestRun.duration_seconds != None))
        avg_response_time = result.scalar() or 0
        
        # Add to stats
        stats["total_runs"] = total_runs
        stats["success_rate"] = round(success_rate, 1)
        stats["avg_response_time"] = round(float(avg_response_time), 2) if avg_response_time else 0
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# DEPRECATED: This endpoint uses old generate_dataset method which no longer exists
# Use /api/v1/datasets/generate endpoint with template-based generation instead
# @router.post("/reindex/{intent}")
# async def reindex_intent(intent: str, background_tasks: BackgroundTasks):
#     """
#     Reindex a specific intent by regenerating embeddings
#     
#     Args:
#         intent: API intent to reindex
#         
#     Returns:
#         Status message
#     """
#     try:
#         logger.info(f"Reindexing intent: {intent}")
#         
#         generator = get_enterprise_dataset_generator()
#         embedder = get_embedding_manager()
#         
#         # Delete existing embeddings
#         deleted = embedder.delete_by_intent(intent)
#         logger.info(f"Deleted {deleted} existing embeddings")
#         
#         # Regenerate dataset - NOTE: generate_dataset method removed, use generate_dataset_from_template
#         dataset_info = await generator.generate_dataset_from_template(
#             intent=intent,
#             num_examples=100,
#         )
#         
#         # Re-embed (using unified format: query,api,endpoint,request,response)
#         import pandas as pd
#         import json
#         csv_path = dataset_info["paths"]["csv"]
#         df = pd.read_csv(csv_path)
#         
#         # Validate required columns
#         if 'api' not in df.columns:
#             raise ValueError(f"Generated CSV missing 'api' column. Expected format: query,api,endpoint,request,response")
#         
#         queries = df['query'].tolist()
#         intents = df['api'].tolist()  # 'api' column contains the intent
#         
#         # Parse slots from 'request' column
#         slots_list = []
#         responses = []
#         for idx, row in df.iterrows():
#             # Parse request (slots) from JSON string
#             slots = {}
#             if 'request' in df.columns and pd.notna(row['request']):
#                 try:
#                     if isinstance(row['request'], str):
#                         request_data = json.loads(row['request'])
#                         if isinstance(request_data, dict):
#                             slots = request_data
#                 except json.JSONDecodeError:
#                     logger.warning(f"Invalid JSON in request at row {idx}: {row['request']}")
#                     slots = {}
#             slots_list.append(slots)
#             
#             # Get response field
#             if 'response' in df.columns and pd.notna(row['response']):
#                 responses.append(row['response'])
#             else:
#                 responses.append(json.dumps({"definition": f"API endpoint for {intents[idx]}"}))
#         
#         upsert_result = embedder.upsert_batch(
#             queries=queries,
#             intents=intents,
#             slots_list=slots_list,
#             api_names=intents,  # Use api column value
#             endpoints=df['endpoint'].tolist() if 'endpoint' in df.columns else None,
#             responses=responses
#         )
#         
#         return {
#             "message": f"Reindexed {intent}",
#             "deleted": deleted,
#             "generated": len(df),
#             "embedded": upsert_result["total"],
#             "new_embeddings": upsert_result["new_count"],
#             "skipped_duplicates": upsert_result["skipped_count"]
#         }
#         
#     except Exception as e:
#         logger.error(f"Error reindexing: {e}")
#         raise HTTPException(status_code=500, detail=str(e))
