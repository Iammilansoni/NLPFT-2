#!/usr/bin/env python3
"""
Migration script to populate MongoDB with function definitions from JSON dictionary.

This script imports the existing function_dictionary.json into MongoDB's 
dictionary_functions collection, converting the format to match the 
DictionaryFunction schema as specified in the PRD.

Usage:
    python migrate_dictionary_to_mongodb.py [--dry-run] [--force]
    
Options:
    --dry-run    Show what would be imported without making changes
    --force      Overwrite existing functions with same name
"""

import asyncio
import json
import sys
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.database import db_manager
from app.models.dictionary_models import DictionaryFunction, FunctionArgument
from app.core.logger import logger


class DictionaryMigration:
    """Handles migration of JSON dictionary to MongoDB."""
    
    def __init__(self, dry_run: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.stats = {
            "total_functions": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0
        }
    
    def load_json_dictionary(self, json_file: Path) -> List[Dict[str, Any]]:
        """Load function definitions from JSON file."""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                functions = json.load(f)
            
            logger.info(f"Loaded {len(functions)} functions from {json_file}")
            return functions
            
        except Exception as e:
            logger.error(f"Failed to load JSON dictionary: {e}")
            raise
    
    def convert_json_to_dictionary_function(self, json_func: Dict[str, Any]) -> DictionaryFunction:
        """
        Convert JSON function definition to DictionaryFunction model.
        
        Maps the JSON structure to the MongoDB schema:
        - id -> name
        - signature -> both signature dict and arguments list
        - Adds default values for missing fields
        """
        # Extract basic fields
        name = json_func.get("name") or json_func.get("id", "unknown")
        signature = json_func.get("signature", {})
        templates = json_func.get("templates", [])
        examples = json_func.get("examples", [])
        category = json_func.get("category", "general")
        
        # Convert signature to arguments list
        arguments = []
        for arg_name, arg_type in signature.items():
            arguments.append(FunctionArgument(
                name=arg_name,
                type=arg_type,
                required=True,  # Assume all args are required by default
                default=None,
                description=f"{arg_name.title()} parameter"
            ))
        
        # Determine category from function ID if not explicitly set
        if category == "general" and "id" in json_func:
            func_id = json_func["id"]
            if func_id.startswith("nav_"):
                category = "navigation"
            elif func_id.startswith("form_"):
                category = "forms"
            elif func_id.startswith("auth_"):
                category = "authentication"
            elif func_id.startswith("assert_"):
                category = "assertions"
            elif func_id.startswith("file_"):
                category = "files"
            elif func_id.startswith("table_"):
                category = "tables"
            elif func_id.startswith("modal_"):
                category = "modals"
            elif func_id.startswith("rbac_"):
                category = "permissions"
        
        # Assign priority based on category and function type
        # Note: Priority is not in the base model, so we'll skip it for now
        
        # Create DictionaryFunction
        return DictionaryFunction(
            name=name,
            display_name=name.replace("_", " ").title(),
            signature=signature,
            templates=templates,
            examples=examples,
            arguments=arguments,
            category=category,
            description=f"Function for {category} operations: {name}",
            is_active=True,
            tags=[category, name.split("_")[0]] if "_" in name else [category],
            created_by="migration_script",
            updated_by="migration_script"
        )
    
    def _calculate_priority(self, name: str, category: str) -> int:
        """Calculate priority based on function importance and usage patterns."""
        # High priority functions (commonly used)
        high_priority_functions = {
            "click", "open_url", "type", "fill", "login", "wait_for_visible"
        }
        
        # Medium priority functions  
        medium_priority_functions = {
            "wait_for_invisible", "select_dropdown", "check", "uncheck",
            "expect_text", "expect_visible", "upload_file"
        }
        
        if name in high_priority_functions:
            return 20
        elif name in medium_priority_functions:
            return 15
        elif category in ["authentication", "navigation"]:
            return 12
        elif category in ["forms", "assertions"]:
            return 10
        else:
            return 5
    
    async def migrate_function(self, json_func: Dict[str, Any]) -> bool:
        """
        Migrate a single function to MongoDB.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert to DictionaryFunction
            dict_func = self.convert_json_to_dictionary_function(json_func)
            
            if self.dry_run:
                logger.info(f"[DRY-RUN] Would create function: {dict_func.name}")
                self.stats["created"] += 1
                return True
            
            # Check if function already exists
            repository = db_manager.dictionary_repository
            if not repository:
                logger.error("Dictionary repository not available")
                return False
            
            existing = await repository.get_function_by_name(dict_func.name)
            
            if existing and not self.force:
                logger.info(f"Function {dict_func.name} already exists, skipping")
                self.stats["skipped"] += 1
                return True
            
            if existing and self.force:
                # Update existing function
                updates = {
                    "templates": dict_func.templates,
                    "signature": dict_func.signature,
                    "arguments": [arg.model_dump() for arg in dict_func.arguments],
                    "examples": dict_func.examples,
                    "category": dict_func.category,
                    "description": dict_func.description,
                    "tags": dict_func.tags,
                    "updated_by": "migration_script"
                }
                
                success = await repository.update_function(str(existing.id), updates)
                if success:
                    logger.info(f"✅ Updated function: {dict_func.name}")
                    self.stats["updated"] += 1
                else:
                    logger.error(f"❌ Failed to update function: {dict_func.name}")
                    self.stats["errors"] += 1
                    return False
            else:
                # Create new function
                created_func = await repository.create_function(dict_func)
                if created_func:
                    logger.info(f"✅ Created function: {dict_func.name}")
                    self.stats["created"] += 1
                else:
                    logger.error(f"❌ Failed to create function: {dict_func.name}")
                    self.stats["errors"] += 1
                    return False
            
            return True
            
        except Exception as e:
            logger.exception(f"❌ Error migrating function {json_func.get('name', 'unknown')}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def migrate_all(self, json_file: Path) -> Dict[str, int]:
        """
        Migrate all functions from JSON file to MongoDB.
        
        Returns:
            Statistics about the migration
        """
        logger.info(f"Starting dictionary migration from {json_file}")
        
        # Load JSON functions
        json_functions = self.load_json_dictionary(json_file)
        self.stats["total_functions"] = len(json_functions)
        
        if self.dry_run:
            logger.info("🔍 DRY-RUN MODE: No changes will be made")
        
        # Migrate each function
        for json_func in json_functions:
            await self.migrate_function(json_func)
        
        # Print summary
        logger.info("📊 Migration Summary:")
        logger.info(f"  Total functions: {self.stats['total_functions']}")
        logger.info(f"  Created: {self.stats['created']}")
        logger.info(f"  Updated: {self.stats['updated']}")
        logger.info(f"  Skipped: {self.stats['skipped']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        
        return self.stats


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate dictionary from JSON to MongoDB")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be imported without making changes")
    parser.add_argument("--force", action="store_true",
                       help="Overwrite existing functions with same name")
    parser.add_argument("--json-file", type=Path, 
                       default=project_root / "storage" / "function_dictionary.json",
                       help="Path to JSON dictionary file")
    
    args = parser.parse_args()
    
    # Check if JSON file exists
    if not args.json_file.exists():
        logger.error(f"JSON dictionary file not found: {args.json_file}")
        sys.exit(1)
    
    try:
        # Connect to database
        logger.info("🔌 Connecting to MongoDB...")
        await db_manager.connect()
        
        if not db_manager.dictionary_repository:
            logger.error("❌ Dictionary repository not available")
            sys.exit(1)
        
        logger.info("✅ Connected to MongoDB")
        
        # Run migration
        migration = DictionaryMigration(dry_run=args.dry_run, force=args.force)
        stats = await migration.migrate_all(args.json_file)
        
        # Check results
        if stats["errors"] > 0:
            logger.error(f"❌ Migration completed with {stats['errors']} errors")
            sys.exit(1)
        else:
            logger.info("✅ Migration completed successfully")
            
            # If not dry-run, trigger hot-reload
            if not args.dry_run and db_manager.dictionary_service:
                logger.info("🔄 Triggering hot-reload...")
                await db_manager.dictionary_service.hot_reload()
                logger.info("✅ Hot-reload completed")
        
    except KeyboardInterrupt:
        logger.info("❌ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())