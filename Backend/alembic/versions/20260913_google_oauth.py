"""add google_id to users, make password nullable

A user created via Google sign-in has no local password until they
explicitly set one, and is identified by Google's stable per-account
"sub" claim rather than a password hash.

create_all() (run on every boot by init_db_direct.py) only creates
missing tables -- it does not alter columns on tables that already
exist, so an existing deployment needs this migration to actually pick
up the new column and the relaxed NOT NULL constraint. A fresh database
gets both from the ORM model directly.

Revision ID: 20260913_google_oauth
Revises: 20260823_pgvector_rls
"""

from alembic import op
import sqlalchemy as sa

revision = "20260913_google_oauth"
down_revision = "20260823_pgvector_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # CI runs unit tests on SQLite with a from-scratch create_all()
        # schema, which already matches the ORM model -- nothing to migrate.
        return

    op.add_column("users", sa.Column("google_id", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_users_google_id", "users", ["google_id"])
    op.create_index("ix_users_google_id", "users", ["google_id"])
    op.alter_column("users", "password", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.alter_column("users", "password", existing_type=sa.Text(), nullable=False)
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_constraint("uq_users_google_id", "users", type_="unique")
    op.drop_column("users", "google_id")
