from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.schemas.preferences import (
    GlobalPreferencesResponse,
    GlobalPreferencesUpdate,
    MemberPreferencesResponse,
    MemberPreferencesUpdate,
)
from src.services import preferences_service, member_service

router = APIRouter(prefix="/api/preferences", tags=["preferences"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=GlobalPreferencesResponse)
async def get_global(db: AsyncSession = Depends(get_db)):
    return await preferences_service.get_global_preferences(db)


@router.put("", response_model=GlobalPreferencesResponse)
async def update_global(body: GlobalPreferencesUpdate, db: AsyncSession = Depends(get_db)):
    return await preferences_service.update_global_preferences(db, body)


@router.get("/members/{member_id}", response_model=MemberPreferencesResponse)
async def get_member_prefs(member_id: int, db: AsyncSession = Depends(get_db)):
    member = await member_service.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")
    prefs = await preferences_service.get_member_preferences(db, member_id)
    if not prefs:
        return MemberPreferencesResponse(id=0, member_id=member_id, preferences_jsonb={})
    return prefs


@router.put("/members/{member_id}", response_model=MemberPreferencesResponse)
async def update_member_prefs(member_id: int, body: MemberPreferencesUpdate, db: AsyncSession = Depends(get_db)):
    member = await member_service.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")
    return await preferences_service.upsert_member_preferences(db, member_id, body)
