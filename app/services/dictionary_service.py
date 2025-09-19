"""Service layer for dictionary management with business logic."""

import re
import inspect
from typing import List, Optional, Dict, Any, Callable, Awaitable

from datetime import datetime, timezone

from app.core.dictionary_repository import DictionaryRepository
from app.models.dictionary_models import (
    DictionaryFunction,
    FunctionArgument,
    FunctionUsageLog,
    DictionaryStats,
)
from app.core.logger import logger


# Type alias for an async (or sync) hot-reload callback.
HotReloadCallback = Callable[[], Awaitable[None]]


class DictionaryService:
    """Service for dictionary management and template matching."""

    def __init__(self, repository: DictionaryRepository) -> None:
        self.repository = repository
        # callbacks should be async-callables returning Awaitable[None]
        self._hot_reload_callbacks: List[HotReloadCallback] = []

    async def create_function(
        self,
        name: str,
        templates: List[str],
        arguments: List[Dict[str, Any]],
        category: str = "general",
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None,
    ) -> DictionaryFunction:
        """Create and validate a new dictionary function."""
        try:
            # Validate function name
            if not self._validate_function_name(name):
                raise ValueError(f"Invalid function name: {name}")

            # Validate templates
            if not templates:
                raise ValueError("At least one template is required")

            for template in templates:
                if not self._validate_template(template):
                    raise ValueError(f"Invalid template: {template}")

            # Create signature from arguments
            signature: Dict[str, Any] = {}
            function_arguments: List[FunctionArgument] = []

            for arg_data in arguments:
                arg = FunctionArgument(**arg_data)
                function_arguments.append(arg)
                signature[arg.name] = arg.type

            # Create examples from templates (simple generation)
            examples = self._generate_examples_from_templates(templates[:3])  # Limit to 3 examples

            # Provide sensible defaults for constructor fields that may be required by the model
            now = datetime.now(timezone.utc)

            # Create function object. Add defaults for fields the model may require.
            function = DictionaryFunction(
                name=name,
                display_name=name.replace("_", " ").title(),
                signature=signature,
                templates=templates,
                examples=examples,
                arguments=function_arguments,  # Pass FunctionArgument objects directly
                category=category,
                description=description or f"Function: {name}",
                aliases=aliases or [],
                tags=tags or [],
                created_by=created_by,
                is_active=True,
                usage_count=0,
                created_at=now,
                updated_at=now,
                updated_by=None,
                last_used=None,
            )

            # Store in repository
            created_function = await self.repository.create_function(function)
            logger.info(f"✅ Dictionary function created: {name}")

            # Trigger hot reload
            await self._trigger_hot_reload()

            return created_function

        except Exception as e:
            logger.error(f"❌ Failed to create dictionary function {name}: {e}")
            raise

    async def get_function(self, identifier: str) -> Optional[DictionaryFunction]:
        """Get function by ID or name."""
        try:
            # Try by ObjectId first
            if len(identifier) == 24:  # ObjectId length
                function = await self.repository.get_function_by_id(identifier)
                if function:
                    return function

            # Try by name
            return await self.repository.get_function_by_name(identifier)

        except Exception as e:
            logger.error(f"❌ Failed to get function {identifier}: {e}")
            return None

    async def list_functions(
        self,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List functions with metadata."""
        functions = await self.repository.list_functions(
            category=category, is_active=is_active, search=search, skip=skip, limit=limit
        )
        return [
            {
                "id": str(func.id),
                "name": func.name,
                "display_name": func.display_name,
                "category": func.category,
                "description": func.description,
                "templates": func.templates,
                "examples": func.examples[:2],  # Limit examples in list view
                "arguments": [arg.model_dump() for arg in func.arguments],
                "is_active": func.is_active,
                "usage_count": func.usage_count,
                "created_at": func.created_at,
                "tags": func.tags,
            }
            for func in functions
        ]

    async def update_function(self, function_id: str, updates: Dict[str, Any]) -> bool:
        """Update function with validation."""
        try:
            # Get existing function
            existing = await self.repository.get_function_by_id(function_id)
            if not existing:
                raise ValueError(f"Function not found: {function_id}")

            # Validate updates
            validated_updates: Dict[str, Any] = {}

            if "name" in updates:
                if not self._validate_function_name(updates["name"]):
                    raise ValueError(f"Invalid function name: {updates['name']}")
                # Check for name conflicts
                if updates["name"] != existing.name:
                    existing_with_name = await self.repository.get_function_by_name(updates["name"])
                    if existing_with_name:
                        raise ValueError(f"Function name already exists: {updates['name']}")
                validated_updates["name"] = updates["name"]

            if "templates" in updates:
                templates = updates["templates"]
                if not templates:
                    raise ValueError("At least one template is required")
                for template in templates:
                    if not self._validate_template(template):
                        raise ValueError(f"Invalid template: {template}")
                validated_updates["templates"] = templates
                # Regenerate examples
                validated_updates["examples"] = self._generate_examples_from_templates(templates[:3])

            if "arguments" in updates:
                arguments_list: List[FunctionArgument] = []
                signature: Dict[str, Any] = {}
                for arg_data in updates["arguments"]:
                    arg = FunctionArgument(**arg_data)
                    arguments_list.append(arg)  # Store FunctionArgument objects directly
                    signature[arg.name] = arg.type
                validated_updates["arguments"] = arguments_list
                validated_updates["signature"] = signature

            # Copy other simple fields
            simple_fields = ["category", "description", "aliases", "tags", "is_active", "display_name"]
            for field in simple_fields:
                if field in updates:
                    validated_updates[field] = updates[field]

            # Add updated_by if provided
            if "updated_by" in updates:
                validated_updates["updated_by"] = updates["updated_by"]

            # Update in repository
            success = await self.repository.update_function(function_id, validated_updates)

            if success:
                logger.info(f"✅ Dictionary function updated: {function_id}")
                # Trigger hot reload
                await self._trigger_hot_reload()

            return success

        except Exception as e:
            logger.error(f"❌ Failed to update dictionary function {function_id}: {e}")
            raise

    async def delete_function(self, function_id: str) -> bool:
        """Delete function."""
        try:
            success = await self.repository.delete_function(function_id)

            if success:
                logger.info(f"✅ Dictionary function deleted: {function_id}")
                # Trigger hot reload
                await self._trigger_hot_reload()

            return success

        except Exception as e:
            logger.error(f"❌ Failed to delete dictionary function {function_id}: {e}")
            return False

    async def match_user_input(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Match user input against function templates."""
        try:
            matches = await self.repository.search_functions_by_template(user_input)

            if not matches:
                return None

            best_match = matches[0]
            function = best_match["function"]
            template = best_match["template"]
            extracted_args = best_match["matched_groups"]
            confidence = best_match["confidence"]

            # Log the usage
            usage_log = FunctionUsageLog(
                function_id=function.id,
                function_name=function.name,
                user_input=user_input,
                matched_template=template,
                extracted_args=extracted_args,
                success=True,
                confidence_score=confidence,
                timestamp=datetime.now(timezone.utc),
            )
            await self.repository.log_function_usage(usage_log)

            return {
                "function_name": function.name,
                "function_id": str(function.id),
                "matched_template": template,
                "extracted_arguments": extracted_args,
                "confidence_score": confidence,
                "function_signature": function.signature,
                "category": function.category,
            }

        except Exception as e:
            logger.error(f"❌ Failed to match user input: {e}")
            return None

    async def get_function_details(self, function_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed function information including stats."""
        try:
            function = await self.repository.get_function_by_id(function_id)
            if not function:
                return None

            # Get usage stats
            stats = await self.repository.get_function_stats(function_id)

            return {
                "id": str(function.id),
                "name": function.name,
                "display_name": function.display_name,
                "signature": function.signature,
                "templates": function.templates,
                "examples": function.examples,
                "arguments": [arg.model_dump() for arg in function.arguments],
                "category": function.category,
                "description": function.description,
                "aliases": function.aliases,
                "tags": function.tags,
                "is_active": function.is_active,
                "created_at": function.created_at,
                "updated_at": function.updated_at,
                "created_by": function.created_by,
                "updated_by": function.updated_by,
                "usage_count": function.usage_count,
                "last_used": function.last_used,
                "stats": stats,
            }

        except Exception as e:
            logger.error(f"❌ Failed to get function details: {e}")
            return None

    async def get_dictionary_stats(self) -> DictionaryStats:
        """Get dictionary statistics."""
        return await self.repository.get_dictionary_stats()

    async def hot_reload(self) -> bool:
        """Force reload dictionary cache and notify subscribers."""
        try:
            success = await self.repository.reload_cache()
            if success:
                await self._trigger_hot_reload()
                logger.info("✅ Dictionary hot reload completed")
            return success
        except Exception as e:
            logger.error(f"❌ Hot reload failed: {e}")
            return False

    def register_hot_reload_callback(self, callback: HotReloadCallback) -> None:
        """Register callback for hot reload events."""
        # store as-is; _trigger_hot_reload will handle sync vs async
        self._hot_reload_callbacks.append(callback)

    async def _trigger_hot_reload(self) -> None:
        """Trigger all registered hot reload callbacks (handles sync & async callbacks)."""
        for callback in list(self._hot_reload_callbacks):
            try:
                if not callable(callback):
                    continue
                result = callback()
                # result may be an awaitable
                if inspect.isawaitable(result):
                    await result  # type: ignore[arg-type]
                else:
                    # callback was sync — nothing to await
                    continue
            except Exception as e:
                logger.error(f"❌ Hot reload callback failed: {e}")

    def _validate_function_name(self, name: str) -> bool:
        """Validate function name format."""
        # Must be alphanumeric with underscores, no spaces
        if not name:
            return False
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))

    def _validate_template(self, template: str) -> bool:
        """Validate template format."""
        if not template:
            return False

        # Check for balanced curly braces
        open_count = template.count("{")
        close_count = template.count("}")

        if open_count != close_count:
            return False

        # Check for valid placeholder format
        placeholders = re.findall(r"{(\w+)}", template)
        invalid_placeholders = re.findall(r"{([^}]*)}", template)

        # All placeholders should be valid identifiers
        return len(placeholders) == len(invalid_placeholders)

    def _generate_examples_from_templates(self, templates: List[str]) -> List[str]:
        """Generate example usage from templates."""
        examples: List[str] = []

        for template in templates:
            # Simple example generation - replace placeholders with sample values
            example = template

            # Common placeholder replacements
            replacements: Dict[str, str] = {
                "username": "admin",
                "password": "secret123",
                "url": "https://example.com",
                "selector": "#submit-btn",
                "value": "sample_value",
                "text": "Hello World",
                "email": "user@example.com",
                "name": "John Doe",
                "file": "document.pdf",
                "timeout": "30",
                "count": "5",
            }

            for placeholder, sample_value in replacements.items():
                example = example.replace(f"{{{placeholder}}}", sample_value)

            # Replace any remaining placeholders with generic values
            remaining_placeholders = re.findall(r"{(\w+)}", example)
            for placeholder in remaining_placeholders:
                example = example.replace(f"{{{placeholder}}}", f"sample_{placeholder}")

            examples.append(example)

        return examples
