"""add soft delete for exercises

Revision ID: 0002_soft_delete_exercises
Revises: 0001_initial
Create Date: 2026-04-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_soft_delete_exercises"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_exercises_deleted_at"), "exercises", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_exercises_deleted_at"), table_name="exercises")
    op.drop_column("exercises", "deleted_at")
