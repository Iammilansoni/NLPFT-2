"""Repository layer for dictionary management in MongoDB."""

from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime, timezone
import re
from collections import Counter
from rapidfuzz import fuzz

from app.models.dictionary_models import DictionaryFunction, FunctionUsageLog, DictionaryStats
from app.core.logger import logger


class DictionaryRepository:
    """Repository for dictionary CRUD operations."""

    def __init__(self, db: Any):
        self.db = db
        self.functions_collection: Any = db.dictionary_functions
        self.usage_logs_collection: Any = db.function_usage_logs
        self._cache: Dict[str, DictionaryFunction] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes cache

    async def create_indexes(self) -> None:
        """Create necessary indexes for optimal performance."""
        try:
            # Function indexes
            await self.functions_collection.create_index("name", unique=True)
            await self.functions_collection.create_index("category")
            await self.functions_collection.create_index("is_active")
            await self.functions_collection.create_index("tags")
            await self.functions_collection.create_index("created_at")
            await self.functions_collection.create_index("usage_count")

            # Compound indexes for common queries
            await self.functions_collection.create_index([("category", 1), ("is_active", 1)])
            await self.functions_collection.create_index([("is_active", 1), ("usage_count", -1)])

            # Text index for search
            await self.functions_collection.create_index([
                ("name", "text"),
                ("description", "text"),
                ("templates", "text"),
                ("examples", "text")
            ])

            # Usage log indexes
            await self.usage_logs_collection.create_index("function_id")
            await self.usage_logs_collection.create_index("function_name")
            await self.usage_logs_collection.create_index("timestamp")
            await self.usage_logs_collection.create_index([("timestamp", -1)])

            logger.info("✅ Dictionary repository indexes created")
        except Exception as e:
            logger.error(f"❌ Failed to create dictionary indexes: {e}")
            raise

    async def create_function(self, function: DictionaryFunction) -> DictionaryFunction:
        """Create a new function in the dictionary."""
        try:
            # Check if function name already exists
            existing = await self.get_function_by_name(function.name)
            if existing:
                raise ValueError(f"Function '{function.name}' already exists")

            function_dict = function.model_dump(by_alias=True)
            result = await self.functions_collection.insert_one(function_dict)
            function.id = result.inserted_id

            # Clear cache
            self._clear_cache()

            logger.info(f"✅ Dictionary function created: {function.name}")
            return function

        except Exception as e:
            logger.error(f"❌ Failed to create dictionary function: {e}")
            raise

    async def get_function_by_id(self, function_id: str) -> Optional[DictionaryFunction]:
        """Get function by ID."""
        try:
            doc = await self.functions_collection.find_one({"_id": ObjectId(function_id)})
            if doc:
                return DictionaryFunction(**doc)  # doc is already a mapping
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get function by ID: {e}")
            return None

    async def get_function_by_name(self, name: str) -> Optional[DictionaryFunction]:
        """Get function by name."""
        try:
            # Check cache first
            if self._is_cache_valid() and name in self._cache:
                return self._cache[name]

            doc = await self.functions_collection.find_one({"name": name})
            if doc:
                function = DictionaryFunction(**doc)
                self._cache[name] = function
                return function
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get function by name: {e}")
            return None

    async def list_functions(self,
                             category: Optional[str] = None,
                             is_active: Optional[bool] = None,
                             search: Optional[str] = None,
                             skip: int = 0,
                             limit: int = 100) -> List[DictionaryFunction]:
        """List functions with optional filters."""
        try:
            query: Dict[str, Any] = {}

            if category:
                query["category"] = category
            if is_active is not None:
                query["is_active"] = is_active

            # Text search
            if search:
                query["$text"] = {"$search": search}

            cursor = self.functions_collection.find(query)

            # Sort by usage count (most used first) if no search, otherwise by text score
            if search:
                cursor = cursor.sort([("score", {"$meta": "textScore"})])
            else:
                cursor = cursor.sort([("usage_count", -1), ("name", 1)])

            cursor = cursor.skip(skip).limit(limit)

            functions: List[DictionaryFunction] = []
            async for doc in cursor:
                functions.append(DictionaryFunction(**doc))

            return functions

        except Exception as e:
            logger.error(f"❌ Failed to list functions: {e}")
            return []

    async def count_functions(self,
                             category: Optional[str] = None,
                             is_active: Optional[bool] = None,
                             search: Optional[str] = None) -> int:
        """Count functions with optional filters."""
        try:
            query: Dict[str, Any] = {}

            if category:
                query["category"] = category
            if is_active is not None:
                query["is_active"] = is_active

            # Text search
            if search:
                query["$text"] = {"$search": search}

            count = await self.functions_collection.count_documents(query)
            return count

        except Exception as e:
            logger.error(f"❌ Failed to count functions: {e}")
            return 0

    async def list_all_active_functions(self) -> List[DictionaryFunction]:
        """Get all active functions for rule engine. Uses caching."""
        try:
            if self._is_cache_valid():
                return list(self._cache.values())

            # Refresh cache
            cursor = self.functions_collection.find({"is_active": True})
            functions: List[DictionaryFunction] = []
            self._cache = {}

            async for doc in cursor:
                function = DictionaryFunction(**doc)
                functions.append(function)
                self._cache[function.name] = function

            self._cache_timestamp = datetime.now(timezone.utc)
            logger.info(f"✅ Loaded {len(functions)} active functions from MongoDB")
            return functions

        except Exception as e:
            logger.error(f"❌ Failed to load active functions: {e}")
            return []

    async def update_function(self, function_id: str, updates: Dict[str, Any]) -> bool:
        """Update a function."""
        try:
            updates["updated_at"] = datetime.now(timezone.utc)
            result = await self.functions_collection.update_one(
                {"_id": ObjectId(function_id)},
                {"$set": updates}
            )

            success = result.modified_count > 0
            if success:
                self._clear_cache()
                logger.info(f"✅ Dictionary function updated: {function_id}")

            return success

        except Exception as e:
            logger.error(f"❌ Failed to update function: {e}")
            return False

    async def delete_function(self, function_id: str) -> bool:
        """Delete a function."""
        try:
            # Get function name for logging
            function = await self.get_function_by_id(function_id)
            if not function:
                return False

            result = await self.functions_collection.delete_one({"_id": ObjectId(function_id)})
            success = result.deleted_count > 0

            if success:
                # Clear cache
                self._clear_cache()

                # Delete usage logs for this function
                await self.usage_logs_collection.delete_many({"function_id": ObjectId(function_id)})

                logger.info(f"✅ Dictionary function deleted: {function.name}")

            return success

        except Exception as e:
            logger.error(f"❌ Failed to delete function: {e}")
            return False

    async def log_function_usage(self, usage_log: FunctionUsageLog) -> bool:
        """Log function usage and update stats."""
        try:
            # Insert usage log
            log_dict = usage_log.model_dump(by_alias=True)
            await self.usage_logs_collection.insert_one(log_dict)

            # Update function usage stats
            await self.functions_collection.update_one(
                {"_id": usage_log.function_id},
                {
                    "$inc": {"usage_count": 1},
                    "$set": {"last_used": usage_log.timestamp}
                }
            )

            return True

        except Exception as e:
            logger.error(f"❌ Failed to log function usage: {e}")
            return False

    async def get_function_stats(self, function_id: str) -> Dict[str, Any]:
        """Get detailed stats for a specific function."""
        try:
            pipeline: List[Dict[str, Any]] = [
                {"$match": {"function_id": ObjectId(function_id)}},
                {"$group": {
                    "_id": None,
                    "total_uses": {"$sum": 1},
                    "successful_uses": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "avg_confidence": {"$avg": "$confidence_score"},
                    "first_used": {"$min": "$timestamp"},
                    "last_used": {"$max": "$timestamp"},
                    "most_common_template": {
                        "$push": "$matched_template"
                    }
                }}
            ]

            result = await self.usage_logs_collection.aggregate(pipeline).to_list(1)
            if result:
                stats: Dict[str, Any] = result[0]
                stats.pop("_id", None)

                # Get most common template
                if stats.get("most_common_template"):
                    template_counts: Counter[str] = Counter(stats["most_common_template"])
                    most_common = template_counts.most_common(1)
                    stats["most_common_template"] = most_common[0][0] if most_common else None

                return stats

            return {}

        except Exception as e:
            logger.error(f"❌ Failed to get function stats: {e}")
            return {}

    async def get_dictionary_stats(self) -> DictionaryStats:
        """Get overall dictionary statistics."""
        try:
            # Get basic counts
            total_functions = await self.functions_collection.count_documents({})
            active_functions = await self.functions_collection.count_documents({"is_active": True})

            # Get category breakdown
            category_pipeline: List[Dict[str, Any]] = [
                {"$match": {"is_active": True}},
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            category_results = await self.functions_collection.aggregate(category_pipeline).to_list(None)
            categories = {item["_id"]: item["count"] for item in category_results}

            # Get most used functions
            most_used: List[Dict[str, Any]] = await self.functions_collection.find(
                {"is_active": True},
                {"name": 1, "usage_count": 1}
            ).sort("usage_count", -1).limit(5).to_list(None)

            most_used_functions = [
                {"name": func["name"], "usage_count": func["usage_count"]}
                for func in most_used
            ]

            # Get recent additions
            recent: List[Dict[str, Any]] = await self.functions_collection.find(
                {"is_active": True},
                {"name": 1, "created_at": 1}
            ).sort("created_at", -1).limit(5).to_list(None)

            recent_additions = [
                {"name": func["name"], "created_at": func["created_at"]}
                for func in recent
            ]

            return DictionaryStats(
                total_functions=total_functions,
                active_functions=active_functions,
                categories=categories,
                most_used_functions=most_used_functions,
                recent_additions=recent_additions,
                last_updated=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"❌ Failed to get dictionary stats: {e}")
            return DictionaryStats()

    async def search_functions_by_template(self, user_input: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search functions by matching templates against user input."""
        try:
            functions = await self.list_all_active_functions()
            matches: List[Dict[str, Any]] = []

            for function in functions:
                # ensure templates is iterable
                templates = getattr(function, "templates", []) or []
                for template in templates:
                    # Simple regex matching - can be enhanced with fuzzy matching
                    template_pattern = self._template_to_regex(template)
                    match = re.search(template_pattern, user_input, re.IGNORECASE)

                    if match:
                        confidence = self._calculate_confidence(user_input, template)
                        matches.append({
                            "function": function,
                            "template": template,
                            "confidence": confidence,
                            "matched_groups": match.groupdict()
                        })

            # Sort by confidence and return top matches
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            return matches[:limit]

        except Exception as e:
            logger.error(f"❌ Failed to search functions by template: {e}")
            return []

    def _template_to_regex(self, template: str) -> str:
        """Convert template with {arg} placeholders to regex pattern."""
        # Escape special regex characters
        pattern = re.escape(template)
        # Replace escaped placeholders with named groups
        pattern = re.sub(r'\\{(\w+)\\}', r'(?P<\\1>[^\\s]+)', pattern)
        return pattern

    def _calculate_confidence(self, user_input: str, template: str) -> float:
        """Calculate confidence score for template match."""
        # Combine fuzzy similarity and simple word overlap
        template_words = set(template.lower().split())
        input_words = set(user_input.lower().split())

        overlap = len(template_words.intersection(input_words))
        total_words = len(template_words.union(input_words))

        overlap_score = (overlap / total_words) if total_words > 0 else 0.0

        # rapidfuzz returns 0..100; convert to 0..1
        fuzzy_score = fuzz.token_set_ratio(user_input, template) / 100.0

        # Weighted combination: fuzzy is stronger
        return (0.6 * fuzzy_score) + (0.4 * overlap_score)

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache_timestamp:
            return False

        age = (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl_seconds

    def _clear_cache(self) -> None:
        """Clear the cache."""
        self._cache = {}
        self._cache_timestamp = None

    async def reload_cache(self) -> bool:
        """Force reload cache (for hot-reload functionality)."""
        try:
            self._clear_cache()
            await self.list_all_active_functions()  # This will repopulate cache
            logger.info("✅ Dictionary cache reloaded")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to reload cache: {e}")
            return False
