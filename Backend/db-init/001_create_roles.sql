-- Runs once, automatically, when Postgres initializes a brand-new data
-- directory (docker-entrypoint-initdb.d convention -- ignored on every boot
-- after the first). It has to exist before alembic/20260823_pgvector_and_rls.py
-- runs: that migration grants an RLS bypass policy to role `nlpforge_admin`
-- (the intended escape hatch for migrations/backups/the seed script) and
-- fails outright with "role nlpforge_admin does not exist" if the role isn't
-- there yet. Nothing else in this stack ever created it.
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nlpforge_admin') THEN
        CREATE ROLE nlpforge_admin;
    END IF;
END
$$;
