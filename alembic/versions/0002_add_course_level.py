"""add course level

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-02 00:00:00.000000

Неліктен 3 қадам?
  Бар кестеде (6 жол) NOT NULL баған бірден қосуға болмайды — DB бар жолдарға
  не мән жазу керектігін білмейді → NotNullViolation.
  Шешім: NULL рұқсат → мән толтыр → NULL тый.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: courses кестесіне level бағанын қосады (3 қадам)."""

    # Қадам 1: NULL рұқсатпен баған қосамыз
    # (бірден nullable=False қойсақ — бар 6 жол үшін мән жоқ → NotNullViolation)
    op.add_column("courses", sa.Column("level", sa.Text(), nullable=True))

    # Қадам 2: Бар жолдарды толтырамыз
    # Ереже: факультативтер → beginner, қалғандары → intermediate
    op.execute(
        "UPDATE courses SET level = CASE WHEN is_elective THEN 'beginner' "
        "ELSE 'intermediate' END"
    )

    # Қадам 3: Енді NULL тыямыз — барлық жолда мән бар, қате болмайды
    op.alter_column("courses", "level", nullable=False)


def downgrade() -> None:
    """Downgrade schema: level бағанын жояды (деректер жоғалады!)."""
    # Downgrade кері орындайды — level бағаны мен оның деректері жойылады
    op.drop_column("courses", "level")
