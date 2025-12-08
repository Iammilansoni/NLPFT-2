"""Enterprise Service - Multi-tenant CRUD operations"""

from typing import List, Optional
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, delete

from app.models.database_models import User, Template, Parameter, ExpectedResponse, Metadata, CSVData, Embedding
from app.core.logger import logger


class EnterpriseService:
    """Multi-tenant service with user isolation"""
    
    # Templates
    @staticmethod
    async def create_template(db: AsyncSession, user_id: uuid.UUID, api_name: Optional[str] = None,
                             description: Optional[str] = None, base_url: Optional[str] = None,
                             method: Optional[str] = None) -> Template:
        """Create API template"""
        template = Template(
            t_id=uuid.uuid4(), user_id=user_id, api_name=api_name,
            description=description, base_url=base_url, method=method, created_at=datetime.utcnow()
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        logger.info(f"Created template {template.t_id} for user {user_id}")
        return template
    
    @staticmethod
    async def get_user_templates(db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Template]:
        """Get user templates with pagination"""
        result = await db.execute(
            select(Template).where(Template.user_id == user_id)
            .offset(skip).limit(limit).order_by(Template.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_template_by_id(db: AsyncSession, t_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Template]:
        """Get template with ownership check"""
        result = await db.execute(
            select(Template).where(and_(Template.t_id == t_id, Template.user_id == user_id))
        )
        return result.scalar_one_or_none()
    
    # CSV Data
    @staticmethod
    async def create_csv_data(db: AsyncSession, user_id: uuid.UUID, t_id: uuid.UUID,
                             query: Optional[str] = None, api_name: Optional[str] = None,
                             endpoint: Optional[str] = None, request: Optional[dict] = None,
                             response: Optional[dict] = None, description: Optional[str] = None) -> CSVData:
        """Create CSV data entry"""
        csv_data = CSVData(
            csv_id=uuid.uuid4(), user_id=user_id, t_id=t_id, query=query, api_name=api_name,
            endpoint=endpoint, request=request, response=response, description=description,
            created_at=datetime.utcnow()
        )
        db.add(csv_data)
        await db.commit()
        await db.refresh(csv_data)
        logger.info(f"Created CSV data {csv_data.csv_id} for template {t_id}")
        return csv_data
    
    @staticmethod
    async def get_csv_data_by_template(db: AsyncSession, user_id: uuid.UUID, t_id: uuid.UUID,
                                      skip: int = 0, limit: int = 1000) -> List[CSVData]:
        """Get CSV data with pagination (optimized for millions)"""
        result = await db.execute(
            select(CSVData).where(and_(CSVData.user_id == user_id, CSVData.t_id == t_id))
            .offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def count_csv_data_by_template(db: AsyncSession, user_id: uuid.UUID, t_id: uuid.UUID) -> int:
        """Count CSV data entries"""
        result = await db.execute(
            select(func.count(CSVData.csv_id)).where(and_(CSVData.user_id == user_id, CSVData.t_id == t_id))
        )
        return result.scalar()
    
    # Embeddings
    @staticmethod
    async def create_embedding_metadata(db: AsyncSession, user_id: uuid.UUID, redis_key: str,
                                       t_id: Optional[uuid.UUID] = None, csv_id: Optional[uuid.UUID] = None) -> Embedding:
        """Create embedding metadata (vector in Redis)"""
        embedding = Embedding(
            emb_id=uuid.uuid4(), user_id=user_id, t_id=t_id, csv_id=csv_id,
            redis_key=redis_key, created_at=datetime.utcnow()
        )
        db.add(embedding)
        await db.commit()
        await db.refresh(embedding)
        logger.info(f"Created embedding {embedding.emb_id} with key {redis_key}")
        return embedding
    
    @staticmethod
    async def get_embeddings_by_user(db: AsyncSession, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Embedding]:
        """Get user embeddings with pagination"""
        result = await db.execute(
            select(Embedding).where(Embedding.user_id == user_id)
            .offset(skip).limit(limit).order_by(Embedding.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def delete_embedding_by_redis_key(db: AsyncSession, redis_key: str, user_id: uuid.UUID) -> bool:
        """Delete embedding by Redis key"""
        result = await db.execute(
            delete(Embedding).where(and_(Embedding.redis_key == redis_key, Embedding.user_id == user_id))
        )
        await db.commit()
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted embedding {redis_key}")
        return deleted
    
    @staticmethod
    async def delete_embeddings_by_template(db: AsyncSession, t_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """Delete all embeddings for template"""
        result = await db.execute(
            delete(Embedding).where(and_(Embedding.t_id == t_id, Embedding.user_id == user_id))
        )
        await db.commit()
        count = result.rowcount
        logger.info(f"Deleted {count} embeddings for template {t_id}")
        return count
    
    # Statistics
    @staticmethod
    async def get_user_statistics(db: AsyncSession, user_id: uuid.UUID) -> dict:
        """Get user statistics"""
        templates_count = await db.execute(select(func.count(Template.t_id)).where(Template.user_id == user_id))
        csv_count = await db.execute(select(func.count(CSVData.csv_id)).where(CSVData.user_id == user_id))
        embeddings_count = await db.execute(select(func.count(Embedding.emb_id)).where(Embedding.user_id == user_id))
        
        return {
            "templates": templates_count.scalar(),
            "csv_data": csv_count.scalar(),
            "embeddings": embeddings_count.scalar()
        }


# Singleton
_enterprise_service = EnterpriseService()

def get_enterprise_service() -> EnterpriseService:
    return _enterprise_service
