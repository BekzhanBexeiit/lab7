from collections.abc import Iterator
from datetime import datetime

from sqlalchemy import DateTime, MetaData, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings

# ── Constraint атаулары үшін шаблондар ───────────────────────────────────────
# Lab 6-да PostgreSQL өзі қойған атаулармен (courses_credits_check,
# enrollments_course_id_fkey, т.б.) сәйкес болуы керек.
# Step 5-те constraint атауымен қате түрін табамыз — сондықтан дәл сәйкес болуы маңызды.
NAMING_CONVENTION = {
    "ix": "%(table_name)s_%(column_0_N_name)s_idx",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}


class Base(DeclarativeBase):
    # Барлық модельдер осы Base-дан мұра алады
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    # str → Text (varchar емес), datetime → timestamptz
    type_annotation_map = {
        str: Text,
        datetime: DateTime(timezone=True),
    }


# Бір Engine — бүкіл апп үшін connection pool ұстайды
engine = create_engine(settings.database_url, echo=settings.sql_echo)

# Session фабрикасы — әр HTTP сұраныс өз сессиясын алады
SessionLocal = sessionmaker(engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: әр route үшін сессия ашады, жауап кеткен соң жабады."""
    with SessionLocal() as session:
        yield session
