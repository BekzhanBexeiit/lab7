from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Барлық схемалардың негізі — camelCase JSON, from_attributes=True (SQLAlchemy объектілерін оқиды)."""
    model_config = ConfigDict(
        alias_generator=to_camel,      # snake_case → camelCase (is_elective → isElective)
        validate_by_name=True,
        validate_by_alias=True,
        from_attributes=True,          # SQLAlchemy моделінің атрибуттарынан оқу
    )


# ── Курстар ───────────────────────────────────────────────────────────────────

class CourseOut(CamelModel):
    """GET /courses және GET /courses/{id} жауабы."""
    id: str
    title: str
    description: str
    credits: int
    is_elective: bool
    likes: int
    level: str          # Step 7-де қосылды — курстың деңгейі


# ── Студенттер ────────────────────────────────────────────────────────────────

class StudentIn(CamelModel):
    """POST /students сұраныс денесі."""
    name: str = Field(min_length=2)    # Pydantic тексереді, DB-ға жетпей 422 береді
    email: EmailStr                    # email форматын тексереді


class StudentOut(StudentIn):
    """POST /students жауабы — id қосылады (DB берген)."""
    id: int


# ── Тіркелулер ────────────────────────────────────────────────────────────────

class EnrollmentIn(CamelModel):
    """POST /enrollments сұраныс денесі — student_id (Lab 5-тегі studentName емес!)."""
    course_id: str
    student_id: int


class EnrollmentOut(CamelModel):
    """POST /enrollments жауабы."""
    id: int
    course_id: str
    student_id: int
    enrolled_at: datetime


class EnrollmentDetail(EnrollmentOut):
    """GET /enrollments жауабы — JOIN арқылы курс атауы мен студент аты қосылады."""
    course_title: str
    student_name: str


# ── Статистика ────────────────────────────────────────────────────────────────

class CourseStats(CamelModel):
    """GET /stats/courses — әр курстың тіркелу саны."""
    course_id: str
    enrolled: int
