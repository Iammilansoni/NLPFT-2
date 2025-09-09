class RuleEngine:
    def parse(self, text: str):
        # Very simple demo: detect "login"
        steps = []
        if "login" in text.lower():
            steps.append({
                "function": "AUTH.LOGIN",
                "args": {"username": "admin", "password": "******"},
                "confidence": 0.9
            })
        return steps