"""
Template Loader - Load API templates from multiple sources
Supports: JSON files, PostgreSQL database, runtime additions
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from app.core.logger import logger


class TemplateLoader:
    """
    Load and parse API templates from various sources
    """
    
    def __init__(self):
        self.templates_cache: Dict[str, Dict] = {}
    
    def load_from_json(self, json_path: str) -> List[Dict]:
        """
        Load templates from api_template.json file
        
        Args:
            json_path: Path to api_template.json
            
        Returns:
            List of template dictionaries
            
        Raises:
            FileNotFoundError: If JSON file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        try:
            path = Path(json_path)
            
            if not path.exists():
                logger.error(f"Template JSON file not found: {json_path}")
                raise FileNotFoundError(f"Template file not found: {json_path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract APIs from the JSON structure
            apis = data.get("apis", [])
            version = data.get("version", 1)
            
            templates = []
            for api in apis:
                template = self._parse_json_template(api, version)
                templates.append(template)
                
                # Cache for quick access
                self.templates_cache[template["intent"]] = template
            
            logger.info(f"✅ Loaded {len(templates)} templates from {json_path}")
            return templates
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading templates from JSON: {e}")
            raise
    
    def _parse_json_template(self, api: Dict, version: int = 1) -> Dict:
        """
        Parse JSON API structure to internal template format
        
        Args:
            api: API definition from JSON
            version: Template version
            
        Returns:
            Parsed template dictionary
        """
        # Extract intent from name
        intent = api.get("name", "").lower().replace(" ", "_")
        
        # Extract slots/fields
        slots = api.get("slots", [])
        fields = []
        slot_configs = {}
        
        for slot in slots:
            field_key = slot.get("key")
            if field_key:
                fields.append(field_key)
                slot_configs[field_key] = {
                    "questions": slot.get("questions", []),
                    "required": slot.get("required", False),
                    "default": slot.get("default"),
                    "postprocess": slot.get("postprocess"),
                    "literal": slot.get("literal")
                }
        
        # Extract intent keywords for pattern matching
        intent_keywords = api.get("intent_keywords", [])
        
        # Build template structure
        template = {
            "intent": intent,
            "api_name": api.get("name", intent.replace("_", " ").title()),
            "description": f"API for {intent.replace('_', ' ')}",
            "endpoint": api.get("endpoint_template", f"/api/{intent}"),
            "method": "POST",  # Default, can be enhanced
            "fields": fields,
            "intent_keywords": intent_keywords,
            "slots_config": slot_configs,
            "example_queries": self._generate_example_queries(intent, fields),
            "version": version,
            "is_system": True,
            "metadata": {
                "source": "api_template.json",
                "slot_count": len(fields),
                "keyword_count": len(intent_keywords)
            }
        }
        
        return template
    
    def _generate_example_queries(self, intent: str, fields: List[str]) -> List[str]:
        """
        Generate example queries based on intent and fields
        
        Args:
            intent: API intent
            fields: List of field names
            
        Returns:
            List of example query templates
        """
        # Common query patterns
        patterns = {
            "login": [
                "Login with {username} and {password}",
                "Authenticate credentials for {username}",
                "Sign in as {username} with password {password}"
            ],
            "logout": [
                "Logout from account",
                "Sign out user with token {token}",
                "End session for {token}"
            ],
            "register": [
                "Register new account with {username} and {email}",
                "Create account for {username}",
                "Sign up with email {email} and username {username}"
            ],
            "reset_password": [
                "Reset password for {email}",
                "Forgot password for account {email}",
                "Send password reset link to {email}"
            ],
            "update_profile": [
                "Update profile for user {user_id}",
                "Change name to {name} for user {user_id}",
                "Modify phone number to {phone}"
            ],
            "upload_file": [
                "Upload file {file_name}",
                "Upload {file_type} file named {file_name}",
                "Attach file {file_name}"
            ],
            "download_file": [
                "Download file {file_id}",
                "Get file with id {file_id}",
                "Fetch file {file_id}"
            ],
            "search": [
                "Search for {query}",
                "Find {query}",
                "Look up {query}"
            ],
            "get_user": [
                "Get user details for {user_id}",
                "Retrieve user information {user_id}",
                "Fetch account data for {user_id}"
            ],
            "delete_account": [
                "Delete account {user_id}",
                "Remove user {user_id}",
                "Close account {user_id} with confirmation {confirm}"
            ]
        }
        
        # Return predefined patterns or generate generic ones
        if intent in patterns:
            return patterns[intent]
        
        # Generate generic patterns
        generic_patterns = [
            f"{intent.replace('_', ' ').title()} with " + " and ".join([f"{{{f}}}" for f in fields[:3]]),
            f"Execute {intent.replace('_', ' ')} for " + f"{{{fields[0]}}}" if fields else "",
            f"Process {intent.replace('_', ' ')}"
        ]
        
        return [p for p in generic_patterns if p]
    
    def get_cached_template(self, intent: str) -> Optional[Dict]:
        """
        Get template from cache
        
        Args:
            intent: API intent
            
        Returns:
            Template dictionary or None
        """
        return self.templates_cache.get(intent)
    
    def get_all_cached_templates(self) -> Dict[str, Dict]:
        """
        Get all cached templates
        
        Returns:
            Dictionary of all templates
        """
        return self.templates_cache.copy()
    
    def clear_cache(self):
        """Clear template cache"""
        self.templates_cache.clear()
        logger.info("Template cache cleared")
    
    def validate_template(self, template: Dict) -> tuple[bool, List[str]]:
        """
        Validate template structure
        
        Args:
            template: Template to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        required_fields = ["intent", "api_name", "endpoint", "method", "fields"]
        
        for field in required_fields:
            if field not in template or not template[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate method
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        if template.get("method") and template["method"].upper() not in valid_methods:
            errors.append(f"Invalid HTTP method: {template.get('method')}")
        
        # Validate fields is a list
        if not isinstance(template.get("fields", []), list):
            errors.append("Fields must be a list")
        
        # Validate intent_keywords is a list
        if template.get("intent_keywords") and not isinstance(template["intent_keywords"], list):
            errors.append("Intent keywords must be a list")
        
        is_valid = len(errors) == 0
        return is_valid, errors


# Global instance
_template_loader = None


def get_template_loader() -> TemplateLoader:
    """
    Get global template loader instance (singleton)
    
    Returns:
        TemplateLoader instance
    """
    global _template_loader
    if _template_loader is None:
        _template_loader = TemplateLoader()
    return _template_loader
