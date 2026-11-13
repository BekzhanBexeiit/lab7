# Course Catalog API — Lab 7

**Advanced Web Technologies · Lab 7**

FastAPI backend connected to PostgreSQL via SQLAlchemy 2.x ORM and Alembic migrations.
Built on top of the Labs 4–6 project: replaces the in-memory data with a real database.

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Database driver | psycopg 3 (binary) |
| Migrations | Alembic |
| Settings | pydantic-settings |
| Database | PostgreSQL 16+ |

---

## Project Structure

```
course-catalog-api/
├── main.py                          # All FastAPI routes (8 endpoints)
├── config.py                        # Settings: reads DATABASE_URL from .env
├── db.py                            # Engine, Base, SessionLocal, get_db dependency
├── models.py                        # SQLAlchemy ORM models (Course, Student, Enrollment)
├── schemas.py                       # Pydantic schemas for request/response JSON
├── seed.sql                         # Initial data (TRUNCATE + INSERT)
├── check_db.py                      # Verify database connection
├── check_models.py                  # Verify model ↔ database constraint name match
├── try_errors.py                    # Test all 5 HTTP error responses (needs running server)
├── alembic.ini                      # Alembic configuration
├── alembic/
│   ├── env.py                       # Connects Alembic to project models and settings
│   ├── script.py.mako               # Migration file template
│   └── versions/
│       ├── 0001_create_catalog_tables.py   # Creates courses, students, enrollments
│       └── 0002_add_course_level.py        # Adds level column (3-step migration)
├── .env.example                     # Sample environment file (copy to .env)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to Run

### Prerequisites
- Python 3.11+
- PostgreSQL 16+

### 1. Create the database role and database (as `postgres` superuser)

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

### 2. Clone and set up the project

```bash
git clone https://github.com/BekzhanBexeiit/lab7.git
cd lab7
```

### 3. Create virtual environment and install dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Configure environment

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env` if your password or port differs:
```
DATABASE_URL=postgresql+psycopg://catalog_app:change-me@localhost:5432/course_catalog
```

### 5. Run migrations

```bash
alembic upgrade head
```

This runs both migrations in order:
- `0001` — creates `courses`, `students`, `enrollments` tables
- `0002` — adds the `level` column to `courses` (3-step migration)

### 6. Load initial data

```bash
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
```

### 7. Verify setup (optional)

```bash
python check_db.py      # Should print: connected to course_catalog as catalog_app
python check_models.py  # Should print: names only in models: none / names only in database: none
```

### 8. Start the server

```bash
fastapi dev main.py
```

API docs: **http://localhost:8000/docs**

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/courses` | List courses (filters: `is_elective`, `level`; sort: `popular`/`title`; pagination: `page`, `page_size`) |
| GET | `/courses/{course_id}` | Get a single course |
| POST | `/courses/{course_id}/like` | Increment likes via `UPDATE … SET likes = likes + 1` |
| POST | `/students` | Create a student |
| POST | `/enrollments` | Enroll a student in a course |
| GET | `/enrollments` | List all enrollments with course title and student name (JOIN) |
| GET | `/stats/courses` | Enrollment count per course including zeros (LEFT JOIN + `count(Enrollment.id)`) |

---

## What Changed from Lab 5

- **Persistent data** — all data is stored in PostgreSQL; it survives server restarts
- **`POST /enrollments`** — now requires `studentId` (integer) instead of `studentName`; create the student first via `POST /students`
- **New routes** — `POST /students`, `GET /enrollments` with JOIN, `GET /stats/courses`
- **`level` field** — every course has a `level` (`beginner` / `intermediate` / `advanced`); filterable via `?level=`
- **Proper error responses** — constraint violations return `409` or `404` instead of `500`

---

## Alembic Migration Commands

| Command | What it does |
|---------|--------------|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back the last migration |
| `alembic current` | Show current database version |
| `alembic history` | Show the full migration chain |
| `alembic revision --autogenerate -m "text"` | Generate a draft migration from model diff |
| `alembic check` | Check if models and database have diverged |
| `alembic upgrade 0001:0002 --sql` | Print migration SQL without running it |
| `alembic stamp head` | Mark database as up to date without running migrations |

---

## Migration 0002 — Why 3 Steps?

Adding a `NOT NULL` column to a table that already has rows fails immediately:

```
IntegrityError: column "level" contains null values
```

The correct approach:

```python
# Step 1 — add as nullable (existing rows get NULL, no error)
op.add_column("courses", sa.Column("level", sa.Text(), nullable=True))

# Step 2 — fill existing rows with a business rule
op.execute("UPDATE courses SET level = CASE WHEN is_elective "
           "THEN 'beginner' ELSE 'intermediate' END")

# Step 3 — now all rows have a value, safe to forbid NULL
op.alter_column("courses", "level", nullable=False)
```

The whole migration runs in one transaction — if any step fails, the database stays at `0001`.

---

## Database Error → HTTP Response Mapping

Constraint violations are translated to proper HTTP responses using the constraint name (not SQLSTATE, which is the same for all UNIQUE violations):

| Constraint | Violation | HTTP Response |
|------------|-----------|---------------|
| `students_email_key` | Duplicate email | `409 Student with this email already exists` |
| `enrollments_course_id_student_id_key` | Already enrolled | `409 Student is already enrolled in this course` |
| `enrollments_course_id_fkey` | Course not found | `404 Course not found` |
| `enrollments_student_id_fkey` | Student not found | `404 Student not found` |

```bash
# Test all 5 cases (server must be running)
python try_errors.py
# Expected: 5 of 5 as expected
```

---

## Key Design Decisions

**Why constraint name instead of SQLSTATE?**
SQLSTATE `23505` fires for *any* UNIQUE violation. We have two UNIQUE constraints, so SQLSTATE alone cannot tell them apart. The constraint name is specific and reliable.

**Why `UPDATE SET likes = likes + 1` instead of read → increment → write?**
Two simultaneous requests would both read `likes = 11`, both write `12`, and one like would be lost (lost update). Delegating the addition to the database with `UPDATE … SET likes = likes + 1` applies a row lock — both increments are counted.

**Why catch `IntegrityError` after `commit()` instead of checking with `SELECT` first?**
A `SELECT` check has a race condition — another request can insert the same value between the check and the insert. It's safer to attempt the operation and handle the rejection.

---

## Experiment Log

| # | Experiment | What happened | Cause | Fix |
|---|------------|---------------|-------|-----|
| 1 | Changed `uq` template in `naming_convention` | `check_models.py` showed `students_email_unique` in models vs `students_email_key` in DB | Template produced different name than PostgreSQL chose | Restored `%(table_name)s_%(column_0_N_name)s_key` |
| 2 | Removed `min_length=2` from `StudentIn`, sent name `N` | `500 Internal Server Error`; log: `students_name_check` constraint violated | Pydantic no longer blocked it; DB CHECK fired but name not in `CONSTRAINT_ERRORS` → re-raised as 500 | Restored `Field(min_length=2)` |
| 3 | Typo in `CONSTRAINT_ERRORS` key: `students_email_uniq` | `500` instead of `409`; log showed real name `students_email_key` | Dict lookup failed → treated as unknown violation → 500 | Fixed key to `students_email_key` |
| 4 | `ALTER TABLE courses ALTER COLUMN title DROP NOT NULL` in psql | `alembic check` failed: `modify_nullable on courses.title` | Model says NOT NULL, database says nullable — mismatch | `ALTER COLUMN title SET NOT NULL` |
| 5 | Auto-generated migration 0002 with `nullable=False` directly | `IntegrityError: NotNullViolation — column "level" contains null values` | Cannot add NOT NULL column to non-empty table without a default | Rewrote as 3-step migration |
| 6 | Commented out `import models` in `alembic/env.py` | Migration proposed `DROP TABLE` for all 3 tables | `Base.metadata` was empty → Alembic saw all tables as "extra" | Deleted `0003_oops.py`, restored `import models` |
| 7 | Added `phone: Mapped[str \| None]` to `Student` without migration | `alembic check` failed: `Detected added column 'students.phone'` | Model ahead of database — diverged | Removed the `phone` field |
| 8 | Created two migrations branching from `0002` (0003 and 0004) | `alembic upgrade head` failed: `Multiple head revisions are present` | Two independent branches, Alembic can't choose | `alembic merge heads` → `0005`; deleted experiment files |

---

## Migration 0002 Self-Check

| What to check | Result |
|---------------|--------|
| Goal and steps | ✅ Add `level TEXT NOT NULL` to `courses`. Three steps with one responsibility each. |
| Data | ✅ All 6 existing rows filled: `is_elective=true` → `beginner`, rest → `intermediate`. No data loss. |
| Renames and drops | ✅ No renames or drops in upgrade. Downgrade drops the column — data lost on rollback (acceptable for training DB). |
| Rollback | ✅ `downgrade()` drops the column. Tested: downgrade → column gone, upgrade → column restored with correct values. |
| Verification | ✅ `--sql` output reviewed. `alembic check` clean. upgrade → downgrade → upgrade cycle passes. |
| History | ✅ Single head: `alembic heads` → `0002 (head)`. Migration committed with model and schema changes. |
| Application | ✅ `CourseOut` and `seed.sql` updated with `level`. `GET /courses?level=beginner` returns 2 courses. |

---

## Resetting to Initial Data

```bash
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
```

> ⚠️ `TRUNCATE` deletes all data. For training databases only.
