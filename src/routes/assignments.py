from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.schemas.assignment import AssignmentCreate, AssignmentBulkCreate, AssignmentResponse, AssignmentUpdate
from src.services import assignment_service, validation_service

router = APIRouter(prefix="/api/schedule-periods/{period_id}", tags=["assignments"], dependencies=[Depends(get_current_user)])


@router.get("/assignments", response_model=list[AssignmentResponse])
async def list_assignments(period_id: int, db: AsyncSession = Depends(get_db)):
    return await assignment_service.list_assignments(db, period_id)


@router.post("/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(period_id: int, body: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    return await assignment_service.create_assignment(db, period_id, body)


@router.post("/assignments/bulk", response_model=list[AssignmentResponse])
async def bulk_create(period_id: int, body: AssignmentBulkCreate, db: AsyncSession = Depends(get_db)):
    return await assignment_service.bulk_create_assignments(db, period_id, body.assignments)


@router.put("/assignments/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(period_id: int, assignment_id: int, body: AssignmentUpdate, db: AsyncSession = Depends(get_db)):
    assignment = await assignment_service.get_assignment(db, assignment_id)
    if not assignment or assignment.schedule_period_id != period_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignacion no encontrada")
    return await assignment_service.update_assignment(db, assignment, body)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(period_id: int, assignment_id: int, db: AsyncSession = Depends(get_db)):
    assignment = await assignment_service.get_assignment(db, assignment_id)
    if not assignment or assignment.schedule_period_id != period_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignacion no encontrada")
    await assignment_service.delete_assignment(db, assignment)


@router.get("/validate")
async def validate(period_id: int, db: AsyncSession = Depends(get_db)):
    warnings = await validation_service.validate_period(db, period_id)
    return {"warnings": warnings}
