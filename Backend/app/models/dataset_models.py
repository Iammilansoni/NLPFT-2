"""
Database models for datasets
Add these to your existing models file
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Dataset(Base):
    __tablename__ = "datasets"
    
    dataset_id = Column(String, primary_key=True)
    template_id = Column(String, ForeignKey("templates.template_id"), nullable=False)
    user_id = Column(String, nullable=False)
    rows_requested = Column(Integer, nullable=False)
    rows_generated = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    llm_model = Column(String, nullable=False)
    custom_prompt = Column(Text, nullable=True)
    temperature = Column(Float, default=0.7)
    embedding_model = Column(String, nullable=True)
    vector_db_collection = Column(String, nullable=True)
    csv_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    embedded_at = Column(DateTime, nullable=True)

class DatasetJob(Base):
    __tablename__ = "dataset_jobs"
    
    job_id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey("datasets.dataset_id"), nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    rows_generated = Column(Integer, default=0)
    total_rows = Column(Integer, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
