"""add is_expert column to users table

Revision ID: 005_add_is_expert_to_users
Revises: add_email_verification
Create Date: 2025-11-15

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '005_add_is_expert_to_users'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_expert column to users table (if it doesn't exist)
    # 0 = regular user, 1 = expert (can approve templates)
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='is_expert'
            ) THEN
                ALTER TABLE users ADD COLUMN is_expert INTEGER NOT NULL DEFAULT 0;
            END IF;
        END $$;
    """)
    
    # Create index on is_expert for faster expert user queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_is_expert ON users(is_expert) WHERE is_expert = 1;
    """)


def downgrade() -> None:
    # Drop index
    op.execute("DROP INDEX IF EXISTS idx_users_is_expert;")
    
    # Drop column
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='is_expert'
            ) THEN
                ALTER TABLE users DROP COLUMN is_expert;
            END IF;
        END $$;
    """)
