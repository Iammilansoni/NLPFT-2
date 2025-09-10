#!/usr/bin/env python3
"""
Function Dictionary Statistics Script

This script analyzes the function_dictionary.json file and provides
detailed statistics about the available functions.
"""

import json
from pathlib import Path
from collections import Counter


def analyze_function_dictionary():
    """Analyze the function dictionary and provide statistics."""
    
    # Load the function dictionary
    dict_path = Path(__file__).parent / "storage" / "function_dictionary.json"
    
    try:
        with open(dict_path, 'r', encoding='utf-8') as file:
            functions = json.load(file)
    except FileNotFoundError:
        print(f"❌ Function dictionary not found at {dict_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in function dictionary: {e}")
        return
    
    print("📊 Function Dictionary Statistics")
    print("=" * 50)
    
    # Basic count
    total_functions = len(functions)
    print(f"📝 Total Functions: {total_functions}")
    
    # Count templates
    total_templates = sum(len(func.get("templates", [])) for func in functions)
    print(f"🔤 Total Templates: {total_templates}")
    
    # Count examples
    total_examples = sum(len(func.get("examples", [])) for func in functions)
    print(f"💡 Total Examples: {total_examples}")
    
    # Categorize by ID prefix
    categories = Counter()  # type: ignore
    for func in functions:
        func_id = func.get("id", "")
        if "_" in func_id:
            category = func_id.split("_")[0]
            categories[category] += 1
        else:
            categories["other"] += 1
    
    print(f"\n📂 Functions by Category:")
    print("-" * 30)
    for category, count in categories.most_common():  # type: ignore
        print(f"  {str(category).upper()}: {count} functions")  # type: ignore
    
    # Analyze signatures
    signature_stats = Counter()  # type: ignore
    for func in functions:
        signature = func.get("signature", {})
        param_count = len(signature)
        signature_stats[param_count] += 1
    
    print(f"\n🔧 Functions by Parameter Count:")
    print("-" * 35)
    for param_count, func_count in sorted(signature_stats.items()):  # type: ignore
        print(f"  {param_count} parameters: {func_count} functions")
    
    # Show template distribution
    template_counts = [len(func.get("templates", [])) for func in functions]
    avg_templates = sum(template_counts) / len(template_counts) if template_counts else 0
    
    print(f"\n📋 Template Statistics:")
    print("-" * 25)
    print(f"  Average templates per function: {avg_templates:.1f}")
    print(f"  Min templates: {min(template_counts) if template_counts else 0}")
    print(f"  Max templates: {max(template_counts) if template_counts else 0}")
    
    # List all function names
    print(f"\n📜 Complete Function List:")
    print("-" * 30)
    for i, func in enumerate(functions, 1):
        name = func.get("name", "unknown")
        func_id = func.get("id", "unknown")
        template_count = len(func.get("templates", []))
        print(f"  {i:2d}. {name} ({func_id}) - {template_count} templates")
    
    # Show some example mappings
    print(f"\n🎯 Example Template Mappings:")
    print("-" * 35)
    
    sample_functions = functions[:5]  # Show first 5 as examples
    for func in sample_functions:
        name = func.get("name", "unknown")
        templates = func.get("templates", [])
        print(f"\n  Function: {name}")
        for template in templates:
            print(f"    - \"{template}\"")
    
    print(f"\n✅ Analysis complete!")
    return total_functions


if __name__ == "__main__":
    analyze_function_dictionary()
