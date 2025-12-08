"""add user_settings, datasets tables and update embeddings

Revision ID: 002
Revises: 001
Create Date: 2024-11-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('default_embedding_model', sa.Text(), nullable=True),
        sa.Column('preferred_llm', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    
    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('dataset_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('generated_with_llm', sa.Text(), nullable=True),
        sa.Column('embedded_with_model', sa.Text(), nullable=True),
        sa.Column('embedding_dim', sa.Integer(), nullable=True),
        sa.Column('redis_namespace', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('dataset_id')
    )
    op.create_index('idx_datasets_user', 'datasets', ['user_id'])
    
    # Add new columns to embeddings table
    op.add_column('embeddings', sa.Column('dataset_id', UUID(as_uuid=True), nullable=True))
    op.add_column('embeddings', sa.Column('row_id', sa.Integer(), nullable=True))
    op.add_column('embeddings', sa.Column('model_name', sa.Text(), nullable=True))
    op.add_column('embeddings', sa.Column('dimension', sa.Integer(), nullable=True))
    
    # Add foreign key constraint for dataset_id
    op.create_foreign_key(
        'fk_embeddings_dataset_id',
        'embeddings', 'datasets',
        ['dataset_id'], ['dataset_id']
    )
    
    # Add index for dataset_id
    op.create_index('idx_embeddings_dataset', 'embeddings', ['dataset_id'])

def downgrade() -> None:
    # Drop embeddings indexes and columns
    op.drop_index('idx_embeddings_dataset', table_name='embeddings')
    op.drop_constraint('fk_embeddings_dataset_id', 'embeddings', type_='foreignkey')
    op.drop_column('embeddings', 'dimension')
    op.drop_column('embeddings', 'model_name')
    op.drop_column('embeddings', 'row_id')
    op.drop_column('embeddings', 'dataset_id')
    
    # Drop datasets table
    op.drop_index('idx_datasets_user', table_name='datasets')
    op.drop_table('datasets')
    
    # Drop user_settings table
    op.drop_table('user_settings')
