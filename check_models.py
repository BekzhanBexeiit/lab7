"""
Модельдердің нақты дерекқормен сәйкестігін тексереді:
1. Әр кестенің жолдарын оқиды (бағана атауы немесе типі қате болса — қате шығады)
2. Base.metadata-дағы constraint/index атауларын pg_constraint + pg_indexes-пен салыстырады

Іске қосу: python check_models.py
Күтілетін нәтиже:
    courses: 6 rows
    students: 3 rows
    enrollments: 6 rows
    names only in models: none
    names only in database: none
"""
from sqlalchemy import select, text

from db import Base, SessionLocal
from models import Course, Enrollment, Student  # noqa: F401 — Base.metadata-ға тіркеу үшін

# Дерекқордағы барлық constraint және index атаулары
DB_NAMES = """
SELECT conname FROM pg_constraint
WHERE connamespace = 'public'::regnamespace AND contype IN ('p', 'u', 'f', 'c')
UNION
SELECT indexname FROM pg_indexes WHERE schemaname = 'public'
"""

with SessionLocal() as db:
    # Әр кестеден барлық жолдарды оқимыз — бағана атауы қате болса осы жерде шығады
    for model in (Course, Student, Enrollment):
        print(f"{model.__tablename__}: {len(db.scalars(select(model)).all())} rows")

    # Дерекқордағы атаулар (alembic_version кестесінің атаулары бізге керек емес)
    in_db = {n for n in db.scalars(text(DB_NAMES)) if not n.startswith("alembic")}

# Модельдердегі атаулар (Base.metadata арқылы)
in_models = {
    c.name
    for table in Base.metadata.tables.values()
    for c in [*table.constraints, *table.indexes]
}

# Айырмашылықты шығарамыз
print("names only in models:", sorted(in_models - in_db) or "none")
print("names only in database:", sorted(in_db - in_models) or "none")
