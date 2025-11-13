from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.api_template_schema import APITemplateCreate
from app.services.api_template_service import create_api_template

router = APIRouter(prefix="/api-template", tags=["API Template"])

@router.post("/create")
def create_api_template_endpoint(template: APITemplateCreate, db: Session = Depends(get_db)):
    """
    Create a new API template with detailed description and structured body.
    """
    try:
        created_template = create_api_template(db, template)
        return {"status": "success", "data": created_template}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
