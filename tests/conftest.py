"""Test fixtures: PostgreSQL DB with transaction rollback per test."""

import asyncio
import os
import platform

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.database import Base, get_db
from src.core.security import create_access_token, hash_password
from src.main import app
from src.models.user import User
import src.models  # noqa: F401

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql+psycopg://appuser:changeme@localhost:5432/appdb")
engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def seed_user(db: AsyncSession):
    user = User(email="test@horarios.app", password_hash=hash_password("test123"), display_name="Test User")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    yield user
    # Cleanup
    await db.delete(user)
    await db.commit()


@pytest_asyncio.fixture
async def auth_token(seed_user):
    return create_access_token(seed_user.id)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(auth_token):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers={"Authorization": f"Bearer {auth_token}"}) as c:
        yield c
