from typing import List, Dict, Any, Union

class Assembler:
    def assemble(self, steps: List[Dict[str, Any]]) -> Dict[str, Union[List[Dict[str, Any]], float]]:
        if not steps:
            return {"steps": [], "overall_confidence": 0.0}
        avg_conf = sum(s["confidence"] for s in steps) / len(steps)
        return {"steps": steps, "overall_confidence": avg_conf}


