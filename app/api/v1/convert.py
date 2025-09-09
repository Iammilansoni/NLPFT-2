"""Text conversion endpoints for NLPForge API."""

from fastapi import APIRouter
from typing import List, Dict, Any
from app.models.schemas import ConvertRequest, ConvertResponse
from app.core.logger import logger
from app.nlp.rule_engine import RuleEngine
from app.nlp.assembler import Assembler

router = APIRouter(prefix="/convert", tags=["convert"])

# Initialize components
rule_engine = RuleEngine()
assembler = Assembler()


@router.post("/", response_model=ConvertResponse)
async def convert(request: ConvertRequest) -> ConvertResponse:
    """
    Convert natural language instructions into structured test steps.
    """
    logger.info(f"Received text: {request.text}")
    # Step 1: Rule Engine Parsing
    steps: List[Dict[str, Any]] = rule_engine.parse(request.text)  # type: ignore
    logger.debug(f"Rule Engine Output: {steps}")

    # (Step 2: later add Semantic Matcher + Ranker)

    # Step 3: Assemble Final JSON
    result: Dict[str, Any] = assembler.assemble(steps)  # type: ignore
    logger.info(f"Conversion completed: {result}")

    return ConvertResponse(
        original_text=request.text,
        converted_text=str(result),
        target_format="nlp_steps",
        processing_time=0.0,
        metadata={"steps_count": len(steps)}
    )