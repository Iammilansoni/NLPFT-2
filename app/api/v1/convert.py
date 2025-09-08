"""Text conversion endpoints for NLPForge API."""

import time
from fastapi import APIRouter, HTTPException

from app.models.schemas import ConvertRequest, ConvertResponse
from app.core.logger import logger

router = APIRouter(prefix="/convert", tags=["convert"])


@router.post("/", response_model=ConvertResponse)
async def convert_text(request: ConvertRequest) -> ConvertResponse:
    """
    Convert text to specified format.
    
    Supported formats:
    - uppercase: Convert to uppercase
    - lowercase: Convert to lowercase
    - title: Convert to title case
    - reverse: Reverse the text
    - base64: Encode to base64
    - url: URL encode
    """
    start_time = time.time()
    
    logger.info(f"🔄 Converting text to {request.target_format}")
    
    try:
        converted_text = await _convert_text(request.text, request.target_format, request.options)
        processing_time = time.time() - start_time
        
        response = ConvertResponse(
            original_text=request.text,
            converted_text=converted_text,
            target_format=request.target_format,
            processing_time=processing_time,
            metadata={
                "original_length": len(request.text),
                "converted_length": len(converted_text),
                "options_used": request.options
            }
        )
        
        logger.info(f"✅ Text conversion completed in {processing_time:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"❌ Text conversion failed: {e}")
        raise HTTPException(status_code=400, detail=f"Conversion failed: {str(e)}")


async def _convert_text(text: str, target_format: str, options: dict) -> str:
    """
    Internal function to perform text conversion.
    """
    if target_format == "uppercase":
        return text.upper()
    elif target_format == "lowercase":
        return text.lower()
    elif target_format == "title":
        return text.title()
    elif target_format == "reverse":
        return text[::-1]
    elif target_format == "base64":
        import base64
        return base64.b64encode(text.encode()).decode()
    elif target_format == "url":
        import urllib.parse
        return urllib.parse.quote(text)
    elif target_format == "capitalize":
        return text.capitalize()
    elif target_format == "snake_case":
        import re
        # Convert to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    elif target_format == "camel_case":
        # Convert to camelCase
        components = text.replace('_', ' ').replace('-', ' ').split()
        return components[0].lower() + ''.join(word.capitalize() for word in components[1:])
    else:
        raise ValueError(f"Unsupported target format: {target_format}")


@router.get("/formats")
async def get_supported_formats() -> dict:
    """
    Get list of supported conversion formats.
    """
    return {
        "formats": [
            {
                "name": "uppercase",
                "description": "Convert text to uppercase",
                "example": "HELLO WORLD"
            },
            {
                "name": "lowercase", 
                "description": "Convert text to lowercase",
                "example": "hello world"
            },
            {
                "name": "title",
                "description": "Convert text to title case",
                "example": "Hello World"
            },
            {
                "name": "capitalize",
                "description": "Capitalize first letter",
                "example": "Hello world"
            },
            {
                "name": "reverse",
                "description": "Reverse the text",
                "example": "dlrow olleh"
            },
            {
                "name": "base64",
                "description": "Encode text to base64",
                "example": "aGVsbG8gd29ybGQ="
            },
            {
                "name": "url",
                "description": "URL encode the text",
                "example": "hello%20world"
            },
            {
                "name": "snake_case",
                "description": "Convert to snake_case",
                "example": "hello_world"
            },
            {
                "name": "camel_case",
                "description": "Convert to camelCase",
                "example": "helloWorld"
            }
        ]
    }