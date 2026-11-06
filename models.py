from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Course(Base):
    """courses кестесі — курстар каталогы."""
    __tablename__ = "courses"
    __table_args__ = (
        # CheckConstraint name-і тек "жалғауы" — толық ат: courses_credits_check
        CheckConstraint("credits > 0", name="credits"),
        CheckConstraint("likes >= 0", name="likes"),
    )

    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    credits: Mapped[int]
    # server_default — DB өзі қояды, Python емес
    is_elective: Mapped[bool] = mapped_column(server_default=text("false"))
    likes: Mapped[int] = mapped_column(server_default=text("0"))
    level: Mapped[str]                  # Step 7: beginner / intermediate / advanced

    # Relationship — колонка жасамайды, тек байланысқан объектілерге ыңғайлы қол жеткізу
    # passive_deletes=True: ON DELETE CASCADE/RESTRICT-ті DB өзі орындайды, ORM емес
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", passive_deletes=True
    )


class Student(Base):
    """students кестесі — студенттер."""
    __tablename__ = "students"
    __table_args__ = (
        # Аты кем дегенде 2 символ — name="name" → толық ат: students_name_check
        CheckConstraint("length(name) >= 2", name="name"),
    )

    # bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    name: Mapped[str]
    # unique=True → students_email_key (naming_convention uq шаблоны бойынша)
    email: Mapped[str] = mapped_column(unique=True)

    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="student", passive_deletes=True
    )


class Enrollment(Base):
    """enrollments кестесі — студентті курсқа тіркеу."""
    __tablename__ = "enrollments"
    __table_args__ = (
        # Бір студент бір курсқа тек бір рет тіркеле алады
        # → enrollments_course_id_student_id_key
        UniqueConstraint("course_id", "student_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)

    # ON DELETE RESTRICT: тіркелуі бар курсты өшіруге болмайды
    # → enrollments_course_id_fkey
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="RESTRICT")
    )

    # ON DELETE CASCADE: студент өшірілсе, оның тіркелулері де өшеді
    # index=True → enrollments_student_id_idx (FK-ларда индекс — жылдам JOIN үшін)
    # → enrollments_student_id_fkey
    student_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("students.id", ondelete="CASCADE"),
        index=True,
    )

    # Тіркелу уақыты — DB өзі now() қояды
    enrolled_at: Mapped[datetime] = mapped_column(server_default=func.now())

    course: Mapped["Course"] = relationship(back_populates="enrollments")
    student: Mapped["Student"] = relationship(back_populates="enrollments")
