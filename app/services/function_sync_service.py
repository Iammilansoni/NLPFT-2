"""
Function Synchronization Service for NLPForge Rule Engine.

This service provides bidirectional synchronization between:
1. storage/function_dictionary.json (JSON file)
2. MongoDB database

Features:
- Automatic sync on Rule Engine startup
- Bidirectional sync (JSON ↔ MongoDB)
- CRUD operations that update both sources
- Conflict resolution and merge strategies
- Backup and restore functionality
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from app.models.dictionary_models import DictionaryFunction
from app.core.database import db_manager
from app.core.dictionary_repository import DictionaryRepository
from app.core.logger import logger


class FunctionSyncService:
    """Service for synchronizing functions between JSON file and MongoDB."""
    
    def __init__(self, json_path: str = "storage/function_dictionary.json"):
        self.json_path = Path(json_path)
        self.repo: Optional[DictionaryRepository] = None
        
    async def initialize(self):
        """Initialize the service with database connection."""
        if not hasattr(db_manager, 'database') or db_manager.database is None:  # type: ignore
            await db_manager.connect()
        self.repo = DictionaryRepository(db_manager.database)  # type: ignore
        logger.info("🔄 Function Sync Service initialized")
    
    async def close(self):
        """Close the service."""
        if hasattr(db_manager, 'database') and db_manager.database is not None:  # type: ignore
            await db_manager.disconnect()
        logger.info("🔄 Function Sync Service closed")
    
    def load_json_functions(self) -> List[Dict[str, Any]]:
        """Load functions from JSON file."""
        if not self.json_path.exists():
            logger.warning(f"📄 JSON file not found: {self.json_path}")
            return []
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"📥 Loaded {len(data)} functions from JSON")
                return data
        except Exception as e:
            logger.error(f"❌ Error loading JSON file: {e}")
            return []
    
    def save_json_functions(self, functions: List[Dict[str, Any]]):
        """Save functions to JSON file."""
        try:
            # Create backup first
            if self.json_path.exists():
                backup_path = self.json_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                self.json_path.rename(backup_path)
                logger.info(f"📄 Created backup: {backup_path}")
            
            # Ensure directory exists
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save new data
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(functions, f, indent=2, ensure_ascii=False)
                logger.info(f"💾 Saved {len(functions)} functions to JSON")
                
        except Exception as e:
            logger.error(f"❌ Error saving JSON file: {e}")
            raise
    
    def json_to_dict_function(self, json_func: Dict[str, Any]) -> DictionaryFunction:
        """Convert JSON function to DictionaryFunction model."""
        return DictionaryFunction(
            name=json_func.get("name", ""),
            display_name=json_func.get("display_name", json_func.get("name", "")),
            description=json_func.get("description", ""),
            signature=json_func.get("signature", {}),
            templates=json_func.get("templates", []),
            category=json_func.get("category", "general"),
            is_active=json_func.get("is_active", True),
            created_by=json_func.get("created_by", "sync_service"),
            updated_by=json_func.get("updated_by", "sync_service"),
            usage_count=json_func.get("usage_count", 0),
            last_used=None
        )
    
    def dict_function_to_json(self, func: DictionaryFunction) -> Dict[str, Any]:
        """Convert DictionaryFunction model to JSON format."""
        return {
            "id": func.name,
            "name": func.name,
            "display_name": func.display_name or func.name,
            "description": func.description or "",
            "signature": func.signature or {},
            "templates": func.templates or [],
            "category": func.category or "general",
            "examples": [
                f"Example: {template}" for template in (func.templates[:2] if func.templates else [])
            ],
            "created_by": func.created_by or "system",
            "updated_by": func.updated_by or "system",
            "usage_count": func.usage_count or 0,
            "is_active": func.is_active
        }
    
    async def sync_json_to_db(self, merge_strategy: str = "overwrite") -> Tuple[int, int, int]:
        """
        Sync functions from JSON file to MongoDB.
        
        Args:
            merge_strategy: 'overwrite', 'skip_existing', or 'merge'
            
        Returns:
            Tuple of (created, updated, skipped) counts
        """
        if not self.repo:
            raise RuntimeError("Service not initialized")
        
        json_functions = self.load_json_functions()
        if not json_functions:
            return 0, 0, 0
        
        created = updated = skipped = 0
        
        for json_func in json_functions:
            try:
                func_name = json_func.get("name")
                if not func_name:
                    logger.warning("⚠️ Function without name, skipping")
                    skipped += 1
                    continue
                
                # Check if function exists in DB
                existing = await self.repo.get_function_by_name(func_name)
                dict_func = self.json_to_dict_function(json_func)
                
                if existing:
                    if merge_strategy == "skip_existing":
                        logger.info(f"⏭️ Skipping existing function: {func_name}")
                        skipped += 1
                        continue
                    elif merge_strategy == "merge":
                        # Merge templates and preserve metadata
                        existing_templates = set(existing.templates or [])
                        new_templates = set(dict_func.templates or [])
                        merged_templates = list(existing_templates | new_templates)
                        
                        dict_func.templates = merged_templates
                        dict_func.created_by = existing.created_by
                        dict_func.usage_count = existing.usage_count
                        dict_func.last_used = existing.last_used
                    
                    # Update existing function
                    await self.repo.update_function(func_name, self.dict_function_to_json(dict_func))
                    logger.info(f"🔄 Updated function: {func_name}")
                    updated += 1
                else:
                    # Create new function
                    await self.repo.create_function(dict_func)
                    logger.info(f"➕ Created function: {func_name}")
                    created += 1
                    
            except Exception as e:
                logger.error(f"❌ Error syncing function {json_func.get('name', 'unknown')}: {e}")
                skipped += 1
        
        logger.info(f"📊 JSON→DB sync completed: {created} created, {updated} updated, {skipped} skipped")
        return created, updated, skipped
    
    async def sync_db_to_json(self) -> int:
        """
        Sync functions from MongoDB to JSON file.
        
        Returns:
            Number of functions synced
        """
        if not self.repo:
            raise RuntimeError("Service not initialized")
        
        db_functions = await self.repo.list_all_active_functions()
        json_functions = [self.dict_function_to_json(func) for func in db_functions]
        
        # Sort by category then name for consistency
        json_functions.sort(key=lambda x: (x.get("category", ""), x["name"]))
        
        self.save_json_functions(json_functions)
        logger.info(f"📊 DB→JSON sync completed: {len(json_functions)} functions")
        
        return len(json_functions)
    
    async def full_sync(self, primary_source: str = "db") -> Dict[str, Any]:
        """
        Perform full bidirectional sync.
        
        Args:
            primary_source: 'db' or 'json' - which source takes precedence for conflicts
            
        Returns:
            Sync statistics
        """
        if not self.repo:
            raise RuntimeError("Service not initialized")
        
        logger.info(f"🔄 Starting full sync with primary source: {primary_source}")
        
        if primary_source == "db":
            # DB is primary: sync DB to JSON
            json_count = await self.sync_db_to_json()
            return {
                "primary_source": "db",
                "json_functions_updated": json_count,
                "db_functions_updated": 0
            }
        else:
            # JSON is primary: sync JSON to DB with merge strategy
            created, updated, skipped = await self.sync_json_to_db("merge")
            return {
                "primary_source": "json",
                "db_functions_created": created,
                "db_functions_updated": updated,
                "db_functions_skipped": skipped
            }
    
    async def create_function(self, function_data: Dict[str, Any]) -> bool:
        """
        Create a function in both JSON and DB.
        
        Args:
            function_data: Function definition in JSON format
            
        Returns:
            True if successful
        """
        if not self.repo:
            raise RuntimeError("Service not initialized")
        
        try:
            func_name = function_data.get("name")
            if not func_name:
                raise ValueError("Function name is required")
            
            # Create in DB first
            dict_func = self.json_to_dict_function(function_data)
            await self.repo.create_function(dict_func)
            logger.info(f"➕ Created function in DB: {func_name}")
            
            # Update JSON file
            await self.sync_db_to_json()
            logger.info(f"➕ Created function in JSON: {func_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating function: {e}")
            return False
    
    async def update_function(self, func_name: str, function_data: Dict[str, Any]) -> bool:
        """
        Update a function in both JSON and DB.
        
        Args:
            func_name: Name of the function to update
            function_data: Updated function definition
            
        Returns:
            True if successful
        """
        if not self.repo:
            raise RuntimeError("Service not initialized")
        
        try:
            # Update in DB first
            dict_func = self.json_to_dict_function(function_data)
            await self.repo.update_function(func_name, self.dict_function_to_json(dict_func))
            logger.info(f"🔄 Updated function in DB: {func_name}")
            
            # Update JSON file
            await self.sync_db_to_json()
            logger.info(f"🔄 Updated function in JSON: {func_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error updating function: {e}")
            return False
    
    async def delete_function(self, func_name: str) -> bool:
        """
        Delete a function from both JSON and DB.
        
        Args:
            func_name: Name of the function to delete
            
        Returns:
            True if successful
        """
        if not self.repo:
            raise RuntimeError("Service not initialized")
        
        try:
            # First get the function by name to get its ID
            function = await self.repo.get_function_by_name(func_name)
            if not function:
                logger.error(f"❌ Function '{func_name}' not found for deletion")
                return False
            
            # Delete from DB using the function ID
            success = await self.repo.delete_function(str(function.id))
            if not success:
                logger.error(f"❌ Failed to delete function '{func_name}' from DB")
                return False
            
            logger.info(f"🗑️ Deleted function from DB: {func_name}")
            
            # Update JSON file
            await self.sync_db_to_json()
            logger.info(f"🗑️ Removed function from JSON: {func_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error deleting function: {e}")
            return False
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get synchronization status between JSON and DB."""
        if not self.repo:
            raise RuntimeError("Service not initialized")
        
        try:
            # Load both sources
            json_functions = self.load_json_functions()
            db_functions = await self.repo.list_all_active_functions()
            
            # Create name sets for comparison
            json_names = {func.get("name") for func in json_functions if func.get("name")}
            db_names = {func.name for func in db_functions}
            
            # Calculate differences
            only_in_json = json_names - db_names
            only_in_db = db_names - json_names
            in_both = json_names & db_names
            
            return {
                "json_count": len(json_functions),
                "db_count": len(db_functions),
                "in_sync": len(only_in_json) == 0 and len(only_in_db) == 0,
                "common_functions": len(in_both),
                "only_in_json": list(only_in_json),
                "only_in_db": list(only_in_db),
                "sync_needed": len(only_in_json) > 0 or len(only_in_db) > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting sync status: {e}")
            return {"error": str(e)}


# Convenience functions for easy usage
async def sync_functions_startup():
    """Auto-sync functions on startup - call from Rule Engine initialization."""
    service = FunctionSyncService()
    try:
        await service.initialize()
        
        # Check sync status first
        status = await service.get_sync_status()
        if status.get("sync_needed", False):
            logger.info("🔄 Functions out of sync, performing auto-sync...")
            result = await service.full_sync("db")  # DB is primary source
            logger.info(f"✅ Auto-sync completed: {result}")
        else:
            logger.info("✅ Functions already in sync")
            
    except Exception as e:
        logger.error(f"❌ Auto-sync failed: {e}")
    finally:
        await service.close()


async def quick_sync_json_to_db():
    """Quick function to sync JSON to DB."""
    service = FunctionSyncService()
    try:
        await service.initialize()
        result = await service.sync_json_to_db("merge")
        logger.info(f"✅ Quick sync completed: {result}")
        return result
    finally:
        await service.close()


async def quick_sync_db_to_json():
    """Quick function to sync DB to JSON."""
    service = FunctionSyncService()
    try:
        await service.initialize()
        result = await service.sync_db_to_json()
        logger.info(f"✅ Quick sync completed: {result} functions")
        return result
    finally:
        await service.close()