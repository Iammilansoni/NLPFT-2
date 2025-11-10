"""
API v1 routes
"""

from fastapi import APIRouter
from app.api.v1 import templates

router = APIRouter(prefix="/v1")

# Include all v1 routers
router.include_router(templates.router)
