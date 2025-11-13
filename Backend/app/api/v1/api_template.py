import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from nlpforge.config.core.database import get_db
from nlpforge.storage.models import APITemplateModel
from mlpforge.storage.schemas import APITemplate, APITemplateResponse

router = APIRouter()

@router.post("/create", response_model=APITemplateResponse)
async def create_api_template(template: APITemplate, db: Session = Depends(get_db)):
    if len(template.description.split()) < 500:
        raise HTTPException(status_code=400, detail="Description must contain at least 500 words.")

    try:
        template_id = str(uuid.uuid4())

        db_entry = APITemplateModel(
            id=template_id,
            api_name=template.api_name,
            description=template.description,
            base_url=template.base_url,
            method=template.method,
            template_json=template.dict(),
            created_at=datetime.utcnow()
        )

        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)

        return {
            "message": "API Template created successfully.",
            "template_id": template_id,
            "stored_template": db_entry.template_json
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
