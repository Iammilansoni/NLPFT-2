"""
Dataset Ingestor - Ingests CSV datasets into Redis vector database
"""

import pandas as pd
import json
from typing import Dict, List
from app.nlp.embedding_manager import get_embedding_manager
from app.core.logger import logger


def ingest_csv_to_redis(csv_path: str) -> Dict:
    """
    Ingest a CSV dataset into Redis vector database
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Dictionary with ingestion statistics
        
    Expected CSV format:
        query,intent,slots,api_name,endpoint
        "Login with username admin","login","{\"username\":\"admin\"}","login","/api/login"
    """
    try:
        logger.info(f"Starting ingestion from {csv_path}")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Validate required columns
        required_cols = ['query', 'intent']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Get embedding manager
        embedder = get_embedding_manager()
        
        # Prepare data
        queries = df['query'].tolist()
        intents = df['intent'].tolist()
        
        # Parse slots
        slots_list = []
        for idx, row in df.iterrows():
            if 'slots' in df.columns and pd.notna(row['slots']):
                try:
                    if isinstance(row['slots'], str):
                        slots_list.append(json.loads(row['slots']))
                    else:
                        slots_list.append(row['slots'])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in slots at row {idx}: {row['slots']}")
                    slots_list.append({})
            else:
                slots_list.append({})
        
        # Get optional fields
        api_names = df['api_name'].tolist() if 'api_name' in df.columns else None
        endpoints = df['endpoint'].tolist() if 'endpoint' in df.columns else None
        
        # Batch upsert to Redis
        logger.info(f"Upserting {len(queries)} entries to Redis...")
        redis_keys = embedder.upsert_batch(
            queries=queries,
            intents=intents,
            slots_list=slots_list,
            api_names=api_names,
            endpoints=endpoints
        )
        
        result = {
            "success": True,
            "count": len(redis_keys),
            "file": csv_path,
            "intents": list(set(intents))
        }
        
        logger.info(f"Successfully ingested {len(redis_keys)} entries")
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
