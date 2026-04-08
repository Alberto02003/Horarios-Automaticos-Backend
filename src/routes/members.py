from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.models.user import User
from src.schemas.member import MemberCreate, MemberResponse, MemberUpdate
from src.services import member_service

router = APIRouter(prefix="/api/members", tags=["members"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[MemberResponse])
async def list_members(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    return await member_service.list_members(db, include_inactive)


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(member_id: int, db: AsyncSession = Depends(get_db)):
    member = await member_service.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")
    return member


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(body: MemberCreate, db: AsyncSession = Depends(get_db)):
    return await member_service.create_member(db, body)


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(member_id: int, body: MemberUpdate, db: AsyncSession = Depends(get_db)):
    member = await member_service.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")
    return await member_service.update_member(db, member, body)


@router.delete("/{member_id}", response_model=MemberResponse)
async def delete_member(member_id: int, db: AsyncSession = Depends(get_db)):
    member = await member_service.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Miembro no encontrado")
    return await member_service.delete_member(db, member)
