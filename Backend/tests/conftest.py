"""
Pytest Configuration and Fixtures
==================================
Provides shared test fixtures for:
- Test database setup/teardown
- Async client for API testing
- Mock authentication
- Sample data factories
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.postgres import Base, get_db

# Test database URL (use in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create event loop for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database tables and provide session.
    Drops all tables after test completes.
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Provide session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create test HTTP client with database dependency override.
    """
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    """
    Sample user registration data.
    """
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!",
        "full_name": "Test User",
    }


@pytest.fixture
def sample_template_data() -> dict:
    """
    Sample template creation data.
    """
    return {
        "name": "Login API Test",
        "description": "Test login endpoint with valid/invalid credentials",
        "api_endpoint": "/api/v1/auth/login",
        "http_method": "POST",
        "parameters": [
            {
                "name": "email",
                "parameter_type": "string",
                "is_required": True,
                "description": "User email address",
            },
            {
                "name": "password",
                "parameter_type": "string",
                "is_required": True,
                "description": "User password",
            },
        ],
        "expected_responses": [
            {
                "status_code": 200,
                "response_description": "Successful login with access token",
            },
            {
                "status_code": 401,
                "response_description": "Invalid credentials",
            },
        ],
    }


@pytest.fixture
async def authenticated_user(client: AsyncClient, sample_user_data: dict) -> dict:
    """
    Create user and return authentication token.
    """
    # Register user
    register_response = await client.post("/api/v1/auth/register", json=sample_user_data)
    assert register_response.status_code == 201
    
    # Login to get token
    login_response = await client.post("/api/v1/auth/login", json={
        "email": sample_user_data["email"],
        "password": sample_user_data["password"],
    })
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    return {
        "token": token_data["access_token"],
        "user_id": token_data["user_id"],
        "email": sample_user_data["email"],
    }


@pytest.fixture
def auth_headers(authenticated_user: dict) -> dict:
    """
    Return authorization headers for authenticated requests.
    """
    return {"Authorization": f"Bearer {authenticated_user['token']}"}


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest with custom markers.
    """
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Tests that take >1 second")
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "datasets: Dataset generation tests")
    config.addinivalue_line("markers", "embeddings: Embedding tests")
