"""create catalog tables

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000

Бұл migration бос дерекқорда 3 кестені жасайды: courses, students, enrollments.
Бар дерекқорда (Lab 6-дан) тек 'stamp' жасалады: alembic stamp head
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: 3 кесте + индекс жасайды."""

    # ── courses ───────────────────────────────────────────────────────────────
    op.create_table(
        "courses",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False),
        sa.Column(
            "is_elective",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "likes",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        # op.f() — naming_convention шаблонын қайта қолданбасын деп атауды "мұздатады"
        sa.CheckConstraint("credits > 0", name=op.f("courses_credits_check")),
        sa.CheckConstraint("likes >= 0", name=op.f("courses_likes_check")),
        sa.PrimaryKeyConstraint("id", name=op.f("courses_pkey")),
    )

    # ── students ──────────────────────────────────────────────────────────────
    op.create_table(
        "students",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.CheckConstraint("length(name) >= 2", name=op.f("students_name_check")),
        sa.PrimaryKeyConstraint("id", name=op.f("students_pkey")),
        sa.UniqueConstraint("email", name=op.f("students_email_key")),
    )

    # ── enrollments ───────────────────────────────────────────────────────────
    op.create_table(
        "enrollments",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column("course_id", sa.Text(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["courses.id"],
            name=op.f("enrollments_course_id_fkey"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("enrollments_student_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("enrollments_pkey")),
        sa.UniqueConstraint(
            "course_id", "student_id", name=op.f("enrollments_course_id_student_id_key")
        ),
    )

    # student_id-де индекс — JOIN сұрауларын жылдамдатады
    op.create_index(
        op.f("enrollments_student_id_idx"),
        "enrollments",
        ["student_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema: кері тәртіппен жояды (FK тәуелділігіне байланысты)."""
    # Алдымен enrollments (courses мен students-ке FK бар)
    op.drop_index(op.f("enrollments_student_id_idx"), table_name="enrollments")
    op.drop_table("enrollments")
    # Содан кейін students және courses
    op.drop_table("students")
    op.drop_table("courses")
