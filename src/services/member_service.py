from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.department_member import DepartmentMember
from src.schemas.member import MemberCreate, MemberUpdate


async def list_members(db: AsyncSession, include_inactive: bool = False) -> list[DepartmentMember]:
    query = select(DepartmentMember).order_by(DepartmentMember.full_name)
    if not include_inactive:
        query = query.where(DepartmentMember.is_active.is_(True))
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_member(db: AsyncSession, member_id: int) -> DepartmentMember | None:
    result = await db.execute(select(DepartmentMember).where(DepartmentMember.id == member_id))
    return result.scalar_one_or_none()


async def create_member(db: AsyncSession, data: MemberCreate) -> DepartmentMember:
    member = DepartmentMember(**data.model_dump(exclude_none=True))
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def update_member(db: AsyncSession, member: DepartmentMember, data: MemberUpdate) -> DepartmentMember:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(member, field, value)
    await db.commit()
    await db.refresh(member)
    return member


async def delete_member(db: AsyncSession, member: DepartmentMember) -> DepartmentMember:
    member.is_active = False
    await db.commit()
    await db.refresh(member)
    return member
