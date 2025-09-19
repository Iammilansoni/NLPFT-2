"""Text conversion endpoints for NLPForge API."""

import time
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import APIRouter

from app.models.schemas import ConvertRequest, ConvertResponse
from app.core.logger import logger
from app.nlp.enhanced_rule_engine import EnhancedRuleEngine
from app.nlp.new_assembler import assemble_steps

router = APIRouter(prefix="/convert", tags=["convert"])

# Use a shared engine instance
_engine = EnhancedRuleEngine()

@router.post("/", response_model=ConvertResponse)
async def convert(request: ConvertRequest) -> ConvertResponse:
    """
    Convert natural language instructions into structured test steps.
    
    This endpoint uses the Enhanced Rule Engine with improved assembler:
    1. Enhanced Rule Engine with advanced clause splitting and heuristics
    2. New assembler with multi-fill expansion and deduplication
    3. Improved confidence scoring and token resolution
    """
    start_time = time.time()
    logger.info(f"🚀 Convert request: {request.text[:100]}...")
    
    try:
        loop = asyncio.get_running_loop()
        
        # Run parse in threadpool so FastAPI's async loop isn't blocked
        engine_result = await loop.run_in_executor(None, _engine.parse, request.text)
        
        # Extract raw steps from Enhanced Rule Engine result
        raw_steps = engine_result.get("steps", []) or engine_result.get("candidates", []) or []
        unresolved = engine_result.get("unresolved_tokens", [])
        
        logger.debug("Engine returned %d raw steps and %d unresolved tokens", len(raw_steps), len(unresolved))
        logger.debug("Raw steps preview: %s", raw_steps[:4])
        
        # Pass to new assembler which expands multi-actions, filters empty args, dedups
        assembled = assemble_steps(raw_steps, original_text=request.text)
        
        # Merge unresolved tokens from engine and assembler
        assembled_unresolved = assembled.get("unresolved_tokens", [])
        final_unresolved = list(dict.fromkeys((unresolved or []) + assembled_unresolved))
        
        # Convert steps to the expected format for the test script
        converted_steps = []
        for step in assembled.get("steps", []):
            converted_step = {
                "action": step.get("function", "unknown"),
                "confidence": step.get("confidence", 0.0)
            }
            # Add args as individual fields for compatibility
            args = step.get("args", {})
            converted_step.update(args)
            converted_steps.append(converted_step)
        
        overall_confidence = assembled.get("overall_confidence", engine_result.get("overall_confidence", 0.0))
        processing_time_ms = engine_result.get("processing_time_ms", 0.0)
        
        logger.info(
            f"✅ Enhanced conversion: {len(converted_steps)} steps, "
            f"confidence {overall_confidence:.3f}, "
            f"unresolved: {len(final_unresolved)}"
        )
        
        # Create response in expected format
        result_dict = {
            "steps": converted_steps,
            "overall_confidence": overall_confidence,
            "unresolved_tokens": final_unresolved,
            "metadata": {
                "steps_count": len(converted_steps),
                "overall_confidence": overall_confidence,
                "clauses_processed": engine_result.get("metadata", {}).get("clauses_processed", 1),
                "patterns_tried": engine_result.get("metadata", {}).get("patterns_tried", 0),
                "processing_time_ms": processing_time_ms,
                "engine_version": "enhanced_v2",
                "timestamp": engine_result.get("metadata", {}).get("timestamp", "")
            }
        }
        
        # Calculate total processing time
        total_time = (time.time() - start_time) * 1000
        
        logger.info(f"🎉 Conversion completed: {len(converted_steps)} steps in {total_time:.1f}ms")
        logger.debug("Convert response steps=%d unresolved=%d", len(converted_steps), len(final_unresolved))
        
        # Return Enhanced Rule Engine response
        converted_json = json.dumps(result_dict, indent=2)
        return ConvertResponse(
            original_text=request.text,
            converted_text=converted_json,
            target_format=request.target_format or "nlp_steps",
            processing_time=total_time / 1000.0,
            metadata={
                "steps_count": len(converted_steps),
                "overall_confidence": overall_confidence,
                "rule_engine_version": "enhanced_v2",
                "unresolved_tokens_count": len(final_unresolved),
                "processing_breakdown": {
                    "rule_engine_ms": processing_time_ms,
                    "total_ms": total_time
                }
            }
        )
        
    except Exception as e:
        logger.exception(f"❌ Enhanced convert endpoint failed: {e}")
        
        # Return error response
        error_time = (time.time() - start_time) * 1000
        return ConvertResponse(
            original_text=request.text,
            converted_text=json.dumps({
                "error": "Enhanced Rule Engine conversion failed", 
                "message": str(e),
                "steps": [],
                "overall_confidence": 0.0
            }),
            target_format=request.target_format or "nlp_steps",
            processing_time=error_time / 1000.0,
            metadata={
                "error": True,
                "steps_count": 0,
                "overall_confidence": 0.0,
                "rule_engine_version": "enhanced_v2"
            }
        )