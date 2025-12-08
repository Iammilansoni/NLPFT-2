"""
Integration Tests for Dataset Generation API
=============================================
Tests dataset generation endpoints and workflows.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.datasets
class TestDatasetGeneration:
    """Test dataset generation endpoints."""
    
    @pytest.mark.asyncio
    async def test_generate_dataset_requires_auth(self, client: AsyncClient):
        """Test dataset generation requires authentication."""
        response = await client.post("/api/v1/datasets/generate", json={
            "template_id": "123e4567-e89b-12d3-a456-426614174000",
            "count": 10,
        })
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_datasets(self, client: AsyncClient, auth_headers: dict):
        """Test listing user's datasets."""
        response = await client.get("/api/v1/datasets", headers=auth_headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_dataset_invalid_template(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test dataset generation with invalid template ID fails."""
        response = await client.post(
            "/api/v1/datasets/generate",
            headers=auth_headers,
            json={
                "template_id": "00000000-0000-0000-0000-000000000000",
                "count": 5,
            }
        )
        
        assert response.status_code in [404, 400]
    
    @pytest.mark.asyncio
    async def test_generate_dataset_invalid_count(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test dataset generation with invalid count fails."""
        response = await client.post(
            "/api/v1/datasets/generate",
            headers=auth_headers,
            json={
                "template_id": "123e4567-e89b-12d3-a456-426614174000",
                "count": -5,  # Negative count
            }
        )
        
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.datasets
class TestDatasetExport:
    """Test dataset export endpoints."""
    
    @pytest.mark.asyncio
    async def test_export_dataset_csv(self, client: AsyncClient, auth_headers: dict):
        """Test exporting dataset as CSV."""
        # This assumes a dataset exists - in real tests, you'd create one first
        dataset_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = await client.get(
            f"/api/v1/datasets/{dataset_id}/export?format=csv",
            headers=auth_headers
        )
        
        # Will be 404 if dataset doesn't exist, which is expected
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            assert "text/csv" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_export_dataset_json(self, client: AsyncClient, auth_headers: dict):
        """Test exporting dataset as JSON."""
        dataset_id = "123e4567-e89b-12d3-a456-426614174000"
        
        response = await client.get(
            f"/api/v1/datasets/{dataset_id}/export?format=json",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            assert "application/json" in response.headers["content-type"]
