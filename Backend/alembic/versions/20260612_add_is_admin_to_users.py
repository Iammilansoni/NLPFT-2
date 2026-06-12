"""add is_admin column to users table

Adds an admin role, separate from the 'expert' role:
- expert: can approve/reject templates (domain privilege)
- admin:  can grant roles, rotate encryption keys (system privilege)

SECURITY: required to fix the promote-expert privilege escalation,
where any authenticated user could grant themselves expert status.

Revision ID: 20260612_add_is_admin
Revises: 20260121_llm_provider_config
Create Date: 2026-06-12

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '20260612_add_is_admin'
down_revision = '20260121_llm_provider_config'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_admin column to users table (idempotent)
    # 0 = regular user, 1 = administrator
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='is_admin'
            ) THEN
                ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;
            END IF;
        END $$;
    """)

    # Partial index for fast admin lookups (admins are rare)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin) WHERE is_admin = 1;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_users_is_admin;")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='users' AND column_name='is_admin'
            ) THEN
                ALTER TABLE users DROP COLUMN is_admin;
            END IF;
        END $$;
    """)
