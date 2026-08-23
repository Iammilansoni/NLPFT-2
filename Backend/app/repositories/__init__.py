"""Data-access layer. Routers delegate here instead of embedding SQL."""

from app.repositories.base import BaseRepository
from app.repositories.dataset_repository import DatasetRepository

__all__ = ["BaseRepository", "DatasetRepository"]
