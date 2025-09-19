"""
Export all functions from MongoDB to function_dictionary.json.
This script will sync the database with the JSON file.
"""
import asyncio
import json
from datetime import datetime
from app.core.database import db_manager
from app.core.dictionary_repository import DictionaryRepository

async def export_db_to_json():
    """Export all functions from MongoDB to function_dictionary.json."""
    try:
        await db_manager.connect()
        repo = DictionaryRepository(db_manager.database)
        
        print("📥 Fetching all functions from MongoDB...")
        all_functions = await repo.list_all_active_functions()
        
        print(f"📊 Found {len(all_functions)} functions in database")
        
        # Convert to JSON format matching the existing structure
        json_functions = []
        
        for func in all_functions:
            # Create JSON function entry
            json_func = {
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
            
            json_functions.append(json_func)
        
        # Sort by category then by name for better organization
        json_functions.sort(key=lambda x: (x.get("category", ""), x["name"]))
        
        # Write to JSON file
        json_path = "storage/function_dictionary.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_functions, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(json_functions)} functions to {json_path}")
        
        # Show summary by category
        by_category = {}
        for func in json_functions:
            category = func.get("category", "general")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(func)
        
        print("\n📊 Functions by category:")
        for category, funcs in sorted(by_category.items()):
            total_templates = sum(len(f["templates"]) for f in funcs)
            print(f"  📁 {category.upper()}: {len(funcs)} functions, {total_templates} templates")
        
        print(f"\n✨ Successfully synchronized {len(all_functions)} functions to JSON!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(export_db_to_json())