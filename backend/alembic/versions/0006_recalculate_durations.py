"""recalculate workout durations

Revision ID: 0006_recalculate_durations
Revises: 0005_add_workouts
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

import math
import json

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006_recalculate_durations"
down_revision: Union[str, None] = "0005_add_workouts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, definition FROM workouts")).mappings().all()

    for row in rows:
        definition = row["definition"] or {}
        if isinstance(definition, str):
            definition = json.loads(definition)
        steps = definition.get("steps") or []
        total_seconds = sum(
            int(step.get("duration_sec") or 0)
            for step in steps
            if step.get("kind") in {"timed_exercise", "rest"}
        )
        duration_min = max(1, math.ceil(total_seconds / 60))
        connection.execute(
            sa.text("UPDATE workouts SET duration_min = :duration_min WHERE id = :id"),
            {"duration_min": duration_min, "id": row["id"]},
        )


def downgrade() -> None:
    pass
