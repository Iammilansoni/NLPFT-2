"""per-user embedding models: record the provider next to every embedding model

Vectors are only comparable within one (provider, model, dimension). Until now
the embedding model was fixed per deployment, so rows recorded only the model
name. With per-user models, datasets, vector rows and user settings also record
which provider produced them.

Existing rows were embedded by the deployment default of their time: Ollama
models are bare names ("nomic-embed-text"), in-process ONNX models are Hugging
Face ids ("BAAI/bge-small-en-v1.5"). The backfill uses that distinction.

Also drops the retired registries (`models`, `embedding_models`, `embeddings`).

Idempotent, like the other post-create_all migrations: a fresh database already
has the ORM-declared columns before this runs.

Revision ID: 20260925_embedding_provider
Revises: 20260924_model_catalog
"""

import sqlalchemy as sa
from alembic import op

revision = "20260925_embedding_provider"
down_revision = "20260924_model_catalog"
branch_labels = None
depends_on = None

BACKFILL = "CASE WHEN embedding_model LIKE '%/%' THEN 'builtin' ELSE 'ollama' END"


def _columns(bind, table):
    return {c["name"] for c in sa.inspect(bind).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table in ("datasets", "vector_rows"):
        if "embedding_provider" not in _columns(bind, table):
            op.add_column(table, sa.Column("embedding_provider", sa.Text(), nullable=True))
        op.execute(
            f"UPDATE {table} SET embedding_provider = {BACKFILL} "
            "WHERE embedding_provider IS NULL AND embedding_model IS NOT NULL"
        )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vector_rows_provider_model_dim "
        "ON vector_rows (u_id, embedding_provider, embedding_model, dimension)"
    )

    if "embedding_provider" not in _columns(bind, "user_settings"):
        op.add_column("user_settings", sa.Column("embedding_provider", sa.Text(), nullable=True))
    # NULL provider now means "use the deployment default"; the old NOT NULL
    # defaults ("nomic-embed-text", 768) were that default written out by hand.
    op.alter_column("user_settings", "default_embedding_model", existing_type=sa.Text(), nullable=True, server_default=None)
    op.alter_column("user_settings", "embedding_dimension", existing_type=sa.Integer(), nullable=True, server_default=None)

    # Retired registries: `models` / `embedding_models` held hand-written model
    # lists (replaced by model_catalog), `embeddings` held Redis vector keys
    # (replaced by vector_rows). Nothing reads them any more.
    for table in ("embeddings", "embedding_models", "models"):
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")


def downgrade() -> None:
    # The dropped legacy tables are not recreated: their contents were
    # hand-maintained lists and Redis keys that no longer mean anything.
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS idx_vector_rows_provider_model_dim")
    for table in ("datasets", "vector_rows", "user_settings"):
        op.drop_column(table, "embedding_provider")
