from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.schemas.shift_type import ShiftTypeCreate, ShiftTypeResponse, ShiftTypeUpdate
from src.schemas.pagination import PaginatedResponse, PaginationParams
from src.services import shift_type_service

router = APIRouter(prefix="/api/shift-types", tags=["shift-types"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=PaginatedResponse[ShiftTypeResponse])
async def list_shift_types(include_inactive: bool = Query(False), pagination: PaginationParams = Depends(), db: AsyncSession = Depends(get_db)):
    items, total = await shift_type_service.list_shift_types(db, include_inactive, pagination.offset, pagination.page_size)
    return PaginatedResponse(items=items, total=total, page=pagination.page, page_size=pagination.page_size, pages=max(1, (total + pagination.page_size - 1) // pagination.page_size))


@router.post("", response_model=ShiftTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_shift_type(body: ShiftTypeCreate, db: AsyncSession = Depends(get_db)):
    return await shift_type_service.create_shift_type(db, body)


@router.put("/{shift_type_id}", response_model=ShiftTypeResponse)
async def update_shift_type(shift_type_id: int, body: ShiftTypeUpdate, db: AsyncSession = Depends(get_db)):
    st = await shift_type_service.get_shift_type(db, shift_type_id)
    if not st:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de turno no encontrado")
    return await shift_type_service.update_shift_type(db, st, body)


@router.delete("/{shift_type_id}", response_model=ShiftTypeResponse)
async def delete_shift_type(shift_type_id: int, db: AsyncSession = Depends(get_db)):
    st = await shift_type_service.get_shift_type(db, shift_type_id)
    if not st:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tipo de turno no encontrado")
    return await shift_type_service.update_shift_type(db, st, ShiftTypeUpdate(is_active=False))
