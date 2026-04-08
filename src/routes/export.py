from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.services import export_service, schedule_period_service

router = APIRouter(prefix="/api/schedule-periods/{period_id}/export", tags=["export"], dependencies=[Depends(get_current_user)])


@router.get("/excel")
async def export_excel(period_id: int, db: AsyncSession = Depends(get_db)):
    period = await schedule_period_service.get_period(db, period_id)
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periodo no encontrado")

    content = await export_service.export_excel(db, period_id)
    filename = f"horarios_{period.name.replace(' ', '_')}.xlsx"

    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
