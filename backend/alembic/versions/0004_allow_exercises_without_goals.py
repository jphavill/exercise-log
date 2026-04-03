"""allow exercises without goals

Revision ID: 0004_allow_no_goals
Revises: 0003_exercise_goals
Create Date: 2026-04-03 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0004_allow_no_goals"
down_revision: Union[str, None] = "0003_exercise_goals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.drop_constraint("ck_exercises_goal_matches_metric", type_="check")
        batch_op.create_check_constraint(
            "ck_exercises_goal_matches_metric",
            "(" 
            "(goal_reps IS NULL AND goal_duration_seconds IS NULL AND goal_weight_lbs IS NULL) "
            "OR "
            "(metric_type = 'reps' AND goal_reps IS NOT NULL AND goal_duration_seconds IS NULL AND goal_weight_lbs IS NULL) "
            "OR "
            "(metric_type = 'duration_seconds' AND goal_duration_seconds IS NOT NULL AND goal_reps IS NULL AND goal_weight_lbs IS NULL) "
            "OR "
            "(metric_type = 'reps_plus_weight_lbs' AND goal_reps IS NOT NULL AND goal_weight_lbs IS NOT NULL AND goal_duration_seconds IS NULL)"
            ")",
        )


def downgrade() -> None:
    with op.batch_alter_table("exercises") as batch_op:
        batch_op.drop_constraint("ck_exercises_goal_matches_metric", type_="check")
        batch_op.create_check_constraint(
            "ck_exercises_goal_matches_metric",
            "(" 
            "(metric_type = 'reps' AND goal_reps IS NOT NULL AND goal_duration_seconds IS NULL AND goal_weight_lbs IS NULL) "
            "OR "
            "(metric_type = 'duration_seconds' AND goal_duration_seconds IS NOT NULL AND goal_reps IS NULL AND goal_weight_lbs IS NULL) "
            "OR "
            "(metric_type = 'reps_plus_weight_lbs' AND goal_reps IS NOT NULL AND goal_weight_lbs IS NOT NULL AND goal_duration_seconds IS NULL)"
            ")",
        )
