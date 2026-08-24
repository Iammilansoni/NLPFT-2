"""
Dataset Ingestor - Ingests CSV datasets into Redis vector database
Supports both old format (api column) and new format (intent column)
"""

import json
from typing import Dict, List

import pandas as pd

from app.core.logger import logger
from app.nlp.embedding_manager import get_embedding_manager


def ingest_csv_to_redis(csv_path: str, clear_existing: bool = False) -> Dict:
    """
    Ingest a CSV dataset into Redis vector database
    
    Args:
        csv_path: Path to CSV file
        clear_existing: If True, clear all existing embeddings before ingestion
        
    Returns:
        Dictionary with ingestion statistics
        
    Expected CSV format (matching csv_dataset.csv):
        query,api,endpoint,request,response
    """
    try:
        logger.info(f"Starting ingestion from {csv_path}")
        
        if clear_existing:
            logger.warning("Clearing all existing embeddings as requested")
            embedder = get_embedding_manager()
            embedder.clear_all_embeddings()
        df = pd.read_csv(csv_path)
        df = df.dropna(subset=['query'])  
        
        required_cols = ['query', 'api']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}. Expected format: query,api,endpoint,request,response")
        
        embedder = get_embedding_manager()
        
        queries = df['query'].astype(str).tolist()
        intents = df['api'].astype(str).tolist()  
        api_names = intents 
       
        slots_list = []
        for idx, row in df.iterrows():
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
        
        if 'endpoint' in df.columns:
            endpoints = df['endpoint'].tolist()
        else:
            endpoints = [f"<base_url>/api/{intent}" for intent in intents]
        
        responses = []
        if 'response' in df.columns:
            responses = df['response'].tolist()
        else:
            responses = [json.dumps({"definition": f"API endpoint for {intent}"}) for intent in intents]
        
        logger.info(f"Upserting {len(queries)} entries to Redis (existing embeddings will be preserved)...")
        upsert_result = embedder.upsert_batch(
            queries=queries,
            intents=intents,
            slots_list=slots_list,
            api_names=api_names,
            endpoints=endpoints,
            responses=responses
        )
        
        result = {
            "success": True,
            "count": upsert_result["total"],
            "file": csv_path,
            "intents": list(set(intents)),
            "new_embeddings": upsert_result["new_count"],
            "skipped_duplicates": upsert_result["skipped_count"]
        }
        
        logger.info(f"Successfully ingested {upsert_result['total']} entries ({upsert_result['new_count']} new, {upsert_result['skipped_count']} skipped)")
        return result
        
    except Exception as e:
        logger.error(f"Error ingesting CSV: {e}", exc_info=True)
        return {
            "success": False,
            "count": 0,
            "error": str(e)
        }


def ingest_multiple_csvs(csv_paths: List[str]) -> Dict:
    """
    Ingest multiple CSV files into Redis
    
    Args:
        csv_paths: List of CSV file paths
        
    Returns:
        Dictionary with aggregated statistics
    """
    total_count = 0
    failed_files = []
    all_intents = set()
    
    for csv_path in csv_paths:
        result = ingest_csv_to_redis(csv_path)
        if result["success"]:
            total_count += result["count"]
            all_intents.update(result.get("intents", []))
        else:
            failed_files.append(csv_path)
    
    return {
        "success": len(failed_files) == 0,
        "total_count": total_count,
        "files_processed": len(csv_paths) - len(failed_files),
        "files_failed": len(failed_files),
        "failed_files": failed_files,
        "intents": list(all_intents)
    }
