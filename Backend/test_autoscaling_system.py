"""
Phase 4: Comprehensive Testing & Validation
Tests the auto-scaling template system end-to-end
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.logger import logger
from app.services.template_service import get_template_service
from app.nlp.query_parser import get_query_parser
from app.nlp.smart_dataset_generator import SmartDatasetGenerator


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_success(message: str):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"ℹ️  {message}")


async def test_template_service():
    """Test 1: Template Service"""
    print_section("TEST 1: Template Service")
    
    try:
        template_service = get_template_service()
        
        # Load templates
        templates = await template_service.load_all_templates()
        print_info(f"Loaded {len(templates)} templates from database")
        
        if len(templates) == 0:
            print_error("No templates loaded!")
            return False
        
        print_success(f"Template service loaded {len(templates)} templates")
        
        # List all templates
        print_info("Available templates:")
        for i, name in enumerate(templates.keys(), 1):
            template = templates[name]
            print(f"   {i}. {name}: {template.get('description', 'No description')}")
        
        return True
        
    except Exception as e:
        print_error(f"Template service test failed: {e}")
        return False


def test_query_parser():
    """Test 2: Query Parser with Dynamic Templates"""
    print_section("TEST 2: Query Parser (Dynamic Pattern Loading)")
    
    try:
        parser = get_query_parser()
        
        # Check if patterns loaded
        if not parser.intent_patterns:
            print_error("No intent patterns loaded!")
            return False
        
        print_success(f"Query parser loaded {len(parser.intent_patterns)} intent patterns")
        
        # Test queries for all 10 APIs
        test_queries = {
            "login": "Login with john and pass123",
            "logout": "Logout from my account",
            "register": "Register with email john@example.com and username john_doe",
            "reset_password": "Reset password for john@example.com",
            "update_profile": "Update profile with new name and phone number",
            "upload_file": "Upload file report.pdf",
            "download_file": "Download file report.pdf",
            "search": "Search for documents about artificial intelligence",
            "get_user": "Get user information for john_doe",
            "delete_account": "Delete account for user U12345"
        }
        
        print_info("Testing query parsing for all APIs:")
        passed = 0
        failed = 0
        
        for expected_intent, query in test_queries.items():
            try:
                result = parser.parse(query)
                detected_intent = result["intent"]
                confidence = result["confidence"]
                
                if detected_intent == expected_intent:
                    print(f"   ✅ {expected_intent}: '{query}' → {detected_intent} ({confidence:.2f})")
                    passed += 1
                else:
                    print(f"   ❌ {expected_intent}: Expected '{expected_intent}', got '{detected_intent}' ({confidence:.2f})")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ {expected_intent}: Error - {e}")
                failed += 1
        
        print(f"\n   Results: {passed} passed, {failed} failed out of {len(test_queries)} tests")
        
        return failed == 0
        
    except Exception as e:
        print_error(f"Query parser test failed: {e}")
        return False


def test_dataset_generator():
    """Test 3: Dataset Generator with Dynamic Templates"""
    print_section("TEST 3: Dataset Generator (Dynamic Template Loading)")
    
    try:
        generator = SmartDatasetGenerator()
        
        # Check if templates loaded
        if not generator.templates:
            print_error("No templates loaded in dataset generator!")
            return False
        
        print_success(f"Dataset generator loaded {len(generator.templates)} templates")
        
        # Test dataset generation for a few APIs
        test_intents = ["login", "register", "search"]
        
        print_info("Testing dataset generation:")
        passed = 0
        failed = 0
        
        for intent in test_intents:
            try:
                # Generate small dataset
                examples = generator.generate_base_examples(intent, num_examples=5)
                
                if examples and len(examples) > 0:
                    print(f"   ✅ {intent}: Generated {len(examples)} examples")
                    # Show first example
                    if examples:
                        print(f"      Sample: {examples[0]['query']}")
                    passed += 1
                else:
                    print(f"   ❌ {intent}: No examples generated")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ {intent}: Error - {e}")
                failed += 1
        
        print(f"\n   Results: {passed} passed, {failed} failed out of {len(test_intents)} tests")
        
        return failed == 0
        
    except Exception as e:
        print_error(f"Dataset generator test failed: {e}")
        return False


async def test_template_sync():
    """Test 4: Template Sync from JSON"""
    print_section("TEST 4: Template Sync from JSON")
    
    try:
        template_service = get_template_service()
        
        # Check if api_template.json exists
        json_path = Path(__file__).parent / "api_template.json"
        
        if not json_path.exists():
            print_error(f"api_template.json not found at {json_path}")
            return False
        
        print_info(f"Found api_template.json at {json_path}")
        
        # Sync from JSON
        stats = await template_service.sync_from_json(str(json_path))
        
        print_success(f"Synced templates from JSON:")
        print(f"   - Loaded: {stats.get('loaded', 0)} templates")
        print(f"   - Added: {stats.get('added', 0)} new templates")
        print(f"   - Updated: {stats.get('updated', 0)} existing templates")
        print(f"   - Total: {stats.get('total', 0)} templates in database")
        
        return True
        
    except Exception as e:
        print_error(f"Template sync test failed: {e}")
        return False


def test_hot_reload():
    """Test 5: Hot Reload"""
    print_section("TEST 5: Hot Reload (Without Restart)")
    
    try:
        # Reload query parser
        parser = get_query_parser()
        old_count = len(parser.intent_patterns)
        parser.reload_patterns()
        new_count = len(parser.intent_patterns)
        print_success(f"Query parser reloaded: {old_count} → {new_count} patterns")
        
        # Reload dataset generator
        generator = SmartDatasetGenerator()
        old_count = len(generator.templates)
        generator.reload_templates()
        new_count = len(generator.templates)
        print_success(f"Dataset generator reloaded: {old_count} → {new_count} templates")
        
        return True
        
    except Exception as e:
        print_error(f"Hot reload test failed: {e}")
        return False


async def test_add_new_api():
    """Test 6: Add New API (11th API)"""
    print_section("TEST 6: Add New API (Scalability Test)")
    
    try:
        template_service = get_template_service()
        
        # Create a test API template
        new_template = {
            "intent": "send_message",
            "api_name": "send_message",
            "description": "Send a message to another user",
            "endpoint": "/api/messages/send",
            "method": "POST",
            "intent_keywords": ["send message", "message", "send", "dm"],
            "fields": ["recipient", "message"],
            "parameters": [
                {
                    "name": "recipient",
                    "type": "string",
                    "required": True,
                    "description": "Recipient username"
                },
                {
                    "name": "message",
                    "type": "string",
                    "required": True,
                    "description": "Message content"
                }
            ]
        }
        
        print_info("Creating new API template: send_message")
        
        # Check if already exists and delete first
        existing = template_service.get_template("send_message")
        if existing:
            print_info("Template already exists, deleting first...")
            await template_service.delete_template("send_message")
        
        # Create new template
        created = await template_service.create_template(new_template)
        
        if not created:
            print_error("Failed to create new template")
            return False
        
        print_success("Created new API template: send_message")
        
        # Hot reload services
        parser = get_query_parser()
        parser.reload_patterns()
        
        generator = SmartDatasetGenerator()
        generator.reload_templates()
        
        print_success("Reloaded all services with new template")
        
        # Test if new API works
        test_query = "Send message to john: Hello there!"
        result = parser.parse(test_query)
        
        if result["intent"] == "send_message":
            print_success(f"New API works! Query '{test_query}' → {result['intent']}")
        else:
            print_error(f"New API failed. Expected 'send_message', got '{result['intent']}'")
            return False
        
        # Test dataset generation
        examples = generator.generate_base_examples("send_message", num_examples=3)
        if examples:
            print_success(f"Dataset generation works! Generated {len(examples)} examples")
        else:
            print_error("Dataset generation failed for new API")
            return False
        
        # Clean up
        print_info("Cleaning up test template...")
        await template_service.delete_template("send_message")
        
        return True
        
    except Exception as e:
        print_error(f"Add new API test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("  🚀 AUTO-SCALING TEMPLATE SYSTEM - COMPREHENSIVE TESTING")
    print("="*80)
    
    results = []
    
    # Test 1: Template Service
    results.append(("Template Service", await test_template_service()))
    
    # Test 2: Query Parser
    results.append(("Query Parser", test_query_parser()))
    
    # Test 3: Dataset Generator
    results.append(("Dataset Generator", test_dataset_generator()))
    
    # Test 4: Template Sync
    results.append(("Template Sync", await test_template_sync()))
    
    # Test 5: Hot Reload
    results.append(("Hot Reload", test_hot_reload()))
    
    # Test 6: Add New API
    results.append(("Add New API (Scalability)", await test_add_new_api()))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*80}")
    print(f"  TOTAL: {passed}/{total} tests passed")
    print(f"{'='*80}\n")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Auto-scaling system is working perfectly!")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    try:
        # Run tests
        success = asyncio.run(run_all_tests())
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
