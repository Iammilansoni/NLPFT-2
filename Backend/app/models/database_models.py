"""
PostgreSQL Database Models - All Tables
Production-ready multi-tenant schema with Redis vector storage

Architecture:
- PostgreSQL: Structured data + metadata (7 main tables)
- Redis: Vector embeddings with HNSW index

Tables:
1. users - User authentication
2. templates - API templates
3. parameters - API parameters
4. expected_responses - Expected API responses
5. metadata - Template metadata & confidence scores
6. csv_data - Test data (millions of rows)
7. embeddings - Vector embedding metadata (vectors in Redis)

Optimized for:
✅ Multi-tenant isolation (user_id in every table)
✅ Lakhs/millions of CSV rows
✅ Fast Redis vector search
✅ Clean separation of concerns
"""

from sqlalchemy import Column, Text, Integer, TIMESTAMP, ForeignKey, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.postgres import Base


class User(Base):
    """
    Users table - Multi-tenant user management
    """
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_name = Column(Text, nullable=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    password = Column(Text, nullable=False)  # Bcrypt hashed
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    parameters = relationship("Parameter", back_populates="user", cascade="all, delete-orphan")
    expected_responses = relationship("ExpectedResponse", back_populates="user", cascade="all, delete-orphan")
    metadata_records = relationship("Metadata", back_populates="user", cascade="all, delete-orphan")
    csv_data = relationship("CSVData", back_populates="user", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="user", cascade="all, delete-orphan")


class Template(Base):
    """
    Templates table - API templates per user
    """
    __tablename__ = "templates"
    
    t_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    api_name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    base_url = Column(Text, nullable=True)
    method = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="templates")
    parameters = relationship("Parameter", back_populates="template", cascade="all, delete-orphan")
    expected_responses = relationship("ExpectedResponse", back_populates="template", cascade="all, delete-orphan")
    metadata_records = relationship("Metadata", back_populates="template", cascade="all, delete-orphan")
    csv_data = relationship("CSVData", back_populates="template", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="template")
    
    # Index for fast user queries
    __table_args__ = (
        Index('idx_templates_user', 'user_id'),
    )


class Parameter(Base):
    """
    Parameters table - API parameters
    """
    __tablename__ = "parameters"
    
    parameter_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=True)
    type = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="parameters")
    template = relationship("Template", back_populates="parameters")
    
    # Index for fast template queries
    __table_args__ = (
        Index('idx_params_template', 't_id'),
    )


class ExpectedResponse(Base):
    """
    Expected responses table - API response schemas
    """
    __tablename__ = "expected_responses"
    
    response_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=False)
    status = Column(Integer, nullable=True)
    fields = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="expected_responses")
    template = relationship("Template", back_populates="expected_responses")
    
    # Index for fast template queries
    __table_args__ = (
        Index('idx_exp_template', 't_id'),
    )


class Metadata(Base):
    """
    Metadata table - Template metadata and confidence scores
    """
    __tablename__ = "metadata"
    
    metadata_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Numeric, nullable=True)
    remarks = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="metadata_records")
    template = relationship("Template", back_populates="metadata_records")
    
    # Index for fast template queries
    __table_args__ = (
        Index('idx_metadata_template', 't_id'),
    )


class CSVData(Base):
    """
    CSV Data table - Test data storage (optimized for millions of rows)
    """
    __tablename__ = "csv_data"
    
    csv_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=False)
    query = Column(Text, nullable=True)
    api_name = Column(Text, nullable=True)
    endpoint = Column(Text, nullable=True)
    request = Column(JSONB, nullable=True)
    response = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="csv_data")
    template = relationship("Template", back_populates="csv_data")
    embeddings = relationship("Embedding", back_populates="csv_data")
    
    # CRITICAL indexes for scaling to millions
    __table_args__ = (
        Index('idx_csv_user_template', 'user_id', 't_id'),
        Index('idx_csv_template', 't_id'),
    )


class Embedding(Base):
    """
    Embeddings table - Vector embedding metadata (vectors stored in Redis)
    
    Redis Key Format: embedding:{user_id}:{t_id}:{csv_id}
    Actual vectors stored in Redis, this table only tracks metadata
    """
    __tablename__ = "embeddings"
    
    emb_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id"), nullable=True)
    csv_id = Column(UUID(as_uuid=True), ForeignKey("csv_data.csv_id"), nullable=True)
    redis_key = Column(Text, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="embeddings")
    template = relationship("Template", back_populates="embeddings")
    csv_data = relationship("CSVData", back_populates="embeddings")
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_embeddings_template', 't_id'),
        Index('idx_embeddings_user', 'user_id'),
    )
