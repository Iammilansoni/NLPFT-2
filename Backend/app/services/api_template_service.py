from sqlalchemy.orm import Session
from app.models.api_template_model import APITemplate
from app.schemas.api_template_schema import APITemplateCreate

def create_api_template(db: Session, template_data: APITemplateCreate):
    new_template = APITemplate(
        api_name=template_data.api_name,
        description=template_data.description,
        base_url=template_data.base_url,
        method=template_data.method,
        body=[param.dict() for param in template_data.body],
        expected_response=template_data.expected_response,
        metadata=template_data.metadata
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template
