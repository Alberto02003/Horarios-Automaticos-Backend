"""Seed script: creates default user, shift types, and generation preferences."""

import asyncio
import platform
from datetime import time

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.models.user import User
from src.models.shift_type import ShiftType
from src.models.generation_preference import GenerationPreference


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

SHIFT_TYPES = [
    {"code": "M", "name": "Manana", "category": "work", "default_start_time": time(7, 0), "default_end_time": time(15, 0), "color": "#3B82F6"},
    {"code": "T", "name": "Tarde", "category": "work", "default_start_time": time(15, 0), "default_end_time": time(23, 0), "color": "#F59E0B"},
    {"code": "N", "name": "Noche", "category": "work", "default_start_time": time(23, 0), "default_end_time": time(7, 0), "color": "#6366F1"},
    {"code": "D", "name": "Descanso", "category": "special", "default_start_time": None, "default_end_time": None, "counts_as_work_time": False, "color": "#10B981"},
    {"code": "V", "name": "Vacaciones", "category": "vacation", "default_start_time": None, "default_end_time": None, "counts_as_work_time": False, "color": "#EF4444"},
    {"code": "L", "name": "Libre", "category": "special", "default_start_time": None, "default_end_time": None, "counts_as_work_time": False, "color": "#9CA3AF"},
]


async def seed(session: AsyncSession) -> None:
    # User
    result = await session.execute(select(User).where(User.email == "jeny@horarios.app"))
    if not result.scalar_one_or_none():
        session.add(User(
            email="jeny@horarios.app",
            password_hash=hash_password("admin123"),
            display_name="Jeny",
        ))
        print("Created user: jeny@horarios.app / admin123")

    # Shift types
    for st in SHIFT_TYPES:
        result = await session.execute(select(ShiftType).where(ShiftType.code == st["code"]))
        if not result.scalar_one_or_none():
            session.add(ShiftType(**st))
            print(f"Created shift type: {st['code']} - {st['name']}")

    # Generation preferences (singleton)
    result = await session.execute(select(GenerationPreference))
    if not result.scalar_one_or_none():
        session.add(GenerationPreference(general_weekly_hour_limit=40.0))
        print("Created default generation preferences (40h/week)")

    await session.commit()
    print("Seed complete.")


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
