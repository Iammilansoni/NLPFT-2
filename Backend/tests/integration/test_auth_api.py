"""
Integration Tests for Authentication API
=========================================
Tests user registration, login, and authentication flows.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.auth
class TestUserRegistration:
    """Test user registration endpoints."""
    
    @pytest.mark.asyncio
    async def test_register_new_user(self, client: AsyncClient, sample_user_data: dict):
        """Test successful user registration."""
        response = await client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with duplicate email fails."""
        # Register first user
        await client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Try to register again with same email
        response = await client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with invalid email fails."""
        sample_user_data["email"] = "invalid-email"
        
        response = await client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient, sample_user_data: dict):
        """Test registration with weak password fails."""
        sample_user_data["password"] = "weak"
        
        response = await client.post("/api/v1/auth/register", json=sample_user_data)
        
        assert response.status_code in [400, 422]


@pytest.mark.integration
@pytest.mark.auth
class TestUserLogin:
    """Test user login endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, sample_user_data: dict):
        """Test successful login returns access token."""
        # Register user first
        await client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Login
        response = await client.post("/api/v1/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"],
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, sample_user_data: dict):
        """Test login with wrong password fails."""
        # Register user first
        await client.post("/api/v1/auth/register", json=sample_user_data)
        
        # Try to login with wrong password
        response = await client.post("/api/v1/auth/login", json={
            "email": sample_user_data["email"],
            "password": "WrongPassword123!",
        })
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        })
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login without credentials fails."""
        response = await client.post("/api/v1/auth/login", json={})
        
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.auth
class TestProtectedEndpoints:
    """Test authentication-protected endpoints."""
    
    @pytest.mark.asyncio
    async def test_access_protected_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token fails."""
        response = await client.get("/api/v1/templates")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_access_protected_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token fails."""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = await client.get("/api/v1/templates", headers=headers)
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_access_protected_with_valid_token(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test accessing protected endpoint with valid token succeeds."""
        response = await client.get("/api/v1/templates", headers=auth_headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
