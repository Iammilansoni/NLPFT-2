from sqlalchemy import Column, String, JSON, Integer
from app.database.connection import Base

class APITemplate(Base):
    __tablename__ = "api_templates"

    id = Column(Integer, primary_key=True, index=True)
    api_name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    method = Column(String, nullable=False)
    body = Column(JSON, nullable=False)
    expected_response = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
