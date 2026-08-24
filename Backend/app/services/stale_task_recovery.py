"""
Stale Task Recovery Service

On server startup, detects and resets datasets stuck in 'processing' state
(caused by server crashes or interrupted embedding jobs).

Resets them to 'pending' so they can be re-triggered by the user.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, update

logger = logging.getLogger("nlpforge")


async def recover_stale_embedding_tasks() -> int:
    """
    Find datasets stuck in 'processing' state and reset them to 'pending'.
    
    This handles the case where the server crashed mid-embedding,
    leaving datasets permanently in 'processing' with no active task.
    
    Returns:
        Number of datasets recovered
    """
    from app.core.postgres import db_manager
    from app.models.database_models import Dataset
    
    recovered = 0
    
    try:
        async with db_manager.session_factory() as db:
            # Find all datasets stuck in 'processing'
            result = await db.execute(
                select(Dataset).where(
                    Dataset.embedding_status == "processing"
                )
            )
            stale_datasets = result.scalars().all()
            
            if not stale_datasets:
                logger.debug("No stale embedding tasks found")
                return 0
            
            datasets_to_recover = []
            for dataset in stale_datasets:
                old_progress = dataset.embedding_progress or 0
                old_embedded = dataset.embedded_rows or 0
                
                dataset.embedding_status = "pending"
                dataset.embedding_error = (
                    f"Interrupted: reset after server restart "
                    f"(was {old_progress}% done, {old_embedded} rows embedded)"
                )
                
                logger.warning(
                    f"🔄 Recovering stale task: dataset {str(dataset.dataset_id)[:8]} "
                    f"was {old_progress}% complete ({old_embedded} rows embedded). "
                    f"Reset to 'pending'."
                )
                datasets_to_recover.append(dataset)
            
            await db.commit()
            recovered = len(datasets_to_recover)
            
    except Exception as e:
        logger.error(f"Stale task recovery failed: {e}", exc_info=True)
    
    return recovered
