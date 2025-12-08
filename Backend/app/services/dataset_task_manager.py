"""
Dataset Task Manager - Manages async dataset generation tasks
"""

import uuid
from datetime import datetime
from typing import Dict, Optional
from app.core.logger import logger

# In-memory task store (in production, use Redis or database)
_task_store: Dict[str, Dict] = {}


class DatasetTaskManager:
    """Manages dataset generation tasks"""
    
    @staticmethod
    def create_task() -> str:
        """Create a new task and return task_id"""
        task_id = str(uuid.uuid4())
        _task_store[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "message": "Task created",
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "statistics": None,
            "files": None,
            "error": None
        }
        logger.info(f"Created task: {task_id}")
        return task_id
    
    @staticmethod
    def update_task(task_id: str, **kwargs):
        """Update task status"""
        if task_id not in _task_store:
            raise ValueError(f"Task {task_id} not found")
        
        _task_store[task_id].update(kwargs)
        if "status" in kwargs:
            logger.info(f"Task {task_id} status: {kwargs['status']}")
    
    @staticmethod
    def get_task(task_id: str) -> Optional[Dict]:
        """Get task by ID"""
        return _task_store.get(task_id)
    
    @staticmethod
    def list_tasks() -> list:
        """List all tasks"""
        return list(_task_store.values())
    
    @staticmethod
    def delete_task(task_id: str):
        """Delete a task"""
        if task_id in _task_store:
            del _task_store[task_id]
            logger.info(f"Deleted task: {task_id}")


def get_task_manager() -> DatasetTaskManager:
    """Get task manager instance"""
    return DatasetTaskManager()

