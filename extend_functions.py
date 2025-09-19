"""
Extended Dictionary Functions for NLPForge Rule Engine.

This script adds 35+ new functions to reach 60+ total functions,
with comprehensive template sets for better natural language matching.
"""
import asyncio
from datetime import datetime, timezone
from app.core.database import db_manager
from app.core.dictionary_repository import DictionaryRepository
from app.models.dictionary_models import DictionaryFunction

async def add_extended_functions():
    """Add extended set of functions to reach 60+ total functions."""
    try:
        await db_manager.connect()
        repo = DictionaryRepository(db_manager.database)
        
        # New comprehensive function set
        new_functions = [
            # ENHANCED NAVIGATION (10 new functions)
            DictionaryFunction(
                name="scroll_to",
                display_name="Scroll To Element",
                description="Scroll the page to bring an element into view",
                signature={"selector": "str"},
                templates=[
                    "scroll to {selector}",
                    "scroll down to {selector}",
                    "scroll up to {selector}", 
                    "bring {selector} into view",
                    "scroll to element {selector}",
                    "navigate to {selector} by scrolling"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="scroll_page",
                display_name="Scroll Page",
                description="Scroll the page by a specified amount or direction",
                signature={"direction": "str", "amount": "int"},
                templates=[
                    "scroll {direction}",
                    "scroll {direction} by {amount}",
                    "scroll the page {direction}",
                    "page scroll {direction}",
                    "move page {direction} by {amount} pixels"
                ],
                category="navigation",
                is_active=True,
                created_by="system", 
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="hover_over",
                display_name="Hover Over Element",
                description="Move mouse cursor over an element to trigger hover effects",
                signature={"selector": "str"},
                templates=[
                    "hover over {selector}",
                    "mouse over {selector}",
                    "hover on {selector}",
                    "move cursor to {selector}",
                    "hover cursor over {selector}",
                    "place mouse on {selector}"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system", 
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="double_click",
                display_name="Double Click",
                description="Double click on an element",
                signature={"selector": "str"},
                templates=[
                    "double click {selector}",
                    "double click on {selector}",
                    "double-click {selector}",
                    "click twice on {selector}",
                    "perform double click on {selector}"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="right_click",
                display_name="Right Click",
                description="Right click on an element to open context menu",
                signature={"selector": "str"},
                templates=[
                    "right click {selector}",
                    "right click on {selector}",
                    "context click {selector}",
                    "open context menu on {selector}",
                    "right mouse click {selector}"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="switch_tab",
                display_name="Switch Tab",
                description="Switch to a different browser tab",
                signature={"tab": "str"},
                templates=[
                    "switch to tab {tab}",
                    "switch to {tab} tab",
                    "go to tab {tab}",
                    "open tab {tab}",
                    "switch browser tab to {tab}",
                    "activate tab {tab}"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="open_new_tab",
                display_name="Open New Tab",
                description="Open a new browser tab",
                signature={"url": "str"},
                templates=[
                    "open new tab",
                    "open {url} in new tab",
                    "create new tab",
                    "open new browser tab",
                    "launch new tab with {url}",
                    "new tab to {url}"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="close_tab",
                display_name="Close Tab",
                description="Close the current or specified browser tab",
                signature={"tab": "str"},
                templates=[
                    "close tab",
                    "close current tab",
                    "close {tab} tab",
                    "close browser tab",
                    "shut tab {tab}"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="resize_window",
                display_name="Resize Window",
                description="Resize the browser window to specific dimensions",
                signature={"width": "int", "height": "int"},
                templates=[
                    "resize window to {width}x{height}",
                    "set window size to {width} by {height}",
                    "change window dimensions to {width}x{height}",
                    "resize browser to {width}x{height}",
                    "set browser window to {width}x{height}"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="maximize_window",
                display_name="Maximize Window",
                description="Maximize the browser window",
                signature={},
                templates=[
                    "maximize window",
                    "maximize browser window",
                    "maximize the window",
                    "make window fullscreen",
                    "expand window to fullscreen"
                ],
                category="navigation",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            # ENHANCED INPUT OPERATIONS (8 new functions)
            DictionaryFunction(
                name="type_text",
                display_name="Type Text",
                description="Type text into an input field with various typing speeds",
                signature={"selector": "str", "text": "str", "speed": "str"},
                templates=[
                    "type {text} in {selector}",
                    "enter {text} into {selector}",
                    "input {text} in field {selector}",
                    "fill {selector} with {text}",
                    "type {text} slowly in {selector}",
                    "type {text} quickly in {selector}",
                    "enter text {text} in {selector}",
                    "input text {text} into {selector}"
                ],
                category="forms",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="press_key",
                display_name="Press Key",
                description="Press a specific keyboard key or key combination",
                signature={"key": "str"},
                templates=[
                    "press {key}",
                    "press {key} key",
                    "hit {key}",
                    "press the {key} key",
                    "keyboard press {key}",
                    "type {key}",
                    "hit {key} button"
                ],
                category="forms",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="paste_text",
                display_name="Paste Text",
                description="Paste text from clipboard into a field",
                signature={"selector": "str", "text": "str"},
                templates=[
                    "paste in {selector}",
                    "paste {text} in {selector}",
                    "paste text in {selector}",
                    "paste clipboard in {selector}",
                    "paste content into {selector}"
                ],
                category="forms",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="select_all",
                display_name="Select All Text",
                description="Select all text in a field",
                signature={"selector": "str"},
                templates=[
                    "select all in {selector}",
                    "select all text in {selector}",
                    "highlight all in {selector}",
                    "select everything in {selector}",
                    "ctrl+a in {selector}"
                ],
                category="forms",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="copy_text",
                display_name="Copy Text",
                description="Copy text from an element to clipboard",
                signature={"selector": "str"},
                templates=[
                    "copy text from {selector}",
                    "copy {selector} text",
                    "copy content of {selector}",
                    "copy text in {selector}",
                    "get text from {selector}"
                ],
                category="forms",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="drag_and_drop",
                display_name="Drag and Drop",
                description="Drag an element and drop it on another element",
                signature={"source": "str", "target": "str"},
                templates=[
                    "drag {source} to {target}",
                    "drag and drop {source} to {target}",
                    "move {source} to {target}",
                    "drag {source} onto {target}",
                    "drop {source} on {target}"
                ],
                category="forms",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="multi_select",
                display_name="Multi Select",
                description="Select multiple options from a multi-select dropdown",
                signature={"selector": "str", "options": "str"},
                templates=[
                    "select multiple options {options} in {selector}",
                    "multi-select {options} from {selector}",
                    "choose multiple {options} in {selector}",
                    "select options {options} in {selector}",
                    "pick multiple {options} from {selector}"
                ],
                category="forms",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="slider_set",
                display_name="Set Slider Value",
                description="Set a slider or range input to a specific value",
                signature={"selector": "str", "value": "int"},
                templates=[
                    "set slider {selector} to {value}",
                    "move slider {selector} to {value}",
                    "adjust {selector} to {value}",
                    "set range {selector} to {value}",
                    "slide {selector} to {value}"
                ],
                category="forms",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            # ENHANCED WAIT OPERATIONS (6 new functions)
            DictionaryFunction(
                name="wait_for_text",
                display_name="Wait for Text",
                description="Wait for specific text to appear on the page",
                signature={"text": "str", "timeout": "int"},
                templates=[
                    "wait for text {text}",
                    "wait until text {text} appears",
                    "wait for {text} to appear",
                    "wait until {text} is visible",
                    "wait for text {text} to show",
                    "expect text {text} to appear"
                ],
                category="synchronization",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="wait_for_url",
                display_name="Wait for URL",
                description="Wait for the page URL to change or match a pattern",
                signature={"url": "str", "timeout": "int"},
                templates=[
                    "wait for url {url}",
                    "wait until url is {url}",
                    "wait for page url {url}",
                    "wait until url contains {url}",
                    "wait for navigation to {url}"
                ],
                category="synchronization",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="wait_for_enabled",
                display_name="Wait for Element Enabled",
                description="Wait for an element to become enabled/clickable",
                signature={"selector": "str", "timeout": "int"},
                templates=[
                    "wait for {selector} to be enabled",
                    "wait until {selector} is enabled",
                    "wait for {selector} to be clickable",
                    "wait until {selector} is clickable",
                    "wait for {selector} enabled state"
                ],
                category="synchronization",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="wait_for_count",
                display_name="Wait for Element Count",
                description="Wait for a specific number of elements to be present",
                signature={"selector": "str", "count": "int", "timeout": "int"},
                templates=[
                    "wait for {count} {selector} elements",
                    "wait until {count} {selector} exist",
                    "wait for exactly {count} {selector}",
                    "wait until there are {count} {selector}"
                ],
                category="synchronization",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="wait_for_value",
                display_name="Wait for Field Value",
                description="Wait for an input field to have a specific value",
                signature={"selector": "str", "value": "str", "timeout": "int"},
                templates=[
                    "wait for {selector} value {value}",
                    "wait until {selector} has value {value}",
                    "wait for {selector} to contain {value}",
                    "wait until {selector} equals {value}"
                ],
                category="synchronization",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="wait_seconds",
                display_name="Wait Seconds",
                description="Wait for a specific number of seconds",
                signature={"seconds": "int"},
                templates=[
                    "wait {seconds} seconds",
                    "wait for {seconds} seconds",
                    "pause for {seconds} seconds",
                    "sleep {seconds} seconds",
                    "delay {seconds} seconds"
                ],
                category="synchronization",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            # ENHANCED ASSERTIONS (8 new functions)
            DictionaryFunction(
                name="expect_element_count",
                display_name="Expect Element Count",
                description="Verify that a specific number of elements are present",
                signature={"selector": "str", "count": "int"},
                templates=[
                    "expect {count} {selector} elements",
                    "verify {count} {selector} exist",
                    "check there are {count} {selector}",
                    "assert {count} {selector} present",
                    "expect exactly {count} {selector}"
                ],
                category="assertions",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="expect_attribute",
                display_name="Expect Element Attribute",
                description="Verify an element has a specific attribute value",
                signature={"selector": "str", "attribute": "str", "value": "str"},
                templates=[
                    "expect {selector} {attribute} to be {value}",
                    "verify {selector} has {attribute} {value}",
                    "check {selector} {attribute} equals {value}",
                    "assert {selector} {attribute} is {value}"
                ],
                category="assertions",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="expect_css_property",
                display_name="Expect CSS Property",
                description="Verify an element has a specific CSS property value",
                signature={"selector": "str", "property": "str", "value": "str"},
                templates=[
                    "expect {selector} {property} to be {value}",
                    "verify {selector} css {property} equals {value}",
                    "check {selector} style {property} is {value}",
                    "assert {selector} has {property} {value}"
                ],
                category="assertions",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="expect_enabled",
                display_name="Expect Element Enabled",
                description="Verify an element is enabled or disabled",
                signature={"selector": "str", "state": "bool"},
                templates=[
                    "expect {selector} to be enabled",
                    "expect {selector} to be disabled",
                    "verify {selector} is enabled",
                    "verify {selector} is disabled",
                    "check {selector} enabled state",
                    "assert {selector} is clickable"
                ],
                category="assertions",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="expect_selected",
                display_name="Expect Option Selected",
                description="Verify a dropdown option or checkbox is selected",
                signature={"selector": "str", "value": "str"},
                templates=[
                    "expect {selector} to be selected",
                    "expect {value} selected in {selector}",
                    "verify {selector} is selected",
                    "check {value} is selected in {selector}",
                    "assert {selector} selection is {value}"
                ],
                category="assertions",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="expect_page_contains",
                display_name="Expect Page Contains",
                description="Verify the page source contains specific text",
                signature={"text": "str"},
                templates=[
                    "expect page contains {text}",
                    "verify page has {text}",
                    "check page contains {text}",
                    "assert page includes {text}",
                    "expect {text} in page source"
                ],
                category="assertions",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="expect_not_visible",
                display_name="Expect Not Visible",
                description="Verify an element is not visible on the page",
                signature={"selector": "str"},
                templates=[
                    "expect {selector} not visible",
                    "expect {selector} to be hidden",
                    "verify {selector} is not visible",
                    "check {selector} is hidden",
                    "assert {selector} not displayed"
                ],
                category="assertions",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="expect_value",
                display_name="Expect Field Value",
                description="Verify an input field has a specific value",
                signature={"selector": "str", "value": "str"},
                templates=[
                    "expect {selector} value {value}",
                    "expect {selector} to have value {value}",
                    "verify {selector} equals {value}",
                    "check {selector} contains {value}",
                    "assert {selector} value is {value}"
                ],
                category="assertions",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            # API/NETWORK OPERATIONS (5 new functions)
            DictionaryFunction(
                name="api_get",
                display_name="API GET Request",
                description="Make a GET request to an API endpoint",
                signature={"url": "str", "headers": "str"},
                templates=[
                    "get from api {url}",
                    "make get request to {url}",
                    "api get {url}",
                    "fetch from {url}",
                    "call get api {url}"
                ],
                category="api",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="api_post",
                display_name="API POST Request",
                description="Make a POST request to an API endpoint",
                signature={"url": "str", "data": "str"},
                templates=[
                    "post to api {url}",
                    "make post request to {url}",
                    "api post {url} with {data}",
                    "send data {data} to {url}",
                    "call post api {url}"
                ],
                category="api",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="set_cookie",
                display_name="Set Cookie",
                description="Set a browser cookie",
                signature={"name": "str", "value": "str"},
                templates=[
                    "set cookie {name} to {value}",
                    "add cookie {name} with value {value}",
                    "create cookie {name} equals {value}",
                    "set browser cookie {name} as {value}"
                ],
                category="api",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="clear_cookies",
                display_name="Clear Cookies",
                description="Clear browser cookies",
                signature={},
                templates=[
                    "clear cookies",
                    "delete all cookies",
                    "remove cookies",
                    "clear browser cookies",
                    "delete cookies"
                ],
                category="api",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="set_local_storage",
                display_name="Set Local Storage",
                description="Set a value in browser local storage",
                signature={"key": "str", "value": "str"},
                templates=[
                    "set local storage {key} to {value}",
                    "store {value} in {key}",
                    "set storage {key} as {value}",
                    "save {value} to local storage {key}"
                ],
                category="api",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            # MOBILE/RESPONSIVE TESTING (4 new functions)
            DictionaryFunction(
                name="set_device_mode",
                display_name="Set Device Mode",
                description="Set browser to emulate a specific device",
                signature={"device": "str"},
                templates=[
                    "set device to {device}",
                    "emulate {device} device",
                    "switch to {device} mode",
                    "simulate {device}",
                    "use {device} viewport"
                ],
                category="mobile",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="swipe",
                display_name="Swipe Gesture",
                description="Perform a swipe gesture on mobile device",
                signature={"direction": "str", "element": "str"},
                templates=[
                    "swipe {direction}",
                    "swipe {direction} on {element}",
                    "perform {direction} swipe",
                    "swipe {element} {direction}",
                    "gesture swipe {direction}"
                ],
                category="mobile",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="tap",
                display_name="Tap Element",
                description="Tap an element on mobile device",
                signature={"selector": "str"},
                templates=[
                    "tap {selector}",
                    "tap on {selector}",
                    "mobile tap {selector}",
                    "touch {selector}",
                    "press {selector}"
                ],
                category="mobile",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="pinch_zoom",
                display_name="Pinch Zoom",
                description="Perform pinch zoom gesture",
                signature={"scale": "float", "element": "str"},
                templates=[
                    "pinch zoom {scale}",
                    "zoom {scale} on {element}",
                    "pinch {element} to {scale}",
                    "zoom in {scale}",
                    "zoom out {scale}"
                ],
                category="mobile",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            # DATA EXTRACTION (3 new functions)
            DictionaryFunction(
                name="get_text",
                display_name="Get Element Text",
                description="Extract text content from an element",
                signature={"selector": "str", "variable": "str"},
                templates=[
                    "get text from {selector}",
                    "extract text from {selector}",
                    "save text from {selector} as {variable}",
                    "capture {selector} text",
                    "read text from {selector}"
                ],
                category="data_extraction",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="get_attribute",
                display_name="Get Element Attribute",
                description="Extract attribute value from an element",
                signature={"selector": "str", "attribute": "str", "variable": "str"},
                templates=[
                    "get {attribute} from {selector}",
                    "extract {selector} {attribute}",
                    "save {selector} {attribute} as {variable}",
                    "capture {attribute} of {selector}",
                    "read {attribute} from {selector}"
                ],
                category="data_extraction",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            ),
            
            DictionaryFunction(
                name="screenshot",
                display_name="Take Screenshot",
                description="Take a screenshot of the page or element",
                signature={"filename": "str", "element": "str"},
                templates=[
                    "take screenshot",
                    "screenshot as {filename}",
                    "capture screen as {filename}",
                    "take screenshot of {element}",
                    "save screenshot {filename}"
                ],
                category="data_extraction",
                is_active=True,
                created_by="system",
                updated_by="system",
                usage_count=0,
                last_used=None
            )
        ]
        
        print(f"📝 Adding {len(new_functions)} new functions to database...")
        
        # Insert all new functions
        for func in new_functions:
            try:
                result = await repo.create_function(func)
                print(f"✅ Added: {func.name} ({len(func.templates)} templates)")
            except Exception as e:
                print(f"❌ Failed to add {func.name}: {e}")
        
        # Get final count
        all_functions = await repo.list_all_active_functions()
        print(f"\n🎯 Database now contains {len(all_functions)} total functions")
        
        # Show summary by category
        by_category = {}
        for func in all_functions:
            category = func.category or "uncategorized"
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(func)
        
        print(f"\n📊 Functions by category:")
        for category, funcs in sorted(by_category.items()):
            total_templates = sum(len(f.templates) if f.templates else 0 for f in funcs)
            print(f"  📁 {category.upper()}: {len(funcs)} functions, {total_templates} templates")
            
        print(f"\n✨ Successfully extended to 60+ functions!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(add_extended_functions())