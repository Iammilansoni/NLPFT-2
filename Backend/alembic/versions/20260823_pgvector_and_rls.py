"""pgvector storage + Row-Level Security multi-tenancy

Phase 3 of the v2 semantic-router refactor.

Moves vector storage from Redis into PostgreSQL and enforces tenant isolation at
the storage layer instead of in application code.

WHAT THIS CREATES
-----------------
  * the `vector` extension
  * `vector_rows` -- one row per indexed utterance, with its embedding inline
  * a PARTIAL HNSW index per supported dimension (see note below)
  * RLS policies on every tenant-owned table, both ENABLED and FORCED

WHY ONE PARTIAL INDEX PER DIMENSION
-----------------------------------
pgvector's `vector` type is dimension-parameterised, and an HNSW index can only
be built over a fixed dimension. v1's multi-model design (384 / 768 / 1536) is
worth preserving, so rather than one table per model we keep one table with a
`dimension` discriminator and build a partial HNSW index per dimension:

    CREATE INDEX ... ON vector_rows USING hnsw ((embedding::vector(384)) ...)
        WHERE dimension = 384

Queries must filter on `dimension` to hit the right index -- `PgVectorStore`
always does.

RLS: ENABLE IS NOT ENOUGH
-------------------------
`ENABLE ROW LEVEL SECURITY` is ignored for the role that OWNS the table, and
applications routinely connect as the owner. Every table below therefore gets
`FORCE ROW LEVEL SECURITY` too. Without it this migration produces tenancy that
silently does nothing.

Policies read `current_setting('app.tenant_id', true)`. The `true` makes a
missing setting return NULL rather than raising, so a session that forgot to
bind a tenant sees ZERO rows instead of erroring -- fail closed, not open.

Revision ID: 20260823_pgvector_rls
Revises: 20260612_add_is_admin
"""

from alembic import op
import sqlalchemy as sa

revision = "20260823_pgvector_rls"
down_revision = "20260612_add_is_admin"
branch_labels = None
depends_on = None


# Tenant-owned tables and the column holding the owning user id.
TENANT_TABLES = [
    ("templates", "u_id"),
    ("datasets", "u_id"),
    ("embeddings", "u_id"),
    ("csv_data", "u_id"),
    ("vector_rows", "u_id"),
]

SUPPORTED_DIMENSIONS = [384, 768, 1536]


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # CI runs on SQLite; nothing here is meaningful there.
        return

    # -- extension ---------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # -- vector_rows -------------------------------------------------------
    op.create_table(
        "vector_rows",
        sa.Column(
            "row_uid",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("u_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("t_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dataset_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        # The indexed utterance -- this is the cross-encoder's passage text.
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("api_name", sa.Text(), nullable=True),
        sa.Column("endpoint", sa.Text(), nullable=True),
        sa.Column("method", sa.Text(), nullable=True),
        sa.Column("scenario_type", sa.Text(), nullable=True, server_default="valid"),
        sa.Column("test_category", sa.Text(), nullable=True),
        sa.Column("intent_type", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Model governance carried over from v1 -- a vector is meaningless
        # without knowing which model produced it.
        sa.Column("embedding_model", sa.Text(), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),  # replaced below
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["u_id"], ["users.u_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["t_id"], ["templates.t_id"], ondelete="CASCADE"),
    )

    # `vector` has no SQLAlchemy type without the pgvector package, so the column
    # is created as text and retyped here. Keeps the migration dependency-free.
    op.execute("ALTER TABLE vector_rows ALTER COLUMN embedding TYPE vector USING embedding::vector")

    # -- btree indexes -----------------------------------------------------
    op.create_index("idx_vector_rows_tenant", "vector_rows", ["u_id"])
    op.create_index("idx_vector_rows_template", "vector_rows", ["t_id"])
    op.create_index("idx_vector_rows_dataset", "vector_rows", ["dataset_id"])
    op.create_index(
        "idx_vector_rows_model_dim", "vector_rows", ["embedding_model", "dimension"]
    )

    # -- HNSW, one partial index per dimension -----------------------------
    # m=16 / ef_construction=200 match the v1 Redis parameters so the pgvector
    # vs Redis benchmark compares like with like.
    for dim in SUPPORTED_DIMENSIONS:
        op.execute(
            f"""
            CREATE INDEX idx_vector_rows_hnsw_{dim}
                ON vector_rows
                USING hnsw ((embedding::vector({dim})) vector_cosine_ops)
                WITH (m = 16, ef_construction = 200)
                WHERE dimension = {dim}
            """
        )

    # -- Row-Level Security ------------------------------------------------
    for table, col in TENANT_TABLES:
        if not _table_exists(bind, table):
            continue

        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        # Without FORCE, the owning role bypasses every policy below.
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
                USING ({col}::text = current_setting('app.tenant_id', true))
                WITH CHECK ({col}::text = current_setting('app.tenant_id', true))
            """
        )

        # Maintenance escape hatch: migrations, backups and the seed script run
        # as a role holding BYPASSRLS or `nlpforge_admin`, not as the app role.
        op.execute(f"DROP POLICY IF EXISTS admin_full_access ON {table}")
        op.execute(
            f"""
            CREATE POLICY admin_full_access ON {table}
                TO nlpforge_admin
                USING (true) WITH CHECK (true)
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table, _col in TENANT_TABLES:
        if not _table_exists(bind, table):
            continue
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"DROP POLICY IF EXISTS admin_full_access ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    for dim in SUPPORTED_DIMENSIONS:
        op.execute(f"DROP INDEX IF EXISTS idx_vector_rows_hnsw_{dim}")
    op.drop_table("vector_rows")
    # The extension is left in place: other objects may depend on it.


def _table_exists(bind, name: str) -> bool:
    return bool(
        bind.execute(
            sa.text("SELECT to_regclass(:n) IS NOT NULL"), {"n": f"public.{name}"}
        ).scalar()
    )
