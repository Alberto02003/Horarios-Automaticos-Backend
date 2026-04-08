from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.generation_preference import GenerationPreference
from src.models.member_generation_preference import MemberGenerationPreference
from src.schemas.preferences import GlobalPreferencesUpdate, MemberPreferencesUpdate


async def get_global_preferences(db: AsyncSession) -> GenerationPreference:
    result = await db.execute(select(GenerationPreference))
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = GenerationPreference(general_weekly_hour_limit=40.0)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)
    return prefs


async def update_global_preferences(db: AsyncSession, data: GlobalPreferencesUpdate) -> GenerationPreference:
    prefs = await get_global_preferences(db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    await db.commit()
    await db.refresh(prefs)
    return prefs


async def get_member_preferences(db: AsyncSession, member_id: int) -> MemberGenerationPreference | None:
    result = await db.execute(
        select(MemberGenerationPreference).where(MemberGenerationPreference.member_id == member_id)
    )
    return result.scalar_one_or_none()


async def upsert_member_preferences(
    db: AsyncSession, member_id: int, data: MemberPreferencesUpdate
) -> MemberGenerationPreference:
    prefs = await get_member_preferences(db, member_id)
    if prefs:
        prefs.preferences_jsonb = data.preferences_jsonb
    else:
        prefs = MemberGenerationPreference(member_id=member_id, preferences_jsonb=data.preferences_jsonb)
        db.add(prefs)
    await db.commit()
    await db.refresh(prefs)
    return prefs
