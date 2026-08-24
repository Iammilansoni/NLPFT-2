"""
PostgreSQL Database Models - Enterprise Multi-Tenant AI-Powered API Testing Platform
Schema for complex domain APIs (Telecom, Defense, RF, Satellite, 5G/6G, Drones)

Platform Purpose:
Understanding & testing cryptic domain APIs like:
- Create_fft_with_no_pilot_signal()
- Compute_phase_noise_map()
- Generate_beamforming_vectors()
- Run_harq_retransmission()

Postman-Style Template Builder with strict validation (min 500 words, 3+ samples)
LLM-powered dataset generation with high variation & error injection
Multi-tenant isolation with approval workflow (draft→review→approved)
Vector embeddings for semantic search (Redis)

Dataset Generation Flow:
1. User creates template with 500+ word description, JSON schema, samples, domain tags
2. Template goes through approval workflow (draft → review → approved)
3. LLM receives full template context + user's custom prompt
4. LLM generates CSV with: 70% valid, 20% edge cases, 10% extreme scenarios
5. Output includes: variations, typos, mistakes, boundary conditions, realistic noise
6. CSV stored, embeddings created, semantic search enabled

Automatic Embeddings → Redis Vector DB:
After dataset generation:
System automatically embeds dataset rows using user's selected model (Settings)
Supported models: 384-dim (MiniLM, CPU-friendly), 768-dim (SBERT), 1536-dim (High accuracy)
Vectors stored in Redis ONLY: embedding:{u_id}:{t_id}:{csv_id}
Metadata stored in PostgreSQL: model_name, dimension, redis_namespace, timestamps
Redis HNSW index created per-dimension (384/768/1536)
High-speed similarity search with multi-tenant separation

Tables (as per diagram):
1. USERS - User authentication (u_id, user_name, email, password, created_at)
2. USER_SETTINGS - Embedding model preferences (default_embedding_model, dimension, auto_embed_on_generation)
3. TEMPLATES - API templates with domain context (min 500 words, 3+ samples, domain tags, JSON schema)
4. PARAMETERS - API parameters (name, type, required, example, description)
5. EXPECTED_RESPONSES - Expected API responses (status + fields JSON)
6. METADATA - Template metadata (confidence, expert notes, security classification, status: draft→review→approved)
7. CSV_DATA - LLM-generated test data with variations, errors, edge cases (70/20/10 split)
8. EMBEDDINGS - Vector metadata (redis_key, model_name, dimension, redis_namespace, auto_generated)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.postgres import Base


def utc_now():
    """Returns current UTC time as timezone-naive for PostgreSQL TIMESTAMP WITHOUT TIME ZONE columns.

    This is intentionally timezone-naive because all TIMESTAMP columns in this schema
    use WITHOUT TIME ZONE. SQLAlchemy stores these as naive datetimes in UTC by convention.

    For timezone-aware UTC datetimes (e.g., JWT expiry comparisons), use:
        from app.core.time_utils import utc_now_aware
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    """
    USERS table - Multi-tenant user authentication
    Core fields from diagram: PK=u_id, user_name, email, password, created_at
    Enhanced fields: is_active, email_verified, google_id for OAuth
    """
    __tablename__ = "users"
    
    u_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_name = Column(Text, nullable=True)
    email = Column(Text, unique=True, nullable=False, index=True)
    password = Column(Text, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)  # 0=disabled, 1=active
    is_expert = Column(Integer, nullable=False, default=0)  # 0=regular user, 1=expert (can approve templates)
    is_admin = Column(Integer, nullable=False, default=0)  # 0=regular user, 1=admin (grants roles, rotates keys)
    email_verified = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    
    # Relationships
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")
    parameters = relationship("Parameter", back_populates="user", cascade="all, delete-orphan")
    expected_responses = relationship("ExpectedResponse", back_populates="user", cascade="all, delete-orphan")
    metadata_records = relationship("Metadata", back_populates="user", cascade="all, delete-orphan")
    csv_data = relationship("CSVData", back_populates="user", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="user", cascade="all, delete-orphan")
    llm_configs = relationship("LLMProviderConfig", back_populates="user", cascade="all, delete-orphan")


class UserSettings(Base):
    """
    USER_SETTINGS table - User preferences for embedding models and LLMs
    
    Supported Embedding Models:
    384-dim: MiniLM (CPU-friendly, fast)
    768-dim: SBERT (balanced performance)
    1536-dim: High accuracy (resource-intensive)
    Future expansion supported
    
    After dataset generation, system automatically embeds rows using selected model
    """
    __tablename__ = "user_settings"
    
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), primary_key=True)
    
    # Embedding model preferences
    default_embedding_model = Column(Text, nullable=False, default="nomic-embed-text")  # Default 768-dim Ollama model
    embedding_dimension = Column(Integer, nullable=False, default=768)  # 384, 768, or 1024
    
    # LLM preferences - Now links to LLMProviderConfig for dynamic configuration
    preferred_llm = Column(Text, nullable=True)  # Legacy field, kept for backward compatibility
    default_llm_config_id = Column(UUID(as_uuid=True), ForeignKey("llm_provider_configs.config_id", ondelete="SET NULL"), nullable=True)
    
    # Auto-embedding on dataset generation
    auto_embed_on_generation = Column(Integer, nullable=False, default=1)  # 0=no, 1=yes
    
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at = Column(TIMESTAMP, default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="settings")
    default_llm_config = relationship("LLMProviderConfig", foreign_keys=[default_llm_config_id])


class LLMProviderConfig(Base):
    """
    LLM_PROVIDER_CONFIGS table - User's LLM provider configurations
    
    Stores configuration for multiple LLM providers per user:
    - OpenAI, Anthropic, Google Gemini, Ollama, HuggingFace, Custom
    - Encrypted API keys for security
    - Model parameters (temperature, max_tokens, etc.)
    - Connection test history
    
    Each user can have multiple configs and set one as default.
    """
    __tablename__ = "llm_provider_configs"
    
    config_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Provider identification
    name = Column(Text, nullable=False)  # User-friendly name (e.g., "My OpenAI", "Production Gemini")
    provider = Column(Text, nullable=False)  # Provider type: openai, anthropic, google, ollama, huggingface, deepseek, custom
    is_default = Column(Integer, default=0)  # 0=no, 1=yes (only one default per user)
    is_active = Column(Integer, default=1)  # 0=disabled, 1=active
    
    # Connection settings
    base_url = Column(Text, nullable=True)  # Custom base URL (for self-hosted, proxies, DeepSeek, etc.)
    api_key_encrypted = Column(Text, nullable=True)  # Encrypted API key (Fernet encryption)
    model_name = Column(Text, nullable=False)  # Model identifier (e.g., "gpt-4", "claude-3-opus", "llama3.1:8b")
    model_type = Column(Text, default="chat")  # Model capability: chat, completion, embeddings
    
    # Generation parameters (stored as JSONB for flexibility)
    config_params = Column(JSONB, default=lambda: {
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 0.9,
        "timeout": 120.0,
        "max_retries": 3
    })
    
    # Connection test metadata
    last_tested_at = Column(TIMESTAMP, nullable=True)
    last_test_success = Column(Integer, nullable=True)  # 0=failed, 1=success
    last_test_message = Column(Text, nullable=True)  # Error message or success info
    last_test_latency_ms = Column(Numeric(10, 2), nullable=True)  # Response time in ms
    
    # Audit timestamps
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at = Column(TIMESTAMP, default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="llm_configs")
    
    def __repr__(self):
        return f"<LLMProviderConfig {self.name} ({self.provider}/{self.model_name})>"


# Index for fast user config lookups
Index("idx_llm_configs_user_active", LLMProviderConfig.u_id, LLMProviderConfig.is_active)
Index("idx_llm_configs_user_default", LLMProviderConfig.u_id, LLMProviderConfig.is_default)

# Partial unique index to enforce only one default config per user
Index(
    "idx_llm_configs_user_single_default",
    LLMProviderConfig.u_id,
    unique=True,
    postgresql_where=(LLMProviderConfig.is_default == 1)
)




class Template(Base):
    """
    TEMPLATES table - Postman-style API templates for complex domain APIs
    Core fields from diagram: PK=t_id, FK=u_id, api_name, description, base_url, method, created_at, Field
    
    Enhanced for Enterprise Template Builder:
    Detailed description (MINIMUM 500 words) explaining domain context
    JSON Schema for strict request/response validation
    Sample requests & responses (minimum 3 examples)
    Domain tags (telecom, fft, mimo, encryption, etc.)
    Auth configuration & headers
    Rate limiting & assertions
    """
    __tablename__ = "templates"
    
    t_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    
    # Core API definition (from diagram)
    api_name = Column(Text, nullable=True)
    description = Column(Text, nullable=True)  # MINIMUM 500 words explaining domain context
    base_url = Column(Text, nullable=True)
    endpoint = Column(Text, nullable=True)  # API endpoint path (e.g., /api/v1/users)
    method = Column(Text, nullable=True)  # GET, POST, PUT, DELETE, PATCH
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    Field = Column(Text, nullable=True)  # Type field from diagram
    
    # JSON Schema for strict validation
    json_schema = Column(JSONB, nullable=True)  # Request body schema with types, enums, constraints
    response_schema = Column(JSONB, nullable=True)  # Expected response schema
    
    # Sample data (minimum 3 examples required for LLM understanding)
    sample_requests = Column(JSONB, nullable=True)  # Array of 3+ request examples
    sample_responses = Column(JSONB, nullable=True)  # Array of 3+ response examples
    
    # Domain context & classification
    domain_tags = Column(JSONB, nullable=True)  # ['telecom', 'fft', 'rf', 'mimo', 'encryption']
    
    # Auth & headers configuration
    auth_config = Column(JSONB, nullable=True)  # {"type": "bearer", "token_env": "API_KEY"}
    headers = Column(JSONB, nullable=True)  # {"Content-Type": "application/json"}
    
    # Validation & testing
    assertions = Column(JSONB, nullable=True)  # Test assertions
    rate_limit = Column(JSONB, nullable=True)  # Rate limiting config
    
    # Dataset generation configuration
    dataset_generation_config = Column(JSONB, nullable=True)  # {"system_prompt": "...", "rules": [...], "quality_split": {"valid": 70, "edge": 20, "extreme": 10}}
    
    updated_at = Column(TIMESTAMP, default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="templates")
    datasets = relationship("Dataset", back_populates="template", cascade="all, delete-orphan")
    parameters = relationship("Parameter", back_populates="template", cascade="all, delete-orphan")
    expected_responses = relationship("ExpectedResponse", back_populates="template", cascade="all, delete-orphan")
    metadata_records = relationship("Metadata", back_populates="template", cascade="all, delete-orphan")
    csv_data = relationship("CSVData", back_populates="template", cascade="all, delete-orphan")
    embeddings = relationship("Embedding", back_populates="template")
    
    # Indexes for production performance
    __table_args__ = (
        Index('idx_templates_user', 'u_id'),
        Index('idx_templates_created_at', 'created_at'),
        Index('idx_templates_updated_at', 'updated_at'),
        Index('idx_templates_api_name', 'api_name'),
    )


class Parameter(Base):
    """
    PARAMETERS table - API parameters with validation
    Core fields from diagram: PK=p_id, FK=u_id, FK=t_id, name, type, description
    Enhanced fields: required, example (for Template Builder parameter table)
    """
    __tablename__ = "parameters"
    
    p_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=True)
    type = Column(Text, nullable=True)  # string, integer, float, boolean, array, object
    description = Column(Text, nullable=True)
    required = Column(Integer, nullable=False, default=0)  # 0=optional, 1=required
    example = Column(Text, nullable=True)  # Example value for parameter
    
    # Relationships
    user = relationship("User", back_populates="parameters")
    template = relationship("Template", back_populates="parameters")
    
    # Index
    __table_args__ = (
        Index('idx_parameters_template', 't_id'),
        Index('idx_parameters_user', 'u_id'),
    )


class ExpectedResponse(Base):
    """
    EXPECTED_RESPONSES table - Expected API responses
    Matches diagram: PK=r_id, FK=u_id, FK=t_id, Fields: status, fields
    """
    __tablename__ = "expected_responses"
    
    r_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=False)
    status = Column(Integer, nullable=True)
    fields = Column(JSONB, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="expected_responses")
    template = relationship("Template", back_populates="expected_responses")
    
    # Index
    __table_args__ = (
        Index('idx_expected_responses_template', 't_id'),
        Index('idx_expected_responses_user', 'u_id'),
    )


class Metadata(Base):
    """
    METADATA table - Template metadata, confidence scores & approval workflow
    Core fields from diagram: PK=m_id, FK=u_id, FK=t_id, confidence, remarks, created_at
    
    Enhanced for Template Builder:
    Expert notes for domain-specific annotations
    Security classification (public, internal, secret, highly-restricted)
    Template status (draft → review → approved)
    Dataset generation only allowed when status='approved'
    """
    __tablename__ = "metadata"
    
    m_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=False)
    confidence = Column(Numeric, nullable=True)  # Confidence score 0-100
    remarks = Column(Text, nullable=True)  # General remarks
    
    # Expert annotations for domain-specific use cases
    expert_notes = Column(Text, nullable=True)  # Detailed technical notes from domain experts
    
    # Template approval workflow
    status = Column(Text, nullable=False, default="draft")  # draft, review, approved
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # User ID who approved
    approved_at = Column(TIMESTAMP, nullable=True)  # Approval timestamp
    rejected_by = Column(UUID(as_uuid=True), nullable=True)  # User ID who rejected
    rejected_at = Column(TIMESTAMP, nullable=True)  # Rejection timestamp
    submitted_at = Column(TIMESTAMP, nullable=True)  # When submitted for review
    
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at = Column(TIMESTAMP, default=utc_now, onupdate=utc_now)
    
    # Relationships
    user = relationship("User", back_populates="metadata_records")
    template = relationship("Template", back_populates="metadata_records")
    
    # Indexes for production performance - status is critical for workflow queries
    __table_args__ = (
        Index('idx_metadata_template', 't_id'),
        Index('idx_metadata_user', 'u_id'),
        Index('idx_metadata_status', 'status'),
        Index('idx_metadata_created_at', 'created_at'),
        Index('idx_metadata_approved_at', 'approved_at'),
    )


class Dataset(Base):
    """
    DATASETS table - Top-level dataset entity for embedding model governance
    
    Key Design Principle: ONE EMBEDDING MODEL PER DATASET
    Once a dataset is embedded with a specific model, ALL rows must use that model.
    Re-embedding requires explicit user action and wipes previous embeddings.
    
    This model tracks:
    Which embedding model was used (embedding_model)
    Embedding dimension (embedding_dimension)  
    When embedding started/completed
    Embedding status (pending, in_progress, completed, failed)
    Progress tracking (0-100%)
    Total rows and embedded count
    """
    __tablename__ = "datasets"
    
    dataset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="SET NULL"), nullable=True)  # Optional: NULL for uploaded datasets without template
    
    # Dataset identification
    name = Column(Text, nullable=True)  # User-friendly name
    description = Column(Text, nullable=True)  # Dataset description
    csv_path = Column(Text, nullable=False)  # Path to the CSV file
    
    # Embedding model governance - ONE MODEL PER DATASET
    embedding_model = Column(Text, nullable=True)  # Model used: e.g., "nomic-embed-text", "bge-small"
    embedding_dimension = Column(Integer, nullable=True)  # 384, 768, or 1024
    
    # Embedding status tracking
    embedding_status = Column(Text, nullable=False, default="pending")  # pending, in_progress, completed, failed
    embedding_progress = Column(Integer, nullable=False, default=0)  # 0-100%
    embedding_error = Column(Text, nullable=True)  # Error message if failed
    
    # Row counts
    total_rows = Column(Integer, nullable=False, default=0)
    embedded_rows = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    embedding_started_at = Column(TIMESTAMP, nullable=True)
    embedding_completed_at = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, default=utc_now, onupdate=utc_now)
    
    # Generation metadata
    generated_with_llm = Column(Text, nullable=True)  # LLM used for generation
    generation_prompt = Column(Text, nullable=True)  # User's custom prompt
    scenario_distribution = Column(JSONB, nullable=True)  # {"valid": 70, "edge": 20, "extreme": 10}
    
    # Background task tracking
    task_id = Column(Text, nullable=True)  # Current background task ID
    
    # Relationships
    user = relationship("User", back_populates="datasets")
    template = relationship("Template", back_populates="datasets")
    csv_rows = relationship("CSVData", back_populates="dataset", cascade="all, delete-orphan")
    
    # Indexes for fast lookups
    __table_args__ = (
        Index('idx_datasets_user', 'u_id'),
        Index('idx_datasets_template', 't_id'),
        Index('idx_datasets_embedding_model', 'embedding_model'),
        Index('idx_datasets_embedding_status', 'embedding_status'),
        Index('idx_datasets_created_at', 'created_at'),
    )


class CSVData(Base):
    """
    CSV_DATA table - Individual rows of LLM-generated test data
    
    Dataset Generation (LLM-Driven):
    LLM receives:
    - Full template (500+ word description, JSON schema, samples, domain tags)
    - System prompt with strict rules
    - User's custom prompt (e.g., "Generate edge cases with pilot disabled")
    
    LLM outputs CSV with:
    70% valid cases (correct, schema-compliant)
    20% edge cases (boundary conditions, rare combinations)
    10% extreme scenarios (stress tests, worst-case)
    Variations: typos, mistakes, realistic noise
    Synthetic but schema-correct values
    
    Enhanced: Track quality category, variation type, error flags, full generation context
    
    Now linked to parent Dataset for embedding model governance
    """
    __tablename__ = "csv_data"
    
    csv_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="SET NULL"), nullable=True)  # Optional: NULL for uploaded datasets without template
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=True)  # Link to parent dataset
    
    query = Column(Text, nullable=True)  # User's custom prompt (e.g., "Generate edge cases with pilot disabled")
    api_name = Column(Text, nullable=True)
    endpoint = Column(Text, nullable=True)
    request = Column(JSONB, nullable=True)  # Full request JSON
    response = Column(JSONB, nullable=True)  # Expected response JSON
    description = Column(Text, nullable=True)
    
    # Dataset quality tracking (70% valid, 20% edge, 10% extreme)
    data_category = Column(Text, nullable=True)  # valid, edge_case, extreme_scenario
    has_typo = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes (intentional typo)
    has_error = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes (intentional error)
    variation_type = Column(Text, nullable=True)  # boundary, rare_combination, synthetic, noise, etc.
    
    # Model lineage tracking (kept for backward compatibility, primary source is Dataset model)
    generated_with_llm = Column(Text, nullable=True)  # LLM model used (e.g., "gpt-4", "gemini-pro")
    embedded_with_model = Column(Text, nullable=True)  # Embedding model used
    generation_prompt = Column(Text, nullable=True)  # Full prompt sent to LLM (system + user + template context)
    
    # Row-level embedding status
    is_embedded = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes
    embedding_error = Column(Text, nullable=True)  # Error message if embedding failed for this row
    
    # Semantic retrieval metadata (for grouping and re-ranking by t_id)
    intent_type = Column(Text, nullable=True)  # "create", "read", "update", "delete", "query", "unknown"
    confidence_score = Column(Numeric, nullable=True)  # 0.0 - 1.0 confidence score for this query
    
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="csv_data")
    template = relationship("Template", back_populates="csv_data")
    dataset = relationship("Dataset", back_populates="csv_rows")
    embeddings = relationship("Embedding", back_populates="csv_data")
    
    # Indexes
    __table_args__ = (
        Index('idx_csv_data_template', 't_id'),
        Index('idx_csv_data_user', 'u_id'),
        Index('idx_csv_data_dataset', 'dataset_id'),
        Index('idx_csv_data_is_embedded', 'is_embedded'),
    )


class Model(Base):
    """
    MODELS table - Unified registry for all models (embedding + LLM)
    
   
    
    Single source of truth synced from config/models.json
    """
    __tablename__ = "models"
    
    model_id = Column(Text, primary_key=True)  # e.g., "BAAI/bge-small-en-v1.5" or "gemini-pro"
    type = Column(Text, nullable=False)  # "embedding" or "llm"
    name = Column(Text, nullable=False)  # Human-readable name
    dimension = Column(Integer, nullable=True)  # For embedding models: 384, 768, 1536; NULL for LLMs
    context_tokens = Column(Integer, nullable=False)  # Max context length
    cpu_friendly = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes
    provider = Column(Text, nullable=False)  # sentence-transformers, google, openai, anthropic, local
    notes = Column(Text, nullable=True)  # Use cases, notes
    status = Column(Text, nullable=False, default="active")  # active, deprecated
    
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    updated_at = Column(TIMESTAMP, default=utc_now, onupdate=utc_now)
    
    # Indexes
    __table_args__ = (
        Index('idx_models_type', 'type'),
        Index('idx_models_status', 'status'),
        Index('idx_models_dimension', 'dimension'),
    )


class EmbeddingModel(Base):
    """
    EMBEDDING_MODELS table - Registry of supported embedding models
    
    Supported Embedding Models (3+ models, future expansion supported):
    384-dim: BAAI/bge-small-en-v1.5 (MiniLM, CPU-friendly, fast inference)
    768-dim: sentence-transformers/all-mpnet-base-v2 (SBERT, balanced)
    1536-dim: text-embedding-ada-002 (OpenAI, high accuracy)
    Future: Custom fine-tuned models for domain-specific APIs
    
    Each model has:
    - Fixed dimension (384/768/1536)
    - Redis HNSW index namespace
    - Performance characteristics
    - Availability status
    """
    __tablename__ = "embedding_models"
    
    model_id = Column(Text, primary_key=True)  # e.g., "BAAI/bge-small-en-v1.5"
    name = Column(Text, nullable=False)  # Human-readable name
    dimension = Column(Integer, nullable=False)  # 384, 768, or 1536
    provider = Column(Text, nullable=False)  # sentence-transformers, openai, custom
    redis_namespace = Column(Text, nullable=False)  # e.g., "embeddings:384"
    
    # Performance characteristics
    cpu_friendly = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes
    inference_speed = Column(Text, nullable=True)  # fast, medium, slow
    accuracy_level = Column(Text, nullable=True)  # standard, high, very_high
    
    # Availability
    is_active = Column(Integer, nullable=False, default=1)  # 0=disabled, 1=active
    requires_api_key = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes (for OpenAI)
    
    description = Column(Text, nullable=True)  # Use cases, notes
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_embedding_models_dimension', 'dimension'),
        Index('idx_embedding_models_active', 'is_active'),
    )


class Embedding(Base):
    """
    EMBEDDINGS table - Vector embedding metadata for semantic search
    Core fields from diagram: PK=emb_id, FK=u_id, FK=t_id, FK=csv_id, redis_key, created_at
    
    Automatic Embeddings → Redis Vector DB:
    After dataset generation, system automatically embeds rows using user's selected model
    
    Supported Models (see embedding_models table):
    384-dim: BAAI/bge-small-en-v1.5 (MiniLM, CPU-friendly)
    768-dim: sentence-transformers/all-mpnet-base-v2 (SBERT)
    1536-dim: OpenAI text-embedding-ada-002 (High accuracy)
    
    Redis Storage:
    - Key format: embedding:{u_id}:{t_id}:{csv_id}
    - HNSW index per dimension (384/768/1536)
    - Multi-tenant separation by u_id
    
    PostgreSQL stores only metadata (model, dimension, namespace, timestamps)
    """
    __tablename__ = "embeddings"
    
    emb_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    u_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    t_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=True)
    csv_id = Column(UUID(as_uuid=True), ForeignKey("csv_data.csv_id", ondelete="CASCADE"), nullable=True)
    redis_key = Column(Text, nullable=False, unique=True)  # embedding:{u_id}:{t_id}:{csv_id}
    
    # Embedding model tracking
    model_name = Column(Text, nullable=False)  # e.g., "BAAI/bge-small-en-v1.5"
    dimension = Column(Integer, nullable=False)  # Vector dimension: 384, 768, or 1536
    redis_namespace = Column(Text, nullable=False)  # e.g., "embeddings:384" or "embeddings:768"
    
    # Generation tracking
    auto_generated = Column(Integer, nullable=False, default=1)  # 0=manual, 1=auto after dataset generation
    
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="embeddings")
    template = relationship("Template", back_populates="embeddings")
    csv_data = relationship("CSVData", back_populates="embeddings")
    
    # Indexes for multi-tenant queries and dimension-based searches
    __table_args__ = (
        Index('idx_embeddings_user', 'u_id'),
        Index('idx_embeddings_template', 't_id'),
        Index('idx_embeddings_csv', 'csv_id'),
        Index('idx_embeddings_dimension', 'dimension'),  # For HNSW index management
        Index('idx_embeddings_namespace', 'redis_namespace'),  # For namespace queries
        Index('idx_embeddings_model', 'model_name'),  # For model-specific queries
    )


class TestRun(Base):
    """
    TEST_RUNS table - Track test execution runs with Selenium
    
    Stores test execution results including:
    - Test plan JSON
    - Step-by-step results
    - Screenshots captured during execution
    - Pass/fail status
    - Performance metrics
    """
    __tablename__ = "test_runs"
    
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.t_id", ondelete="CASCADE"), nullable=False)
    
    # Test execution details
    template_name = Column(Text, nullable=True)
    intent = Column(Text, nullable=True)  # For analytics grouping
    status = Column(Text, nullable=False, default="running")  # running, passed, failed, error
    
    # Test plan and results
    test_plan = Column(JSONB, nullable=True)  # Full test plan JSON
    step_results = Column(JSONB, nullable=True)  # Array of step results
    
    # Metrics
    total_steps = Column(Integer, nullable=False, default=0)
    passed_steps = Column(Integer, nullable=False, default=0)
    failed_steps = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Numeric, nullable=True)
    
    # Evidence
    screenshots = Column(JSONB, nullable=True)  # Array of screenshot URLs
    error_message = Column(Text, nullable=True)
    
    # Execution metadata
    executed_with_selenium = Column(Integer, nullable=False, default=1)  # 0=mock, 1=real
    headless = Column(Integer, nullable=False, default=1)  # 0=no, 1=yes
    
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_test_runs_user', 'user_id'),
        Index('idx_test_runs_template', 'template_id'),
        Index('idx_test_runs_status', 'status'),
        Index('idx_test_runs_created', 'created_at'),
    )


class AuditLog(Base):
    """
    AUDIT_LOGS table - Track all user actions for security and compliance
    
    Logs include:
    - Template CRUD operations
    - Dataset generation
    - Approval workflow actions
    - Test executions
    - Settings changes
    """
    __tablename__ = "audit_logs"
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.u_id", ondelete="CASCADE"), nullable=False)
    
    # Action details
    action = Column(Text, nullable=False)  # create_template, approve_template, generate_dataset, execute_test, etc.
    resource_type = Column(Text, nullable=False)  # template, dataset, test_run, settings
    resource_id = Column(UUID(as_uuid=True), nullable=True)  # ID of affected resource
    
    # Request context
    ip_address = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(Text, nullable=True)  # API endpoint called
    
    # Change details
    changes = Column(JSONB, nullable=True)  # Before/after values for updates
    metadata_ = Column(JSONB, nullable=True)  # Additional context
    
    # Outcome
    success = Column(Integer, nullable=False, default=1)  # 0=failed, 1=success
    error_message = Column(Text, nullable=True)
    
    created_at = Column(TIMESTAMP, default=utc_now, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_user', 'user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_created', 'created_at'),
    )
