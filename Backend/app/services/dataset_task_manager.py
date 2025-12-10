"""
Dataset Task Manager - Manages async dataset generation tasks with progress tracking
"""

import uuid
from datetime import datetime
from typing import Dict, Optional, List, Callable
from app.core.logger import logger

# In-memory task store (in production, use Redis or database)
_task_store: Dict[str, Dict] = {}
# Progress callbacks for SSE
_progress_callbacks: Dict[str, List[Callable]] = {}


class DatasetTaskManager:
    """Manages dataset generation tasks with progress tracking"""
    
    @staticmethod
    def create_task() -> str:
        """Create a new task and return task_id"""
        task_id = str(uuid.uuid4())
        _task_store[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "message": "Task created",
            "progress": 0,
            "current_step": "initializing",
            "steps": [],
            "created_at": datetime.utcnow().isoformat() + "Z",  # Add Z suffix to indicate UTC
            "completed_at": None,
            "statistics": None,
            "files": None,
            "error": None
        }
        _progress_callbacks[task_id] = []
        logger.info(f"Created task: {task_id}")
        return task_id
    
    @staticmethod
    def update_task(task_id: str, **kwargs):
        """Update task status and notify callbacks"""
        if task_id not in _task_store:
            raise ValueError(f"Task {task_id} not found")
        
        _task_store[task_id].update(kwargs)
        
        # Log progress updates
        if "progress" in kwargs or "current_step" in kwargs:
            progress = _task_store[task_id].get("progress", 0)
            step = _task_store[task_id].get("current_step", "")
            message = _task_store[task_id].get("message", "")
            logger.info(f"Task {task_id}: {progress}% - {step} - {message}")
        elif "status" in kwargs:
            logger.info(f"Task {task_id} status: {kwargs['status']}")
        
        # Notify all registered callbacks
        for callback in _progress_callbacks.get(task_id, []):
            try:
                callback(_task_store[task_id])
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")
    
    @staticmethod
    def add_step(task_id: str, step_name: str, step_status: str = "running"):
        """Add a step to the task's step history"""
        if task_id not in _task_store:
            return
        
        if "steps" not in _task_store[task_id]:
            _task_store[task_id]["steps"] = []
        
        _task_store[task_id]["steps"].append({
            "name": step_name,
            "status": step_status,
            "timestamp": datetime.utcnow().isoformat()
        })
        _task_store[task_id]["current_step"] = step_name
    
    @staticmethod
    def update_progress(task_id: str, progress: int, message: str = None, current_step: str = None):
        """Update task progress (0-100)"""
        if task_id not in _task_store:
            return
        
        updates = {"progress": min(100, max(0, progress))}
        if message:
            updates["message"] = message
        if current_step:
            updates["current_step"] = current_step
        
        DatasetTaskManager.update_task(task_id, **updates)
    
    @staticmethod
    def register_callback(task_id: str, callback: Callable):
        """Register a callback for progress updates"""
        if task_id not in _progress_callbacks:
            _progress_callbacks[task_id] = []
        _progress_callbacks[task_id].append(callback)
    
    @staticmethod
    def unregister_callback(task_id: str, callback: Callable):
        """Unregister a progress callback"""
        if task_id in _progress_callbacks and callback in _progress_callbacks[task_id]:
            _progress_callbacks[task_id].remove(callback)
    
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
            if task_id in _progress_callbacks:
                del _progress_callbacks[task_id]
            logger.info(f"Deleted task: {task_id}")


def get_task_manager() -> DatasetTaskManager:
    """Get task manager instance"""
    return DatasetTaskManager()

