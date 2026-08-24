"""
Model Schemas - Model registry and configuration
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ModelResponse(BaseModel):
    """Response model for model registry"""
    model_id: str = Field(..., description="Unique model identifier")
    type: str = Field(..., description="Model type: 'embedding' or 'llm'")
    name: str = Field(..., description="Human-readable model name")
    dimension: Optional[int] = Field(None, description="Vector dimension (embedding models only)")
    context_tokens: Optional[int] = Field(None, description="Maximum context length")
    cpu_friendly: bool = Field(False, description="Can run efficiently on CPU")
    notes: Optional[str] = Field(None, description="Model description and use cases")
    provider: Optional[str] = Field(None, description="Model provider")
    status: str = Field("active", description="Model status: 'active' or 'deprecated'")
    
    class Config:
        from_attributes = True


class ModelListResponse(BaseModel):
    """Response for listing all models"""
    embedding_models: List[ModelResponse] = Field(default_factory=list)
    llm_models: List[ModelResponse] = Field(default_factory=list)
    total_count: int = Field(..., description="Total number of models")
    default_embedding: Optional[str] = Field(None, description="Default embedding model ID")
    default_llm: Optional[str] = Field(None, description="Default LLM model ID")


class ModelConfigResponse(BaseModel):
    """Response for full model configuration including compatibility matrix"""
    models: List[ModelResponse]
    default_models: Dict[str, str] = Field(
        default_factory=dict,
        description="Default models by type"
    )
    compatibility_matrix: Optional[Dict[str, Any]] = Field(
        None,
        description="Model compatibility information"
    )


class ModelFilterRequest(BaseModel):
    """Request to filter models"""
    type: Optional[str] = Field(None, description="Filter by type: 'embedding' or 'llm'")
    status: Optional[str] = Field(None, description="Filter by status: 'active' or 'deprecated'")
    cpu_friendly: Optional[bool] = Field(None, description="Filter CPU-friendly models")
    min_dimension: Optional[int] = Field(None, description="Minimum vector dimension")
    max_dimension: Optional[int] = Field(None, description="Maximum vector dimension")
