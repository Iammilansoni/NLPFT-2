"""
Model catalogue lifecycle, against a real PostgreSQL.

Provider listings are faked; everything else (upserts, lifecycle, scoping,
dependent checks) runs through the real service and schema.

DESTRUCTIVE: a full sync retires every catalogue row it did not list, and each
test empties the catalogue tables. Runs only when ALLOW_DESTRUCTIVE_DB_TESTS
names the database the app is actually connected to (CI: its throwaway
"nlpforge"). Naming it, not just setting a flag, matters: DATABASE_URL
overrides POSTGRES_DB, so a flag alone once let this run against a dev database.
"""

import os
import uuid
from datetime import date, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.postgres import AsyncSessionLocal, engine
from app.llm.model_discovery import DiscoveredModel, DiscoveryError
from app.models.database_models import LLMProviderConfig, ModelCatalogEntry, ModelCatalogSource, User, utc_now
from app.services import model_catalog_service as catalog
from app.services.model_catalog_service import GLOBAL_SCOPE, Credential

requires_scratch_db = pytest.mark.skipif(
    engine.url.get_backend_name() != "postgresql"
    or engine.url.database != os.getenv("ALLOW_DESTRUCTIVE_DB_TESTS"),
    reason=f"set ALLOW_DESTRUCTIVE_DB_TESTS to the scratch database's name (connected to: {engine.url.database})",
)
pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
@requires_scratch_db
@pytest.mark.asyncio
async def test_db():
    created_users = []
    async with AsyncSessionLocal() as db:
        await db.execute(delete(ModelCatalogEntry))
        await db.execute(delete(ModelCatalogSource))
        await db.commit()
        db.info["created_users"] = created_users
        yield db
        await db.rollback()
        if created_users:
            await db.execute(delete(LLMProviderConfig).where(LLMProviderConfig.u_id.in_(created_users)))
            await db.execute(delete(User).where(User.u_id.in_(created_users)))
        await db.execute(delete(ModelCatalogEntry))
        await db.execute(delete(ModelCatalogSource))
        await db.commit()
    await engine.dispose()


def llm(model_id, **kw):
    return DiscoveredModel(model_id=model_id, kind="llm", display_name=model_id, **kw)


class FakeProviders:
    """Stands in for model_discovery: listings keyed by (provider, api_key)."""

    def __init__(self):
        self.listings = {}

    def set(self, provider, models, api_key=None):
        self.listings[(provider, api_key)] = models

    async def discover(self, provider, api_key=None, base_url=None):
        result = self.listings.get((provider, api_key))
        if isinstance(result, Exception):
            raise result
        if result is None:
            raise DiscoveryError(f"{provider} unreachable", "UNREACHABLE")
        return list(result)


@pytest.fixture
def providers(monkeypatch):
    fake = FakeProviders()
    monkeypatch.setattr(catalog, "discover_models", fake.discover)
    monkeypatch.setattr(catalog, "deployment_credentials", lambda: [Credential(GLOBAL_SCOPE, "ollama", None, None)])

    async def no_probe(*_args, **_kwargs):
        return None

    monkeypatch.setattr(catalog, "probe_dimension", no_probe)
    return fake


async def rows(db, **filters):
    query = select(ModelCatalogEntry)
    for key, value in filters.items():
        query = query.where(getattr(ModelCatalogEntry, key) == value)
    return {r.model_id: r for r in (await db.execute(query)).scalars()}


async def age_retirements(db):
    for row in (await rows(db, status="retired")).values():
        row.retired_at = utc_now() - catalog.RETIRED_RETENTION - timedelta(minutes=1)
    await db.commit()


async def make_user(db):
    user = User(u_id=uuid.uuid4(), email=f"{uuid.uuid4().hex}@example.com", password="x")
    db.add(user)
    await db.commit()
    db.info["created_users"].append(user.u_id)
    return user


@requires_scratch_db
@pytest.mark.asyncio
async def test_first_sync_lists_models_without_new_badges(test_db, providers):
    providers.set("ollama", [llm("llama3.2:3b"), DiscoveredModel("nomic-embed-text", "embedding", "nomic", dimension=768)])

    [result] = await catalog.sync_catalog(test_db)

    assert result.ok and result.added == 2
    stored = await rows(test_db)
    assert stored["nomic-embed-text"].dimension == 768
    source = await test_db.get(ModelCatalogSource, (GLOBAL_SCOPE, "ollama"))
    assert source.model_count == 2 and source.last_error is None
    user = await make_user(test_db)
    assert not any(m["is_new"] for m in await catalog.list_catalog(test_db, user.u_id))


@requires_scratch_db
@pytest.mark.asyncio
async def test_missing_model_is_deprecated_then_restored(test_db, providers):
    providers.set("ollama", [llm("a"), llm("b")])
    await catalog.sync_catalog(test_db)

    providers.set("ollama", [llm("a")])
    [result] = await catalog.sync_catalog(test_db)
    assert result.deprecated == 1
    b = (await rows(test_db))["b"]
    assert b.status == "deprecated" and "stopped listing" in b.status_reason

    providers.set("ollama", [llm("a"), llm("b")])
    await catalog.sync_catalog(test_db)
    b = (await rows(test_db))["b"]
    assert b.status == "active" and b.missing_since is None and b.status_reason is None


@requires_scratch_db
@pytest.mark.asyncio
async def test_outage_changes_nothing(test_db, providers):
    providers.set("ollama", [llm("a")])
    await catalog.sync_catalog(test_db)

    providers.set("ollama", DiscoveryError("Couldn't reach Ollama", "UNREACHABLE"))
    [result] = await catalog.sync_catalog(test_db)

    assert not result.ok
    assert (await rows(test_db))["a"].status == "active"
    source = await test_db.get(ModelCatalogSource, (GLOBAL_SCOPE, "ollama"))
    assert source.last_error == "Couldn't reach Ollama" and source.last_error_code == "UNREACHABLE"


@requires_scratch_db
@pytest.mark.asyncio
async def test_partial_failure_skips_deprecation(test_db, providers, monkeypatch):
    user = await make_user(test_db)
    for key in ("key-1", "key-2"):
        test_db.add(LLMProviderConfig(u_id=user.u_id, name=key, provider="groq", model_name="m", api_key_encrypted=key))
    await test_db.commit()
    monkeypatch.setattr(catalog, "decrypt_api_key", lambda enc: enc)

    providers.set("groq", [llm("m"), llm("only-on-key-2")], api_key="key-2")
    providers.set("groq", [llm("m")], api_key="key-1")
    await catalog.sync_catalog(test_db, user_id=user.u_id, include_global=False)

    providers.set("groq", DiscoveryError("rate limited", "RATE_LIMITED"), api_key="key-2")
    [result] = await catalog.sync_catalog(test_db, user_id=user.u_id, include_global=False)

    assert result.ok and result.deprecated == 0
    assert (await rows(test_db))["only-on-key-2"].status == "active"


@requires_scratch_db
@pytest.mark.asyncio
async def test_retired_after_grace_and_deleted_only_when_unused(test_db, providers):
    user = await make_user(test_db)
    providers.set("ollama", [llm("keep"), llm("used"), llm("unused")])
    await catalog.sync_catalog(test_db)
    test_db.add(LLMProviderConfig(u_id=user.u_id, name="c", provider="ollama", model_name="used"))
    await test_db.commit()

    providers.set("ollama", [llm("keep")])
    await catalog.sync_catalog(test_db)  # -> deprecated
    for row in (await rows(test_db)).values():
        if row.missing_since:
            row.missing_since = utc_now() - catalog.RETIRE_GRACE - timedelta(minutes=1)
    await test_db.commit()

    [result] = await catalog.sync_catalog(test_db)
    assert result.retired == 2 and result.deleted == 0  # retired rows stay visible for the retention period
    visible = {m["model_id"] for m in await catalog.list_catalog(test_db, user.u_id)}
    assert visible == {"keep"}

    await age_retirements(test_db)
    [result] = await catalog.sync_catalog(test_db)

    assert result.deleted == 1
    stored = await rows(test_db)
    assert "unused" not in stored
    assert stored["used"].status == "retired"


@requires_scratch_db
@pytest.mark.asyncio
async def test_announced_shutdown_retires(test_db, providers):
    providers.set("ollama", [llm("sunset", shutdown_date=date.today() - timedelta(days=1)), llm("later", shutdown_date=date.today() + timedelta(days=30))])
    await catalog.sync_catalog(test_db)
    stored = await rows(test_db)
    assert stored["sunset"].status == "retired" and "shuts down" in stored["sunset"].status_reason
    assert stored["later"].status == "active"


@requires_scratch_db
@pytest.mark.asyncio
async def test_models_found_with_a_users_key_stay_private(test_db, providers, monkeypatch):
    alice, bob = await make_user(test_db), await make_user(test_db)
    test_db.add(LLMProviderConfig(u_id=alice.u_id, name="g", provider="google", model_name="gemini", api_key_encrypted="enc"))
    await test_db.commit()
    monkeypatch.setattr(catalog, "decrypt_api_key", lambda enc: "alice-key")
    providers.set("ollama", [llm("shared")])
    providers.set("google", [llm("gemini"), llm("alice-fine-tune")], api_key="alice-key")

    await catalog.sync_catalog(test_db)

    alice_sees = {m["model_id"] for m in await catalog.list_catalog(test_db, alice.u_id)}
    bob_sees = {m["model_id"] for m in await catalog.list_catalog(test_db, bob.u_id)}
    assert alice_sees == {"shared", "gemini", "alice-fine-tune"}
    assert bob_sees == {"shared"}


@requires_scratch_db
@pytest.mark.asyncio
async def test_deleted_connection_retires_its_models(test_db, providers, monkeypatch):
    user = await make_user(test_db)
    config = LLMProviderConfig(u_id=user.u_id, name="g", provider="groq", model_name="other", api_key_encrypted="enc")
    test_db.add(config)
    await test_db.commit()
    monkeypatch.setattr(catalog, "decrypt_api_key", lambda enc: "k")
    providers.set("groq", [llm("llama-70b")], api_key="k")
    await catalog.sync_catalog(test_db, user_id=user.u_id, include_global=False)
    assert "llama-70b" in await rows(test_db, scope=str(user.u_id))

    await test_db.delete(config)
    await test_db.commit()
    await catalog.sync_catalog(test_db, user_id=user.u_id, include_global=False)
    assert (await rows(test_db, scope=str(user.u_id)))["llama-70b"].status == "retired"

    await age_retirements(test_db)
    await catalog.sync_catalog(test_db, user_id=user.u_id, include_global=False)
    assert await rows(test_db, scope=str(user.u_id)) == {}
    assert await test_db.get(ModelCatalogSource, (str(user.u_id), "groq")) is None


@requires_scratch_db
@pytest.mark.asyncio
async def test_new_badge_only_for_later_arrivals(test_db, providers):
    providers.set("ollama", [llm("old")])
    await catalog.sync_catalog(test_db)
    source = await test_db.get(ModelCatalogSource, (GLOBAL_SCOPE, "ollama"))
    source.first_success_at = utc_now() - timedelta(days=1)
    for row in (await rows(test_db)).values():
        row.first_seen_at = source.first_success_at
    await test_db.commit()

    providers.set("ollama", [llm("old"), llm("fresh")])
    await catalog.sync_catalog(test_db)
    user = await make_user(test_db)
    badges = {m["model_id"]: m["is_new"] for m in await catalog.list_catalog(test_db, user.u_id)}
    assert badges == {"old": False, "fresh": True}

