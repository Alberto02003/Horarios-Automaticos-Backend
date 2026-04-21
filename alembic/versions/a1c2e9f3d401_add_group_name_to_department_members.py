"""add group_name to department_members

Revision ID: a1c2e9f3d401
Revises: 430667857ba4
Create Date: 2026-04-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c2e9f3d401"
down_revision: Union[str, Sequence[str], None] = "430667857ba4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("department_members", sa.Column("group_name", sa.Text(), nullable=True))
    op.create_index("ix_department_members_group_name", "department_members", ["group_name"])


def downgrade() -> None:
    op.drop_index("ix_department_members_group_name", table_name="department_members")
    op.drop_column("department_members", "group_name")
