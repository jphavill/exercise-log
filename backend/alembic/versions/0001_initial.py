"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


metric_type_enum = postgresql.ENUM(
    "duration_seconds", "reps", "reps_plus_weight_lbs", name="metric_type_enum", create_type=False
)


def upgrade() -> None:
    metric_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("metric_type", metric_type_enum, nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_exercises_id"), "exercises", ["id"], unique=False)
    op.create_index(op.f("ix_exercises_slug"), "exercises", ["slug"], unique=False)

    op.create_table(
        "exercise_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.Integer(), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("weight_lbs", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exercise_logs_id"), "exercise_logs", ["id"], unique=False)
    op.create_index(
        op.f("ix_exercise_logs_exercise_id"), "exercise_logs", ["exercise_id"], unique=False
    )
    op.create_index(op.f("ix_exercise_logs_logged_at"), "exercise_logs", ["logged_at"], unique=False)
    op.create_index(
        "ix_exercise_logs_exercise_id_logged_at",
        "exercise_logs",
        ["exercise_id", "logged_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_exercise_logs_exercise_id_logged_at", table_name="exercise_logs")
    op.drop_index(op.f("ix_exercise_logs_logged_at"), table_name="exercise_logs")
    op.drop_index(op.f("ix_exercise_logs_exercise_id"), table_name="exercise_logs")
    op.drop_index(op.f("ix_exercise_logs_id"), table_name="exercise_logs")
    op.drop_table("exercise_logs")

    op.drop_index(op.f("ix_exercises_slug"), table_name="exercises")
    op.drop_index(op.f("ix_exercises_id"), table_name="exercises")
    op.drop_table("exercises")
    metric_type_enum.drop(op.get_bind(), checkfirst=True)
