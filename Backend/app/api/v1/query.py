"""
Query API endpoint - Main entry point for natural language queries
Handles the complete pipeline: parse -> generate dataset -> embed -> search
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from app.nlp.query_parser import parse_query
from app.nlp.dataset_generator import get_dataset_generator
from app.nlp.embedding_manager import get_embedding_manager
from app.services.template_service import get_template_service
from app.core.logger import logger

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


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
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
                
                # Prepare data for embedding
                queries = df['query'].tolist()
                intents = df['intent'].tolist()
                
                # Parse slots from JSON string
                slots_list = []
                for idx, row in df.iterrows():
                    if 'slots_json' in df.columns:
                        slots_list.append(json.loads(row['slots_json']))
                    elif 'slots' in df.columns:
                        if isinstance(row['slots'], str):
                            slots_list.append(json.loads(row['slots']))
                        else:
                            slots_list.append(row['slots'])
                    else:
                        slots_list.append({})
                
                # Batch upsert to Redis
                redis_keys = embedder.upsert_batch(
                    queries=queries,
                    intents=intents,
                    slots_list=slots_list,
                    api_names=df['api_name'].tolist() if 'api_name' in df.columns else None,
                    endpoints=df['endpoint'].tolist() if 'endpoint' in df.columns else None
                )
                
                dataset_info["redis_keys"] = len(redis_keys)
                logger.info(f"Embedded {len(redis_keys)} entries to Redis")
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
        
        # Step 7: Build response
        response = QueryResponse(
            query=request.query,
            intent=intent,
            slots=slots,
            confidence=confidence,
            best_matches=unique_matches,
            dataset_generated=dataset_generated,
            dataset_info=dataset_info,
            search_results=search_results[:request.top_k]
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
        
        # Re-embed
        import pandas as pd
        import json
        csv_path = dataset_info["paths"]["csv"]
        df = pd.read_csv(csv_path)
        
        queries = df['query'].tolist()
        intents = df['intent'].tolist()
        slots_list = []
        
        for idx, row in df.iterrows():
            if 'slots_json' in df.columns:
                slots_list.append(json.loads(row['slots_json']))
            elif 'slots' in df.columns:
                if isinstance(row['slots'], str):
                    slots_list.append(json.loads(row['slots']))
                else:
                    slots_list.append(row['slots'])
            else:
                slots_list.append({})
        
        redis_keys = embedder.upsert_batch(
            queries=queries,
            intents=intents,
            slots_list=slots_list
        )
        
        return {
            "message": f"Reindexed {intent}",
            "deleted": deleted,
            "generated": len(df),
            "embedded": len(redis_keys)
        }
        
    except Exception as e:
        logger.error(f"Error reindexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
