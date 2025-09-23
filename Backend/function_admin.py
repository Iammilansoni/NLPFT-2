#!/usr/bin/env python3
"""
NLPForge Function Management Admin Tool.

This script provides a command-line interface for managing functions
with automatic synchronization between JSON file and MongoDB database.

Features:
- Create, read, update, delete functions
- List and search functions
- Sync operations between JSON and DB  
- Interactive and CLI modes
- Validation and error handling

Usage:
    python function_admin.py list
    python function_admin.py create --name "new_function" --templates "template1,template2"
    python function_admin.py update "function_name" --templates "new template"
    python function_admin.py delete "function_name"
    python function_admin.py sync --direction both
    python function_admin.py interactive
"""

import argparse
import asyncio
import json
import sys
from typing import Dict, Any, List, Optional

from app.services.function_crud_manager import FunctionCRUDManager
from app.core.logger import logger


class FunctionAdminCLI:
    """Command-line interface for function management."""
    
    def __init__(self):
        self.crud_manager = FunctionCRUDManager()
    
    async def __aenter__(self):
        await self.crud_manager.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.crud_manager.close()
    
    def print_function(self, func: Dict[str, Any], verbose: bool = False):
        """Print function details in a readable format."""
        print(f"\n📋 Function: {func['name']}")
        print(f"   Display Name: {func.get('display_name', func['name'])}")
        print(f"   Category: {func.get('category', 'general')}")
        print(f"   Active: {'✅' if func.get('is_active', True) else '❌'}")
        
        if verbose:
            print(f"   Description: {func.get('description', 'No description')}")
            print(f"   Signature: {json.dumps(func.get('signature', {}), indent=2)}")
            print(f"   Created by: {func.get('created_by', 'unknown')}")
            print(f"   Usage count: {func.get('usage_count', 0)}")
        
        templates = func.get('templates', [])
        print(f"   Templates ({len(templates)}):")
        for i, template in enumerate(templates[:5], 1):  # Show first 5
            print(f"     {i}. \"{template}\"")
        if len(templates) > 5:
            print(f"     ... and {len(templates) - 5} more")
    
    def print_result(self, result: Dict[str, Any]):
        """Print operation result with proper formatting."""
        if result.get("success"):
            print(f"✅ {result.get('message', 'Operation successful')}")
            if "function" in result:
                self.print_function(result["function"])
            elif "functions" in result:
                functions = result["functions"]
                print(f"\n📊 Found {len(functions)} functions:")
                for func in functions:
                    self.print_function(func)
            elif "stats" in result:
                print(f"📊 Stats: {json.dumps(result['stats'], indent=2)}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
            if "details" in result:
                print("   Details:")
                for key, value in result["details"].items():
                    print(f"     {key}: {value}")
    
    async def list_functions(self, category: Optional[str] = None, verbose: bool = False):
        """List all functions, optionally filtered by category."""
        print(f"📋 Listing functions{f' in category: {category}' if category else ''}...")
        
        result = await self.crud_manager.list_functions(category=category)
        
        if result["success"]:
            functions = result["functions"]
            print(f"\n📊 Found {len(functions)} functions")
            
            # Group by category for better display
            by_category = {}
            for func in functions:
                cat = func.get("category", "general")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(func)
            
            for cat, funcs in sorted(by_category.items()):
                total_templates = sum(len(f.get("templates", [])) for f in funcs)
                print(f"\n📁 {cat.upper()}: {len(funcs)} functions, {total_templates} templates")
                
                for func in sorted(funcs, key=lambda x: x["name"]):
                    if verbose:
                        self.print_function(func, verbose=True)
                    else:
                        templates = func.get("templates", [])
                        active = "✅" if func.get("is_active", True) else "❌"
                        print(f"   {active} {func['name']}: {len(templates)} templates")
        else:
            self.print_result(result)
    
    async def search_functions(self, query: str, search_in: List[str] = None):
        """Search functions by query string."""
        print(f"🔍 Searching for: '{query}'...")
        
        result = await self.crud_manager.search_functions(query, search_in)
        self.print_result(result)
    
    async def get_function(self, name: str):
        """Get and display a specific function."""
        print(f"📋 Getting function: {name}...")
        
        result = await self.crud_manager.get_function(name)
        if result["success"]:
            self.print_function(result["function"], verbose=True)
        else:
            self.print_result(result)
    
    async def create_function(self, name: str, templates: List[str], **kwargs):
        """Create a new function."""
        print(f"➕ Creating function: {name}...")
        
        function_data = {
            "name": name,
            "templates": templates,
            "display_name": kwargs.get("display_name", name),
            "description": kwargs.get("description", ""),
            "signature": kwargs.get("signature", {}),
            "category": kwargs.get("category", "general"),
            "is_active": kwargs.get("active", True)
        }
        
        result = await self.crud_manager.create_function(function_data)
        self.print_result(result)
    
    async def update_function(self, name: str, **kwargs):
        """Update an existing function."""
        print(f"🔄 Updating function: {name}...")
        
        # Get existing function first
        existing = await self.crud_manager.get_function(name)
        if not existing["success"]:
            self.print_result(existing)
            return
        
        # Merge with updates
        function_data = existing["function"].copy()
        
        if "templates" in kwargs and kwargs["templates"]:
            function_data["templates"] = kwargs["templates"]
        if "display_name" in kwargs:
            function_data["display_name"] = kwargs["display_name"]
        if "description" in kwargs:
            function_data["description"] = kwargs["description"]
        if "signature" in kwargs:
            function_data["signature"] = kwargs["signature"]
        if "category" in kwargs:
            function_data["category"] = kwargs["category"]
        if "active" in kwargs:
            function_data["is_active"] = kwargs["active"]
        
        result = await self.crud_manager.update_function(name, function_data)
        self.print_result(result)
    
    async def delete_function(self, name: str):
        """Delete a function."""
        print(f"🗑️ Deleting function: {name}...")
        
        # Confirm deletion
        confirmation = input(f"Are you sure you want to delete '{name}'? (y/N): ")
        if confirmation.lower() != 'y':
            print("❌ Deletion cancelled")
            return
        
        result = await self.crud_manager.delete_function(name)
        self.print_result(result)
    
    async def sync_functions(self, direction: str = "both"):
        """Synchronize functions between JSON and DB."""
        print(f"🔄 Syncing functions: {direction}...")
        
        result = await self.crud_manager.force_sync(direction)
        self.print_result(result)
    
    async def sync_status(self):
        """Check synchronization status."""
        print("🔍 Checking sync status...")
        
        result = await self.crud_manager.sync_status()
        
        if "error" not in result:
            print(f"📊 Sync Status:")
            print(f"   JSON functions: {result.get('json_count', 0)}")
            print(f"   DB functions: {result.get('db_count', 0)}")
            print(f"   In sync: {'✅' if result.get('in_sync', False) else '❌'}")
            print(f"   Common functions: {result.get('common_functions', 0)}")
            
            only_json = result.get('only_in_json', [])
            only_db = result.get('only_in_db', [])
            
            if only_json:
                print(f"   Only in JSON ({len(only_json)}): {', '.join(only_json[:5])}")
                if len(only_json) > 5:
                    print(f"      ... and {len(only_json) - 5} more")
            
            if only_db:
                print(f"   Only in DB ({len(only_db)}): {', '.join(only_db[:5])}")
                if len(only_db) > 5:
                    print(f"      ... and {len(only_db) - 5} more")
        else:
            print(f"❌ Error checking status: {result['error']}")
    
    async def categories(self):
        """List all function categories."""
        print("📁 Function categories:")
        
        result = await self.crud_manager.get_categories()
        
        if result["success"]:
            categories = result["categories"]
            total_functions = sum(cat["count"] for cat in categories)
            total_templates = sum(cat["template_count"] for cat in categories)
            
            print(f"📊 Total: {len(categories)} categories, {total_functions} functions, {total_templates} templates\n")
            
            for cat in sorted(categories, key=lambda x: x["count"], reverse=True):
                print(f"   📁 {cat['name'].upper()}: {cat['count']} functions, {cat['template_count']} templates")
        else:
            self.print_result(result)
    
    async def interactive_mode(self):
        """Start interactive mode for function management."""
        print("🎛️ Welcome to NLPForge Function Management Interactive Mode")
        print("Type 'help' for available commands or 'quit' to exit.\n")
        
        while True:
            try:
                command = input("nlpforge> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                
                if command.lower() == 'help':
                    print("""
Available commands:
  list [category]          - List all functions (optionally by category)
  search <query>           - Search functions by text
  get <name>               - Show details for a specific function
  create <name>            - Create a new function (interactive)
  update <name>            - Update a function (interactive)  
  delete <name>            - Delete a function
  sync [direction]         - Sync functions (json_to_db, db_to_json, both)
  status                   - Check sync status
  categories              - List all categories
  help                    - Show this help
  quit                    - Exit interactive mode
                    """)
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:]
                
                if cmd == 'list':
                    category = args[0] if args else None
                    await self.list_functions(category, verbose=False)
                
                elif cmd == 'search':
                    if not args:
                        print("❌ Please provide a search query")
                        continue
                    await self.search_functions(' '.join(args))
                
                elif cmd == 'get':
                    if not args:
                        print("❌ Please provide a function name")
                        continue
                    await self.get_function(args[0])
                
                elif cmd == 'delete':
                    if not args:
                        print("❌ Please provide a function name")
                        continue
                    await self.delete_function(args[0])
                
                elif cmd == 'sync':
                    direction = args[0] if args else "both"
                    if direction not in ["json_to_db", "db_to_json", "both"]:
                        print("❌ Invalid sync direction. Use: json_to_db, db_to_json, or both")
                        continue
                    await self.sync_functions(direction)
                
                elif cmd == 'status':
                    await self.sync_status()
                
                elif cmd == 'categories':
                    await self.categories()
                
                elif cmd in ['create', 'update']:
                    if not args:
                        print(f"❌ Please provide a function name for {cmd}")
                        continue
                    
                    name = args[0]
                    
                    if cmd == 'create':
                        print(f"Creating new function: {name}")
                        templates_input = input("Templates (comma-separated): ")
                        templates = [t.strip() for t in templates_input.split(',') if t.strip()]
                        
                        if not templates:
                            print("❌ At least one template is required")
                            continue
                        
                        display_name = input(f"Display name [{name}]: ") or name
                        description = input("Description: ")
                        category = input("Category [general]: ") or "general"
                        
                        await self.create_function(
                            name, templates,
                            display_name=display_name,
                            description=description,
                            category=category
                        )
                    
                    elif cmd == 'update':
                        print(f"Updating function: {name}")
                        print("Leave empty to keep current value")
                        
                        templates_input = input("Templates (comma-separated): ")
                        templates = [t.strip() for t in templates_input.split(',') if t.strip()] if templates_input else None
                        
                        display_name = input("Display name: ") or None
                        description = input("Description: ") or None
                        category = input("Category: ") or None
                        
                        update_args = {}
                        if templates:
                            update_args["templates"] = templates
                        if display_name:
                            update_args["display_name"] = display_name
                        if description:
                            update_args["description"] = description
                        if category:
                            update_args["category"] = category
                        
                        if not update_args:
                            print("❌ No updates provided")
                            continue
                        
                        await self.update_function(name, **update_args)
                
                else:
                    print(f"❌ Unknown command: {cmd}. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


async def main():
    """Main entry point for the admin CLI."""
    parser = argparse.ArgumentParser(description="NLPForge Function Management Admin Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List functions")
    list_parser.add_argument("--category", help="Filter by category")
    list_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed information")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search functions")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--in", dest="search_in", nargs="+", 
                              choices=["name", "templates", "description"],
                              default=["name", "templates", "description"],
                              help="Fields to search in")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get function details")
    get_parser.add_argument("name", help="Function name")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create function")
    create_parser.add_argument("--name", required=True, help="Function name")
    create_parser.add_argument("--templates", required=True, help="Comma-separated templates")
    create_parser.add_argument("--display-name", help="Display name")
    create_parser.add_argument("--description", help="Description")
    create_parser.add_argument("--category", default="general", help="Category")
    create_parser.add_argument("--signature", help="JSON signature")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update function")
    update_parser.add_argument("name", help="Function name")
    update_parser.add_argument("--templates", help="Comma-separated templates")
    update_parser.add_argument("--display-name", help="Display name")
    update_parser.add_argument("--description", help="Description")
    update_parser.add_argument("--category", help="Category")
    update_parser.add_argument("--signature", help="JSON signature")
    update_parser.add_argument("--active", type=bool, help="Active status")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete function")
    delete_parser.add_argument("name", help="Function name")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync functions")
    sync_parser.add_argument("--direction", choices=["json_to_db", "db_to_json", "both"],
                           default="both", help="Sync direction")
    
    # Status command
    subparsers.add_parser("status", help="Check sync status")
    
    # Categories command
    subparsers.add_parser("categories", help="List categories")
    
    # Interactive command
    subparsers.add_parser("interactive", help="Start interactive mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    async with FunctionAdminCLI() as admin:
        try:
            if args.command == "list":
                await admin.list_functions(category=args.category, verbose=args.verbose)
            
            elif args.command == "search":
                await admin.search_functions(args.query, args.search_in)
            
            elif args.command == "get":
                await admin.get_function(args.name)
            
            elif args.command == "create":
                templates = [t.strip() for t in args.templates.split(',')]
                signature = json.loads(args.signature) if args.signature else {}
                
                await admin.create_function(
                    args.name, templates,
                    display_name=args.display_name,
                    description=args.description,
                    category=args.category,
                    signature=signature
                )
            
            elif args.command == "update":
                update_args = {}
                if args.templates:
                    update_args["templates"] = [t.strip() for t in args.templates.split(',')]
                if args.display_name:
                    update_args["display_name"] = args.display_name
                if args.description:
                    update_args["description"] = args.description
                if args.category:
                    update_args["category"] = args.category
                if args.signature:
                    update_args["signature"] = json.loads(args.signature)
                if args.active is not None:
                    update_args["active"] = args.active
                
                await admin.update_function(args.name, **update_args)
            
            elif args.command == "delete":
                await admin.delete_function(args.name)
            
            elif args.command == "sync":
                await admin.sync_functions(args.direction)
            
            elif args.command == "status":
                await admin.sync_status()
            
            elif args.command == "categories":
                await admin.categories()
            
            elif args.command == "interactive":
                await admin.interactive_mode()
        
        except KeyboardInterrupt:
            print("\n👋 Operation cancelled")
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())