from typing import List, Dict, Any

class RuleEngine:
    def parse(self, text: str) -> List[Dict[str, Any]]:
        # Very simple demo: detect "login"
        steps: List[Dict[str, Any]] = []
        if "login" in text.lower():
            steps.append({
                "function": "AUTH.LOGIN",
                "args": {"username": "admin", "password": "******"},
                "confidence": 0.9
            })
        return steps