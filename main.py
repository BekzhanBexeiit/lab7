from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db import get_db
from models import Course, Enrollment, Student
from schemas import (
    CourseOut,
    CourseStats,
    EnrollmentDetail,
    EnrollmentIn,
    EnrollmentOut,
    StudentIn,
    StudentOut,
)

app = FastAPI(title="Course Catalog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Тип алиасы — db: SessionDep деп жазу ыңғайлы
SessionDep = Annotated[Session, Depends(get_db)]


# ── Constraint атауы → HTTP жауап ────────────────────────────────────────────
# naming_convention шаблондарынан шыққан нақты атаулар (check_models.py растайды)
CONSTRAINT_ERRORS: dict[str, tuple[int, str]] = {
    "students_email_key":                    (409, "Student with this email already exists"),
    "enrollments_course_id_student_id_key":  (409, "Student is already enrolled in this course"),
    "enrollments_course_id_fkey":            (404, "Course not found"),
    "enrollments_student_id_fkey":           (404, "Student not found"),
}


def raise_http_error(exc: IntegrityError) -> None:
    """IntegrityError-ды constraint атауымен HTTP жауапқа айналдырады.
    Белгісіз violation — бұл кодтағы қате, 500 қалдырамыз."""
    name = exc.orig.diag.constraint_name  # type: ignore[union-attr]
    if name in CONSTRAINT_ERRORS:
        status, detail = CONSTRAINT_ERRORS[name]
        raise HTTPException(status_code=status, detail=detail)
    # Белгісіз constraint — кодта қате бар, re-raise → 500
    raise exc


# ── Утилита: пагинация ────────────────────────────────────────────────────────

def pagination(page: int = 1, page_size: int = 20) -> dict:
    return {"offset": (page - 1) * page_size, "limit": page_size}


# ── Тамыр ────────────────────────────────────────────────────────────────────

@app.get("/")
def read_root():
    return {"message": "Course Catalog API is running"}


# ── Курстар ───────────────────────────────────────────────────────────────────

@app.get("/courses", response_model=list[CourseOut])
def list_courses(
    db: SessionDep,
    is_elective: bool | None = None,
    level: str | None = None,           # Step 7: деңгей бойынша сүзгі
    sort: str = "popular",
    p: dict = Depends(pagination),
):
    """Курстар тізімі. Сүзгілер: is_elective, level. Сұрыптау: popular (әдепкі) / title."""
    stmt = select(Course)

    # Факультатив сүзгісі
    if is_elective is not None:
        stmt = stmt.where(Course.is_elective == is_elective)

    # Деңгей сүзгісі
    if level is not None:
        stmt = stmt.where(Course.level == level)

    # Сұрыптау: likes бойынша кемуші, тең likes-та id бойынша (бет қабаттасу болмасын)
    if sort == "title":
        stmt = stmt.order_by(Course.title)
    else:
        stmt = stmt.order_by(Course.likes.desc(), Course.id)

    # Беттеу
    stmt = stmt.limit(p["limit"]).offset(p["offset"])

    return db.scalars(stmt).all()


@app.get("/courses/{course_id}", response_model=CourseOut)
def get_course(course_id: str, db: SessionDep):
    """Бір курс. Жоқ болса — 404."""
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@app.post("/courses/{course_id}/like", response_model=CourseOut)
def like_course(course_id: str, db: SessionDep):
    """Курсқа like қосады. UPDATE … RETURNING — жоғалтылған жаңарту болмайды."""
    stmt = (
        update(Course)
        .where(Course.id == course_id)
        # likes + 1 — DB өзі қосады (race condition болмайды)
        .values(likes=Course.likes + 1)
        .returning(Course)
    )
    course = db.scalars(stmt).one_or_none()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    db.commit()
    return course


# ── Студенттер ────────────────────────────────────────────────────────────────

@app.post("/students", response_model=StudentOut, status_code=201)
def create_student(data: StudentIn, db: SessionDep):
    """Жаңа студент жасайды. Email қайталанса — 409."""
    student = Student(name=data.name, email=data.email)
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        # commit()-тен кейін ғана DB-ға INSERT кетеді → constraint қатесі осында
        raise_http_error(exc)
    return student


# ── Тіркелулер ────────────────────────────────────────────────────────────────

@app.post("/enrollments", response_model=EnrollmentOut, status_code=201)
def create_enrollment(data: EnrollmentIn, db: SessionDep):
    """Студентті курсқа тіркейді. Курс/студент жоқ — 404, екірет — 409."""
    enrollment = Enrollment(course_id=data.course_id, student_id=data.student_id)
    db.add(enrollment)
    try:
        db.commit()
    except IntegrityError as exc:
        raise_http_error(exc)
    return enrollment


@app.get("/enrollments", response_model=list[EnrollmentDetail])
def list_enrollments(db: SessionDep):
    """Барлық тіркелулер — курс атауы мен студент атымен (JOIN)."""
    stmt = (
        select(
            Enrollment.id,
            Enrollment.course_id,
            Course.title.label("course_title"),   # label → EnrollmentDetail.course_title
            Enrollment.student_id,
            Student.name.label("student_name"),
            Enrollment.enrolled_at,
        )
        # Relationship бойынша JOIN — ON шартын SQLAlchemy FK-дан алады
        .join(Enrollment.course)
        .join(Enrollment.student)
        .order_by(Enrollment.id)
    )
    return db.execute(stmt).all()


# ── Статистика ────────────────────────────────────────────────────────────────

@app.get("/stats/courses", response_model=list[CourseStats])
def course_stats(db: SessionDep):
    """Әр курстың тіркелу саны. Тіркелмегендер де болады (LEFT JOIN → 0)."""
    stmt = (
        select(
            Course.id.label("course_id"),
            # count(*) емес! — тіркелусіз курс үшін Enrollment.id = NULL → count = 0
            func.count(Enrollment.id).label("enrolled"),
        )
        # LEFT JOIN: тіркелуі жоқ курс да нәтижеде қалады
        .outerjoin(Course.enrollments)
        .group_by(Course.id)
        .order_by(func.count(Enrollment.id).desc(), Course.id)
    )
    return db.execute(stmt).all()
