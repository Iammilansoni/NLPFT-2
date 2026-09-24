"""model catalogue: live provider model listings and their sync health

Replaces hand-maintained model lists with what each provider reports serving.
See ModelCatalogEntry / ModelCatalogSource in app/models/database_models.py.

A fresh database gets both tables from create_all() before migrations run, so
every step is conditional (same pattern as 20260913_google_oauth).

Revision ID: 20260924_model_catalog
Revises: 20260913_google_oauth
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260924_model_catalog"
down_revision = "20260913_google_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    tables = set(sa.inspect(bind).get_table_names())

    if "model_catalog" not in tables:
        op.create_table(
            "model_catalog",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("scope", sa.Text(), nullable=False),
            sa.Column("provider", sa.Text(), nullable=False),
            sa.Column("model_id", sa.Text(), nullable=False),
            sa.Column("kind", sa.Text(), nullable=False),
            sa.Column("display_name", sa.Text(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("context_tokens", sa.Integer(), nullable=True),
            sa.Column("dimension", sa.Integer(), nullable=True),
            sa.Column("is_local", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("is_free", sa.Boolean(), nullable=True),
            sa.Column("status", sa.Text(), nullable=False, server_default="active"),
            sa.Column("status_reason", sa.Text(), nullable=True),
            sa.Column("shutdown_date", sa.Date(), nullable=True),
            sa.Column("first_seen_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
            sa.Column("last_seen_at", sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
            sa.Column("missing_since", sa.TIMESTAMP(), nullable=True),
            sa.Column("retired_at", sa.TIMESTAMP(), nullable=True),
            sa.Column("extra", postgresql.JSONB(), nullable=True),
            sa.UniqueConstraint("scope", "provider", "model_id", name="uq_model_catalog_scope_provider_model"),
        )
        op.create_index("idx_model_catalog_kind_status", "model_catalog", ["kind", "status"])

    if "model_catalog_sources" not in tables:
        op.create_table(
            "model_catalog_sources",
            sa.Column("scope", sa.Text(), primary_key=True),
            sa.Column("provider", sa.Text(), primary_key=True),
            sa.Column("first_success_at", sa.TIMESTAMP(), nullable=True),
            sa.Column("last_attempt_at", sa.TIMESTAMP(), nullable=True),
            sa.Column("last_success_at", sa.TIMESTAMP(), nullable=True),
            sa.Column("last_error", sa.Text(), nullable=True),
            sa.Column("last_error_code", sa.Text(), nullable=True),
            sa.Column("model_count", sa.Integer(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.drop_table("model_catalog_sources")
    op.drop_index("idx_model_catalog_kind_status", table_name="model_catalog")
    op.drop_table("model_catalog")
