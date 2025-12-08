"""add_models_table_and_csv_tracking

Revision ID: 004
Revises: 003
Create Date: 2024-11-14 00:00:00.000000

Phase 1: Multi-Model System
- Creates models table for model registry
- Adds tracking fields to csv_data (generated_with_llm, embedded_with_model, etc.)
- Seeds models from config/models.json (single source of truth)
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import json
from pathlib import Path

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def load_models_from_config():
    """Load model specifications from config/models.json"""
    config_path = Path(__file__).parent.parent.parent / 'config' / 'models.json'
    
    if not config_path.exists():
        print(f"Warning: Config file not found at {config_path}")
        return []
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    models = []
    
    # Process embedding models
    for model in config.get('embedding_models', []):
        models.append({
            'model_id': model['model_id'],
            'type': 'embedding',
            'name': model['name'],
            'dimension': model['dimension'],
            'context_tokens': model['context_tokens'],
            'cpu_friendly': model['cpu_friendly'],
            'notes': model.get('notes', ''),
            'provider': model['provider'],
            'status': 'active'
        })
    
    # Process LLM models
    for model in config.get('llm_models', []):
        models.append({
            'model_id': model['model_id'],
            'type': 'llm',
            'name': model['name'],
            'dimension': None,  # LLMs don't have vector dimensions
            'context_tokens': model['context_tokens'],
            'cpu_friendly': not model.get('api_required', True),  # Local = CPU-friendly
            'notes': model.get('notes', ''),
            'provider': model['provider'],
            'status': 'active'
        })
    
    print(f"✅ Loaded {len(models)} models from config file")
    return models


def upgrade() -> None:
    """Create models table and add csv_data tracking fields"""
    
    # 1. Create models table
    op.create_table(
        'models',
        sa.Column('model_id', sa.String(100), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('dimension', sa.Integer, nullable=True),
        sa.Column('context_tokens', sa.Integer, nullable=False),
        sa.Column('cpu_friendly', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    )
    
    # 2. Create indexes for models table
    op.create_index('idx_models_type', 'models', ['type'])
    op.create_index('idx_models_status', 'models', ['status'])
    
    # 3. Add tracking fields to csv_data
    op.add_column('csv_data', sa.Column('generated_with_llm', sa.String(100), nullable=True))
    op.add_column('csv_data', sa.Column('embedded_with_model', sa.String(100), nullable=True))
    op.add_column('csv_data', sa.Column('embedding_dim', sa.Integer, nullable=True))
    op.add_column('csv_data', sa.Column('redis_namespace', sa.String(100), nullable=True))
    
    # 4. Create index for csv_data tracking
    op.create_index('idx_csv_embedded_model', 'csv_data', ['embedded_with_model'])
    
    # 5. Seed models from config file (single source of truth)
    models = load_models_from_config()
    
    if models:
        # Use bulk insert for efficiency
        from sqlalchemy import table, column
        models_table = table('models',
            column('model_id', sa.String),
            column('type', sa.String),
            column('name', sa.String),
            column('dimension', sa.Integer),
            column('context_tokens', sa.Integer),
            column('cpu_friendly', sa.Boolean),
            column('notes', sa.Text),
            column('provider', sa.String),
            column('status', sa.String),
            column('created_at', sa.TIMESTAMP)
        )
        
        # Add created_at timestamp to each model
        for model in models:
            model['created_at'] = datetime.utcnow()
        
        op.bulk_insert(models_table, models)
        print(f"✅ Seeded {len(models)} models from config/models.json")
    else:
        print("⚠️  No models loaded from config file - skipping seed")


def downgrade() -> None:
    """Rollback changes"""
    
    # 1. Remove csv_data tracking fields
    op.drop_index('idx_csv_embedded_model', table_name='csv_data')
    op.drop_column('csv_data', 'redis_namespace')
    op.drop_column('csv_data', 'embedding_dim')
    op.drop_column('csv_data', 'embedded_with_model')
    op.drop_column('csv_data', 'generated_with_llm')
    
    # 2. Drop models table (cascade will delete all rows)
    op.drop_index('idx_models_status', table_name='models')
    op.drop_index('idx_models_type', table_name='models')
    op.drop_table('models')
    
    print("✅ Rolled back models table and csv_data tracking fields")
