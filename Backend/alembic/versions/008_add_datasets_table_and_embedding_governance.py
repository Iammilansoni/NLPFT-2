"""008_add_datasets_table_and_embedding_governance

Add Dataset model for embedding model governance and update CSVData with dataset_id FK.

🎯 KEY DESIGN: ONE EMBEDDING MODEL PER DATASET
- Once embedded, a dataset is locked to that model
- Re-embedding requires explicit user action
- Enables MODEL_MISMATCH error when search model != dataset model

Revision ID: 008
Revises: 007_add_production_indexes
Create Date: 2024-01-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP


# revision identifiers, used by Alembic.
revision = '008_add_datasets_table'
down_revision = '007_add_production_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create datasets table
    op.create_table(
        'datasets',
        sa.Column('dataset_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('u_id', UUID(as_uuid=True), sa.ForeignKey('users.u_id', ondelete='CASCADE'), nullable=False),
        sa.Column('t_id', UUID(as_uuid=True), sa.ForeignKey('templates.t_id', ondelete='CASCADE'), nullable=False),
        
        # Dataset identification
        sa.Column('name', sa.Text, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('csv_path', sa.Text, nullable=False),
        
        # Embedding model governance - ONE MODEL PER DATASET
        sa.Column('embedding_model', sa.Text, nullable=True),
        sa.Column('embedding_dimension', sa.Integer, nullable=True),
        
        # Embedding status tracking
        sa.Column('embedding_status', sa.Text, nullable=False, server_default='pending'),
        sa.Column('embedding_progress', sa.Integer, nullable=False, server_default='0'),
        sa.Column('embedding_error', sa.Text, nullable=True),
        
        # Row counts
        sa.Column('total_rows', sa.Integer, nullable=False, server_default='0'),
        sa.Column('embedded_rows', sa.Integer, nullable=False, server_default='0'),
        
        # Timestamps
        sa.Column('created_at', TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('embedding_started_at', TIMESTAMP, nullable=True),
        sa.Column('embedding_completed_at', TIMESTAMP, nullable=True),
        sa.Column('updated_at', TIMESTAMP, nullable=True, onupdate=sa.func.now()),
        
        # Generation metadata
        sa.Column('generated_with_llm', sa.Text, nullable=True),
        sa.Column('generation_prompt', sa.Text, nullable=True),
        sa.Column('scenario_distribution', JSONB, nullable=True),
        
        # Celery task tracking
        sa.Column('celery_task_id', sa.Text, nullable=True),
    )
    
    # 2. Add indexes for datasets table
    op.create_index('idx_datasets_user', 'datasets', ['u_id'])
    op.create_index('idx_datasets_template', 'datasets', ['t_id'])
    op.create_index('idx_datasets_embedding_model', 'datasets', ['embedding_model'])
    op.create_index('idx_datasets_embedding_status', 'datasets', ['embedding_status'])
    op.create_index('idx_datasets_created_at', 'datasets', ['created_at'])
    
    # 3. Add dataset_id column to csv_data table
    op.add_column('csv_data', 
        sa.Column('dataset_id', UUID(as_uuid=True), sa.ForeignKey('datasets.dataset_id', ondelete='CASCADE'), nullable=True)
    )
    
    # 4. Add is_embedded and embedding_error columns to csv_data
    op.add_column('csv_data',
        sa.Column('is_embedded', sa.Integer, nullable=False, server_default='0')
    )
    op.add_column('csv_data',
        sa.Column('embedding_error', sa.Text, nullable=True)
    )
    
    # 5. Add indexes for csv_data improvements
    op.create_index('idx_csv_data_dataset', 'csv_data', ['dataset_id'])
    op.create_index('idx_csv_data_is_embedded', 'csv_data', ['is_embedded'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_csv_data_is_embedded', 'csv_data')
    op.drop_index('idx_csv_data_dataset', 'csv_data')
    
    # Drop columns from csv_data
    op.drop_column('csv_data', 'embedding_error')
    op.drop_column('csv_data', 'is_embedded')
    op.drop_column('csv_data', 'dataset_id')
    
    # Drop datasets indexes
    op.drop_index('idx_datasets_created_at', 'datasets')
    op.drop_index('idx_datasets_embedding_status', 'datasets')
    op.drop_index('idx_datasets_embedding_model', 'datasets')
    op.drop_index('idx_datasets_template', 'datasets')
    op.drop_index('idx_datasets_user', 'datasets')
    
    # Drop datasets table
    op.drop_table('datasets')
