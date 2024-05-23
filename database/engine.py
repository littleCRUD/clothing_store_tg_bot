import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from database.models import Base
from database.orm_query import orm_add_banner_description, orm_create_categories
from common.caption_for_db import categories, description_for_info_pages


db_url = f'postgresql+asyncpg://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}'\
    f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'

engine = create_async_engine(db_url, echo=True)

session_maker = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


# Создаем БД
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await orm_create_categories(session, categories)
        await orm_add_banner_description(session, description_for_info_pages)


# Удаляем БД
async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
