from typing import List, Dict, Any, Union
import re

class Assembler:
    """
    Enhanced assemb        elif function == "type" or function == "enter_text" or function == "fill":
            selector = args.get("selector") or args.get("field", "")
            value = args.get("value", "")
            return {
                "action": "type",
                "selector": self._normalize_selector(selector),
                "value": value,
                "confidence": confidence
            }converts internal NLP steps to the desired action/selector/value format.
    """
    
    def __init__(self):
        # Mapping of internal function names to standard action names
        self.function_to_action = {
            "type": "type",
            "enter_text": "type", 
            "click": "click",
            "open_url": "open_url",
            "login": "login",
            "wait_for_appear": "wait_for_appear",
            "wait_for_disappear": "wait_for_disappear",
            "assert_text": "assert_text",
            "check": "check",
            "upload_file": "upload_file",
            "scroll_to": "scroll_to",
            "select": "select",
            "unresolved": "unresolved"
        }
    
    def _normalize_selector(self, selector: str) -> str:
        """
        Convert field descriptions to proper CSS selectors when possible.
        """
        if not selector:
            return selector
            
        # If already a CSS selector, return as-is
        if selector.startswith(('#', '.', '[')) or selector.startswith('xpath='):
            return selector
            
        selector_lower = selector.lower().strip()
        
        # Common field mappings
        field_mappings = {
            'email': '#email',
            'e-mail': '#email', 
            'mail': '#email',
            'email field': '#email',
            'password': '#password',
            'pass': '#password',
            'password field': '#password',
            'username': '#username',
            'user': '#username',
            'login': '#username',
            'username field': '#username',
            'search': '#search',
            'search box': '#search',
            'search field': '#search',
            'submit': '#submit',
            'login button': '#login',
            'submit button': '#submit',
            'save button': '#save',
            'cancel button': '#cancel',
            'close button': '#close',
            'ok button': '#ok'
        }
        
        # Try exact match first
        if selector_lower in field_mappings:
            return field_mappings[selector_lower]
            
        # Try partial matches for common patterns
        for pattern, css_selector in field_mappings.items():
            if pattern in selector_lower:
                return css_selector
                
        # If it looks like a button, add a class selector
        if 'button' in selector_lower:
            # Extract the button name
            button_name = selector_lower.replace(' button', '').replace('button', '').strip()
            button_name = re.sub(r'[^a-zA-Z0-9_-]', '', button_name)
            if button_name:
                return f'.{button_name}-button'
        
        # If it looks like a field, add an ID selector
        if any(keyword in selector_lower for keyword in ['field', 'input', 'box']):
            field_name = selector_lower
            for keyword in ['field', 'input', 'box']:
                field_name = field_name.replace(keyword, '').strip()
            field_name = re.sub(r'[^a-zA-Z0-9_-]', '', field_name)
            if field_name:
                return f'#{field_name}'
        
        # Return original if no normalization possible
        return selector
    
    def _convert_step_to_action_format(self, step: Dict[str, Any]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Convert internal step format to action/selector/value format.
        """
        function = step.get("function", "unresolved")
        args = step.get("args", {})
        confidence = step.get("confidence", 0.0)
        
        # Handle different function types
        if function == "type" or function == "enter_text":
            selector = args.get("selector") or args.get("field", "")
            value = args.get("value", "")
            return {
                "action": "type",
                "selector": self._normalize_selector(selector),
                "value": value,
                "confidence": confidence
            }
            
        elif function == "login":
            # Split login into two type actions
            username = args.get("username", "")
            password = args.get("password", "")
            return [
                {
                    "action": "type",
                    "selector": "#username",
                    "value": username,
                    "confidence": confidence
                },
                {
                    "action": "type", 
                    "selector": "#password",
                    "value": password,
                    "confidence": confidence
                }
            ]
            
        elif function == "click":
            selector = args.get("selector", "")
            return {
                "action": "click",
                "selector": self._normalize_selector(selector),
                "confidence": confidence
            }
            
        elif function == "open_url":
            url = args.get("url", "")
            return {
                "action": "open_url",
                "url": url,
                "confidence": confidence
            }
            
        elif function == "wait_for_appear":
            selector = args.get("selector") or args.get("element", "")
            return {
                "action": "wait_for_appear",
                "selector": self._normalize_selector(selector),
                "confidence": confidence
            }
            
        elif function == "wait_for_disappear" or function == "wait_for_invisible":
            selector = args.get("selector") or args.get("element", "")
            return {
                "action": "wait_for_disappear", 
                "selector": self._normalize_selector(selector),
                "confidence": confidence
            }
            
        elif function == "assert_text" or function == "expect_text":
            value = args.get("expected", "") or args.get("value", "")
            selector = args.get("selector", "body")
            return {
                "action": "assert_text",
                "value": value,
                "selector": selector,
                "confidence": confidence
            }
            
        elif function == "expect_visible":
            selector = args.get("selector", "")
            return {
                "action": "assert_visible",
                "selector": self._normalize_selector(selector),
                "confidence": confidence
            }
            
        elif function == "select_dropdown" or function == "select":
            selector = args.get("selector", "")
            value = args.get("value") or args.get("option", "")
            return {
                "action": "select",
                "selector": self._normalize_selector(selector),
                "value": value,
                "confidence": confidence
            }
            
        elif function == "uncheck":
            selector = args.get("selector", "")
            return {
                "action": "uncheck",
                "selector": self._normalize_selector(selector),
                "confidence": confidence
            }
            
        elif function == "check":
            selector = args.get("selector", "")
            return {
                "action": "check",
                "selector": self._normalize_selector(selector),
                "confidence": confidence
            }
            
        elif function == "upload_file":
            selector = args.get("selector", "")
            file = args.get("file") or args.get("filename", "")
            return {
                "action": "upload_file",
                "selector": self._normalize_selector(selector),
                "file": file,
                "confidence": confidence
            }
            
        elif function == "scroll_to":
            selector = args.get("selector") or args.get("element", "")
            return {
                "action": "scroll_to",
                "selector": self._normalize_selector(selector),
                "confidence": confidence
            }
            
        else:
            # Unresolved or unknown function
            return {
                "action": "unresolved",
                "text": args.get("text", ""),
                "tokens": args.get("tokens", []),
                "confidence": confidence
            }
    
    def assemble(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert internal steps to the desired action/selector/value format.
        """
        if not steps:
            return {"steps": [], "overall_confidence": 0.0}
        
        converted_steps: List[Dict[str, Any]] = []
        total_confidence = 0.0
        step_count = 0
        
        for step in steps:
            converted = self._convert_step_to_action_format(step)
            
            # Handle cases where one step becomes multiple steps (like login)
            if isinstance(converted, list):
                for sub_step in converted:
                    converted_steps.append(sub_step)
                    total_confidence += sub_step.get("confidence", 0.0)
                    step_count += 1
            else:
                converted_steps.append(converted)
                total_confidence += converted.get("confidence", 0.0)
                step_count += 1
        
        avg_confidence = total_confidence / step_count if step_count > 0 else 0.0
        
        return {
            "steps": converted_steps,
            "overall_confidence": round(avg_confidence, 3)
        }


