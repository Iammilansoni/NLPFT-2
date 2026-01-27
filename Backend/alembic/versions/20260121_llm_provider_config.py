"""Add LLM provider config table and user settings extension

Revision ID: 20260121_llm_provider_config
Revises: 20251215_1400_remove_simulate
Create Date: 2026-01-21

This migration adds:
1. llm_provider_configs table for storing LLM provider configurations
2. default_llm_config_id column to user_settings for linking default provider
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '20260121_llm_provider_config'
down_revision = '20251215_1400_remove_simulate'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create llm_provider_configs table
    op.create_table(
        'llm_provider_configs',
        sa.Column('config_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('u_id', UUID(as_uuid=True), sa.ForeignKey('users.u_id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Provider identification
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('is_default', sa.Integer(), server_default=sa.text('0')),
        sa.Column('is_active', sa.Integer(), server_default=sa.text('1')),
        
        # Connection settings
        sa.Column('base_url', sa.Text(), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('model_name', sa.Text(), nullable=False),
        sa.Column('model_type', sa.Text(), server_default=sa.text("'chat'")),
        
        # Generation parameters (JSONB) - use server_default for per-row default
        sa.Column('config_params', JSONB(), server_default=sa.text("'{\"temperature\": 0.7, \"max_tokens\": 4096, \"top_p\": 0.9, \"timeout\": 120.0, \"max_retries\": 3}'::jsonb")),
        
        # Connection test metadata
        sa.Column('last_tested_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_test_success', sa.Integer(), nullable=True),
        sa.Column('last_test_message', sa.Text(), nullable=True),
        sa.Column('last_test_latency_ms', sa.Numeric(10, 2), nullable=True),
        
        # Audit timestamps - server_default only, ORM handles updates
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
    )
    
    # 2. Create indexes for performance
    op.create_index(
        'idx_llm_configs_user_active',
        'llm_provider_configs',
        ['u_id', 'is_active']
    )
    op.create_index(
        'idx_llm_configs_user_default',
        'llm_provider_configs',
        ['u_id', 'is_default']
    )
    
    # 3. Add default_llm_config_id to user_settings
    op.add_column(
        'user_settings',
        sa.Column(
            'default_llm_config_id',
            UUID(as_uuid=True),
            sa.ForeignKey('llm_provider_configs.config_id', ondelete='SET NULL'),
            nullable=True
        )
    )


def downgrade() -> None:
    # 1. Remove default_llm_config_id from user_settings
    op.drop_column('user_settings', 'default_llm_config_id')
    
    # 2. Drop indexes
    op.drop_index('idx_llm_configs_user_default', table_name='llm_provider_configs')
    op.drop_index('idx_llm_configs_user_active', table_name='llm_provider_configs')
    
    # 3. Drop llm_provider_configs table
    op.drop_table('llm_provider_configs')
