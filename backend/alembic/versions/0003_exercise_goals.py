"""add per-exercise goal fields

Revision ID: 0003_exercise_goals
Revises: 0002_soft_delete_exercises
Create Date: 2026-04-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_exercise_goals"
down_revision: Union[str, None] = "0002_soft_delete_exercises"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("goal_reps", sa.Integer(), nullable=True))
    op.add_column("exercises", sa.Column("goal_duration_seconds", sa.Integer(), nullable=True))
    op.add_column("exercises", sa.Column("goal_weight_lbs", sa.Numeric(8, 2), nullable=True))

    op.execute(
        """
        UPDATE exercises
        SET
          goal_reps = CASE
            WHEN metric_type = 'reps' OR metric_type = 'reps_plus_weight_lbs' THEN 40
            ELSE NULL
          END,
          goal_duration_seconds = CASE
            WHEN metric_type = 'duration_seconds' THEN 40
            ELSE NULL
          END,
          goal_weight_lbs = CASE
            WHEN metric_type = 'reps_plus_weight_lbs' THEN 15
            ELSE NULL
          END
        """
    )

    op.create_check_constraint(
        "ck_exercises_goal_positive",
        "exercises",
        "(goal_reps IS NULL OR goal_reps > 0) AND "
        "(goal_duration_seconds IS NULL OR goal_duration_seconds > 0) AND "
        "(goal_weight_lbs IS NULL OR goal_weight_lbs > 0)",
    )
    op.create_check_constraint(
        "ck_exercises_goal_matches_metric",
        "exercises",
        "(" 
        "(metric_type = 'reps' AND goal_reps IS NOT NULL AND goal_duration_seconds IS NULL AND goal_weight_lbs IS NULL) "
        "OR "
        "(metric_type = 'duration_seconds' AND goal_duration_seconds IS NOT NULL AND goal_reps IS NULL AND goal_weight_lbs IS NULL) "
        "OR "
        "(metric_type = 'reps_plus_weight_lbs' AND goal_reps IS NOT NULL AND goal_weight_lbs IS NOT NULL AND goal_duration_seconds IS NULL)"
        ")",
    )


def downgrade() -> None:
    op.drop_constraint("ck_exercises_goal_matches_metric", "exercises", type_="check")
    op.drop_constraint("ck_exercises_goal_positive", "exercises", type_="check")
    op.drop_column("exercises", "goal_weight_lbs")
    op.drop_column("exercises", "goal_duration_seconds")
    op.drop_column("exercises", "goal_reps")
