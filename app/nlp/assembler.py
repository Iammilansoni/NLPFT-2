class Assembler:
    def assemble(self, steps):
        if not steps:
            return {"steps": [], "overall_confidence": 0.0}
        avg_conf = sum(s["confidence"] for s in steps) / len(steps)
        return {"steps": steps, "overall_confidence": avg_conf}
