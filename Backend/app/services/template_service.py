"""
Template Service - Core service for managing API templates
Handles loading, caching, CRUD operations, and synchronization
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.core.postgres import APITemplate, AsyncSessionLocal
from app.services.template_loader import get_template_loader
from app.core.logger import logger
import json


class TemplateService:
    """
    Service for managing API templates across JSON, database, and cache
    """
    
    def __init__(self):
        self.loader = get_template_loader()
        self._memory_cache: Dict[str, Dict] = {}
    
    async def sync_from_json(self, json_path: str) -> Dict[str, int]:
        """
        Sync templates from api_template.json to PostgreSQL
        
        Args:
            json_path: Path to api_template.json file
            
        Returns:
            Dictionary with sync statistics
        """
        try:
            # Load from JSON
            templates = self.loader.load_from_json(json_path)
            
            stats = {
                "loaded": len(templates),
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "errors": 0
            }
            
            async with AsyncSessionLocal() as session:
                for template in templates:
                    try:
                        # Check if template exists
                        result = await session.execute(
                            select(APITemplate).where(APITemplate.intent == template["intent"])
                        )
                        existing = result.scalar_one_or_none()
                        
                        if existing:
                            # Update existing template
                            await self._update_template_db(session, existing, template)
                            stats["updated"] += 1
                            logger.info(f"Updated template: {template['intent']}")
                        else:
                            # Create new template
                            await self._create_template_db(session, template)
                            stats["created"] += 1
                            logger.info(f"Created template: {template['intent']}")
                        
                        # Update memory cache
                        self._memory_cache[template["intent"]] = template
                        
                    except Exception as e:
                        logger.error(f"Error syncing template {template.get('intent')}: {e}")
                        stats["errors"] += 1
                
                await session.commit()
            
            logger.info(f"✅ Template sync complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error syncing templates from JSON: {e}")
            raise
    
    async def _create_template_db(self, session: AsyncSession, template: Dict):
        """Create new template in database"""
        db_template = APITemplate(
            intent=template["intent"],
            api_name=template["api_name"],
            description=template.get("description", ""),
            endpoint=template["endpoint"],
            method=template["method"],
            fields=template["fields"],
            example_queries=template.get("example_queries", []),
            is_system=template.get("is_system", True),
            metadata_={
                "intent_keywords": template.get("intent_keywords", []),
                "slots_config": template.get("slots_config", {}),
                "version": template.get("version", 1),
                **template.get("metadata", {})
            }
        )
        session.add(db_template)
    
    async def _update_template_db(self, session: AsyncSession, existing: APITemplate, template: Dict):
        """Update existing template in database"""
        existing.api_name = template["api_name"]
        existing.description = template.get("description", "")
        existing.endpoint = template["endpoint"]
        existing.method = template["method"]
        existing.fields = template["fields"]
        existing.example_queries = template.get("example_queries", [])
        
        # Merge metadata_
        current_meta = existing.metadata_ or {}
        current_meta.update({
            "intent_keywords": template.get("intent_keywords", []),
            "slots_config": template.get("slots_config", {}),
            "version": template.get("version", 1),
            **template.get("metadata", {})
        })
        existing.metadata_ = current_meta
    
    async def load_all_templates(self) -> Dict[str, Dict]:
        """
        Load all templates from database into memory cache
        
        Returns:
            Dictionary of templates keyed by intent
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(APITemplate))
                db_templates = result.scalars().all()
                
                self._memory_cache.clear()
                
                for db_template in db_templates:
                    template = self._db_to_dict(db_template)
                    self._memory_cache[template["intent"]] = template
                
                logger.info(f"✅ Loaded {len(self._memory_cache)} templates into memory")
                return self._memory_cache.copy()
                
        except Exception as e:
            logger.error(f"Error loading templates from database: {e}")
            return {}
    
    def _db_to_dict(self, db_template: APITemplate) -> Dict:
        """
        Convert database template to dictionary
        
        Args:
            db_template: SQLAlchemy model instance
            
        Returns:
            Template dictionary
        """
        metadata = db_template.metadata_ or {}

        return {
            "id": db_template.id,
            "intent": db_template.intent,
            "api_name": db_template.api_name,
            "description": db_template.description or "",
            "endpoint": db_template.endpoint,
            "method": db_template.method,
            "fields": db_template.fields or [],
            "intent_keywords": metadata.get("intent_keywords", []),
            "slots_config": metadata.get("slots_config", {}),
            "example_queries": db_template.example_queries or [],
            "version": metadata.get("version", 1),
            "is_system": db_template.is_system,
            "created_at": db_template.created_at.isoformat() if db_template.created_at else None,
            "updated_at": db_template.updated_at.isoformat() if db_template.updated_at else None,
            "metadata": metadata
        }
    
    def get_template(self, intent: str) -> Optional[Dict]:
        """
        Get template by intent from memory cache
        
        Args:
            intent: API intent
            
        Returns:
            Template dictionary or None
        """
        return self._memory_cache.get(intent)
    
    def get_all_templates(self) -> Dict[str, Dict]:
        """
        Get all templates from memory cache
        
        Returns:
            Dictionary of all templates
        """
        return self._memory_cache.copy()
    
    def get_all_intents(self) -> List[str]:
        """
        Get list of all available intents
        
        Returns:
            List of intent strings
        """
        return list(self._memory_cache.keys())
    
    def get_intent_patterns(self) -> Dict[str, List[str]]:
        """
        Get intent keywords for pattern matching
        
        Returns:
            Dictionary mapping intent to list of keywords
        """
        patterns = {}
        for intent, template in self._memory_cache.items():
            keywords = template.get("intent_keywords", [])
            if keywords:
                patterns[intent] = keywords
        return patterns
    
    async def create_template(self, template: Dict) -> Dict:
        """
        Create new template dynamically
        
        Args:
            template: Template dictionary
            
        Returns:
            Created template with ID
        """
        try:
            # Validate template
            is_valid, errors = self.loader.validate_template(template)
            if not is_valid:
                raise ValueError(f"Invalid template: {', '.join(errors)}")
            
            async with AsyncSessionLocal() as session:
                # Check if already exists
                result = await session.execute(
                    select(APITemplate).where(APITemplate.intent == template["intent"])
                )
                existing = result.scalar_one_or_none()
                
                if existing:
                    raise ValueError(f"Template with intent '{template['intent']}' already exists")
                
                # Create in database
                await self._create_template_db(session, template)
                await session.commit()
                
                # Add to cache
                self._memory_cache[template["intent"]] = template
                
                logger.info(f"✅ Created new template: {template['intent']}")
                return template
                
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    async def update_template(self, intent: str, updates: Dict) -> Dict:
        """
        Update existing template
        
        Args:
            intent: Template intent to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated template
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(APITemplate).where(APITemplate.intent == intent)
                )
                existing = result.scalar_one_or_none()
                
                if not existing:
                    raise ValueError(f"Template with intent '{intent}' not found")
                
                # Update fields
                for key, value in updates.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                
                await session.commit()
                
                # Update cache
                template = self._db_to_dict(existing)
                self._memory_cache[intent] = template
                
                logger.info(f"✅ Updated template: {intent}")
                return template
                
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            raise
    
    async def delete_template(self, intent: str) -> bool:
        """
        Delete template
        
        Args:
            intent: Template intent to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    delete(APITemplate).where(APITemplate.intent == intent)
                )
                await session.commit()
                
                # Remove from cache
                if intent in self._memory_cache:
                    del self._memory_cache[intent]
                
                logger.info(f"✅ Deleted template: {intent}")
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            raise
    
    def clear_cache(self):
        """Clear memory cache"""
        self._memory_cache.clear()
        logger.info("Template cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        return {
            "total_templates": len(self._memory_cache),
            "intents": list(self._memory_cache.keys()),
            "system_templates": sum(1 for t in self._memory_cache.values() if t.get("is_system")),
            "custom_templates": sum(1 for t in self._memory_cache.values() if not t.get("is_system"))
        }


# Global instance
_template_service = None


def get_template_service() -> TemplateService:
    """
    Get global template service instance (singleton)
    
    Returns:
        TemplateService instance
    """
    global _template_service
    if _template_service is None:
        _template_service = TemplateService()
    return _template_service
