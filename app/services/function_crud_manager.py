"""
Unified CRUD Manager for NLPForge Functions.

This manager provides a simple interface for Create, Read, Update, Delete operations
on functions that automatically keeps both JSON file and MongoDB database in sync.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.services.function_sync_service import FunctionSyncService
from app.core.logger import logger


class FunctionCRUDManager:
    """Unified CRUD manager for functions with dual persistence."""
    
    def __init__(self):
        self.sync_service = FunctionSyncService()
        self._initialized = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def initialize(self):
        """Initialize the manager."""
        if not self._initialized:
            await self.sync_service.initialize()
            self._initialized = True
            logger.info("🎛️ CRUD Manager initialized")
    
    async def close(self):
        """Close the manager."""
        if self._initialized:
            await self.sync_service.close()
            self._initialized = False
            logger.info("🎛️ CRUD Manager closed")
    
    def _validate_function_data(self, function_data: Dict[str, Any]) -> Dict[str, str]:
        """Validate function data and return any errors."""
        errors = {}
        
        if not function_data.get("name"):
            errors["name"] = "Function name is required"
        
        if not function_data.get("templates"):
            errors["templates"] = "At least one template is required"
        
        if not isinstance(function_data.get("signature", {}), dict):
            errors["signature"] = "Signature must be a dictionary"
        
        # Validate template format
        templates = function_data.get("templates", [])
        for i, template in enumerate(templates):
            if not isinstance(template, str) or not template.strip():
                errors[f"template_{i}"] = f"Template {i+1} must be a non-empty string"
        
        return errors
    
    async def create_function(self, function_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new function.
        
        Args:
            function_data: Function definition
            
        Returns:
            Operation result with success status and details
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Validate input
            errors = self._validate_function_data(function_data)
            if errors:
                return {
                    "success": False,
                    "error": "Validation failed",
                    "details": errors
                }
            
            func_name = function_data["name"]
            
            # Check if function already exists
            existing = await self.get_function(func_name)
            if existing["success"]:
                return {
                    "success": False,
                    "error": f"Function '{func_name}' already exists",
                    "details": {"name": "Function name must be unique"}
                }
            
            # Add metadata
            now = datetime.now().isoformat()
            function_data.setdefault("created_by", "admin")
            function_data.setdefault("updated_by", "admin")
            function_data.setdefault("usage_count", 0)
            function_data.setdefault("is_active", True)
            function_data.setdefault("category", "general")
            
            # Create the function
            success = await self.sync_service.create_function(function_data)
            
            if success:
                return {
                    "success": True,
                    "message": f"Function '{func_name}' created successfully",
                    "function": function_data
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create function"
                }
                
        except Exception as e:
            logger.error(f"❌ Error creating function: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_function(self, func_name: str) -> Dict[str, Any]:
        """
        Get a function by name.
        
        Args:
            func_name: Name of the function
            
        Returns:
            Function data or error
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if not self.sync_service.repo:
                return {"success": False, "error": "Repository not initialized"}
            
            func = await self.sync_service.repo.get_function_by_name(func_name)
            if func:
                return {
                    "success": True,
                    "function": self.sync_service.dict_function_to_json(func)
                }
            else:
                return {
                    "success": False,
                    "error": f"Function '{func_name}' not found"
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting function: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_function(self, func_name: str, function_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing function.
        
        Args:
            func_name: Name of the function to update
            function_data: Updated function definition
            
        Returns:
            Operation result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Validate input
            errors = self._validate_function_data(function_data)
            if errors:
                return {
                    "success": False,
                    "error": "Validation failed",
                    "details": errors
                }
            
            # Check if function exists
            existing = await self.get_function(func_name)
            if not existing["success"]:
                return {
                    "success": False,
                    "error": f"Function '{func_name}' not found"
                }
            
            # Preserve some metadata from existing function
            existing_data = existing["function"]
            function_data["created_by"] = existing_data.get("created_by", "admin")
            function_data["usage_count"] = existing_data.get("usage_count", 0)
            function_data.setdefault("updated_by", "admin")
            function_data.setdefault("is_active", True)
            
            # Update the function
            success = await self.sync_service.update_function(func_name, function_data)
            
            if success:
                return {
                    "success": True,
                    "message": f"Function '{func_name}' updated successfully",
                    "function": function_data
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update function"
                }
                
        except Exception as e:
            logger.error(f"❌ Error updating function: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_function(self, func_name: str) -> Dict[str, Any]:
        """
        Delete a function.
        
        Args:
            func_name: Name of the function to delete
            
        Returns:
            Operation result
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Check if function exists
            existing = await self.get_function(func_name)
            if not existing["success"]:
                return {
                    "success": False,
                    "error": f"Function '{func_name}' not found"
                }
            
            # Delete the function
            success = await self.sync_service.delete_function(func_name)
            
            if success:
                return {
                    "success": True,
                    "message": f"Function '{func_name}' deleted successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to delete function"
                }
                
        except Exception as e:
            logger.error(f"❌ Error deleting function: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_functions(self, category: Optional[str] = None, active_only: bool = True) -> Dict[str, Any]:
        """
        List all functions, optionally filtered by category.
        
        Args:
            category: Optional category filter
            active_only: Only return active functions
            
        Returns:
            List of functions
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if not self.sync_service.repo:
                return {"success": False, "error": "Repository not initialized"}
            
            if active_only:
                db_functions = await self.sync_service.repo.list_all_active_functions()
            else:
                # Get all functions (would need to add this method to repository)
                db_functions = await self.sync_service.repo.list_all_active_functions()
            
            # Convert to JSON format
            json_functions = [
                self.sync_service.dict_function_to_json(func) 
                for func in db_functions
            ]
            
            # Filter by category if specified
            if category:
                json_functions = [
                    func for func in json_functions 
                    if func.get("category", "").lower() == category.lower()
                ]
            
            # Sort by category then name
            json_functions.sort(key=lambda x: (x.get("category", ""), x["name"]))
            
            return {
                "success": True,
                "functions": json_functions,
                "count": len(json_functions)
            }
            
        except Exception as e:
            logger.error(f"❌ Error listing functions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_functions(self, query: str, search_in: List[str] = None) -> Dict[str, Any]:
        """
        Search functions by query string.
        
        Args:
            query: Search query
            search_in: Fields to search in ('name', 'templates', 'description')
            
        Returns:
            Matching functions
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            search_in = search_in or ['name', 'templates', 'description']
            query_lower = query.lower()
            
            # Get all functions
            all_functions = await self.list_functions(active_only=False)
            if not all_functions["success"]:
                return all_functions
            
            matching_functions = []
            for func in all_functions["functions"]:
                match = False
                
                # Search in name
                if 'name' in search_in and query_lower in func.get("name", "").lower():
                    match = True
                
                # Search in description  
                if 'description' in search_in and query_lower in func.get("description", "").lower():
                    match = True
                
                # Search in templates
                if 'templates' in search_in:
                    for template in func.get("templates", []):
                        if query_lower in template.lower():
                            match = True
                            break
                
                if match:
                    matching_functions.append(func)
            
            return {
                "success": True,
                "functions": matching_functions,
                "count": len(matching_functions),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"❌ Error searching functions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_categories(self) -> Dict[str, Any]:
        """Get all available function categories with counts."""
        if not self._initialized:
            await self.initialize()
        
        try:
            all_functions = await self.list_functions(active_only=False)
            if not all_functions["success"]:
                return all_functions
            
            categories = {}
            for func in all_functions["functions"]:
                category = func.get("category", "general")
                if category not in categories:
                    categories[category] = {
                        "name": category,
                        "count": 0,
                        "template_count": 0
                    }
                categories[category]["count"] += 1
                categories[category]["template_count"] += len(func.get("templates", []))
            
            return {
                "success": True,
                "categories": list(categories.values()),
                "total_categories": len(categories)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting categories: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_status(self) -> Dict[str, Any]:
        """Get synchronization status between JSON and DB."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.sync_service.get_sync_status()
        except Exception as e:
            logger.error(f"❌ Error getting sync status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def force_sync(self, direction: str = "both") -> Dict[str, Any]:
        """
        Force synchronization between JSON and DB.
        
        Args:
            direction: 'json_to_db', 'db_to_json', or 'both'
            
        Returns:
            Sync results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            if direction == "json_to_db":
                result = await self.sync_service.sync_json_to_db("merge")
                return {
                    "success": True,
                    "message": "Synced JSON to database",
                    "stats": {"created": result[0], "updated": result[1], "skipped": result[2]}
                }
            elif direction == "db_to_json":
                result = await self.sync_service.sync_db_to_json()
                return {
                    "success": True,
                    "message": "Synced database to JSON",
                    "stats": {"functions_synced": result}
                }
            elif direction == "both":
                result = await self.sync_service.full_sync("db")
                return {
                    "success": True,
                    "message": "Full bidirectional sync completed",
                    "stats": result
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid direction. Use 'json_to_db', 'db_to_json', or 'both'"
                }
                
        except Exception as e:
            logger.error(f"❌ Error during sync: {e}")
            return {
                "success": False,
                "error": str(e)
            }