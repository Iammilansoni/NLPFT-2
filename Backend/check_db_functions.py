"""
Quick script to check the number of functions in MongoDB database.
"""
import asyncio
from app.core.database import db_manager
from app.core.dictionary_repository import DictionaryRepository

async def count_functions():
    """Count and list all functions in the database."""
    try:
        # Connect to database
        await db_manager.connect()
        
        # Get repository
        repo = DictionaryRepository(db_manager.database)
        
        # Get all active functions
        functions = await repo.list_all_active_functions()
        
        print(f"📊 Total active functions in MongoDB: {len(functions)}")
        print("\n📋 Function List:")
        print("=" * 50)
        
        # Group by category
        by_category = {}
        for func in functions:
            category = func.category or "uncategorized"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(func)
        
        # Display by category
        for category, funcs in sorted(by_category.items()):
            print(f"\n📁 {category.upper()} ({len(funcs)} functions):")
            for func in sorted(funcs, key=lambda f: f.name):
                template_count = len(func.templates) if func.templates else 0
                print(f"  • {func.name} - {template_count} templates")
        
        print(f"\n🎯 Summary:")
        print(f"  • Total Functions: {len(functions)}")
        print(f"  • Categories: {len(by_category)}")
        
        # Count total templates
        total_templates = sum(len(f.templates) if f.templates else 0 for f in functions)
        print(f"  • Total Templates: {total_templates}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(count_functions())