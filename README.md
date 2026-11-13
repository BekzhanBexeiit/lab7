# Course Catalog API — 7-зертхана

**Заманауи веб-технологиялар · 7-зертхана**

SQLAlchemy 2.x ORM және Alembic миграциялары арқылы PostgreSQL-ге қосылған FastAPI бэкенд.
4–6-зертханалар жобасының үстіне салынған: жадта сақталатын деректер нақты дерекқормен ауыстырылды.

---

## Технологиялар

| Қабат | Құрал |
|-------|-------|
| Веб-фреймворк | FastAPI |
| ORM | SQLAlchemy 2.x |
| Дерекқор драйвері | psycopg 3 (binary) |
| Миграциялар | Alembic |
| Параметрлер | pydantic-settings |
| Дерекқор | PostgreSQL 16+ |

---

## Жоба құрылымы

```
course-catalog-api/
├── main.py                          # Барлық FastAPI маршруттары (8 endpoint)
├── config.py                        # Параметрлер: .env-тен DATABASE_URL оқиды
├── db.py                            # Engine, Base, SessionLocal, get_db dependency
├── models.py                        # SQLAlchemy ORM модельдері (Course, Student, Enrollment)
├── schemas.py                       # Сұраныс/жауап JSON үшін Pydantic схемалары
├── seed.sql                         # Бастапқы деректер (TRUNCATE + INSERT)
├── check_db.py                      # Дерекқор қосылымын тексеру
├── check_models.py                  # Модель ↔ дерекқор constraint атауларының сәйкестігін тексеру
├── try_errors.py                    # 5 HTTP қате жауабын тестілеу (сервер іске қосылған болуы керек)
├── alembic.ini                      # Alembic конфигурациясы
├── alembic/
│   ├── env.py                       # Alembic-ті жоба модельдері мен параметрлеріне қосады
│   ├── script.py.mako               # Миграция файлының үлгісі
│   └── versions/
│       ├── 0001_create_catalog_tables.py   # courses, students, enrollments кестелерін жасайды
│       └── 0002_add_course_level.py        # level бағанын қосады (3 қадамды миграция)
├── .env.example                     # Параметрлер файлының үлгісі (.env-ке көшір)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Іске қосу жолы

### Алдын ала талаптар
- Python 3.11+
- PostgreSQL 16+

### 1. Дерекқор рөлі мен дерекқорды жасау (`postgres` superuser ретінде)

```sql
CREATE ROLE catalog_app LOGIN PASSWORD 'change-me';
CREATE DATABASE course_catalog OWNER catalog_app;
```

### 2. Жобаны клондау және орнату

```bash
git clone https://github.com/BekzhanBexeiit/lab7.git
cd lab7
```

### 3. Виртуалды орта жасау және тәуелділіктерді орнату

```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Параметрлерді баптау

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Егер пароль немесе порт өзгеше болса, `.env`-ті өңдеңіз:
```
DATABASE_URL=postgresql+psycopg://catalog_app:change-me@localhost:5432/course_catalog
```

### 5. Миграцияларды жүргізу

```bash
alembic upgrade head
```

Екі миграция кезекпен жүргізіледі:
- `0001` — `courses`, `students`, `enrollments` кестелерін жасайды
- `0002` — `courses` кестесіне `level` бағанын қосады (3 қадамды миграция)

### 6. Бастапқы деректерді жүктеу

```bash
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
```

### 7. Орнатуды тексеру (міндетті емес)

```bash
python check_db.py      # Шығуы керек: connected to course_catalog as catalog_app
python check_models.py  # Шығуы керек: names only in models: none / names only in database: none
```

### 8. Серверді іске қосу

```bash
fastapi dev main.py
```

API құжаттамасы: **http://localhost:8000/docs**

---

## API Маршруттары

| Әдіс | Жол | Сипаттама |
|------|-----|-----------|
| GET | `/` | Сервер жұмыс істеп тұрғанын тексеру |
| GET | `/courses` | Курстар тізімі (сүзгілер: `is_elective`, `level`; сұрыптау: `popular`/`title`; беттеу: `page`, `page_size`) |
| GET | `/courses/{course_id}` | Бір курсты алу |
| POST | `/courses/{course_id}/like` | `UPDATE … SET likes = likes + 1` арқылы like қосу |
| POST | `/students` | Студент жасау |
| POST | `/enrollments` | Студентті курсқа тіркеу |
| GET | `/enrollments` | Курс атауы мен студент атымен барлық тіркелулер (JOIN) |
| GET | `/stats/courses` | Әр курстың тіркелу саны, нөлдер де қосылған (LEFT JOIN + `count(Enrollment.id)`) |

---

## 5-зертханадан өзгерістер

- **Тұрақты деректер** — барлық деректер PostgreSQL-де сақталады; сервер қайта іске қосылса да жоғалмайды
- **`POST /enrollments`** — енді `studentName` орнына `studentId` (бүтін сан) қабылдайды; алдымен `POST /students` арқылы студент жасаңыз
- **Жаңа маршруттар** — `POST /students`, JOIN арқылы `GET /enrollments`, `GET /stats/courses`
- **`level` өрісі** — әр курстың деңгейі бар (`beginner` / `intermediate` / `advanced`); `?level=` арқылы сүзуге болады
- **Дұрыс қате жауаптары** — constraint бұзылса `500` орнына `409` немесе `404` қайтарылады

---

## Alembic Миграция Командалары

| Команда | Не жасайды |
|---------|-----------|
| `alembic upgrade head` | Барлық күтіп тұрған миграцияларды жүргізеді |
| `alembic downgrade -1` | Соңғы миграцияны кері қайтарады |
| `alembic current` | Дерекқордың қазіргі нұсқасын көрсетеді |
| `alembic history` | Толық миграция тізбегін көрсетеді |
| `alembic revision --autogenerate -m "мәтін"` | Модель айырмашылығынан миграция жобасын жасайды |
| `alembic check` | Модельдер мен дерекқор арасында айырмашылық бар ма тексереді |
| `alembic upgrade 0001:0002 --sql` | Іске қоспай миграция SQL-ін басып шығарады |
| `alembic stamp head` | Миграцияларды іске қоспай дерекқорды жаңартылды деп белгілейді |

---

## 0002 Миграциясы — Неліктен 3 Қадам?

Деректері бар кестеге `NOT NULL` бағанын бірден қосу бірден қатемен тоқтайды:

```
IntegrityError: column "level" contains null values
```

Дұрыс жол:

```python
# Қадам 1 — NULL рұқсатпен қосамыз (бар жолдар NULL алады, қате болмайды)
op.add_column("courses", sa.Column("level", sa.Text(), nullable=True))

# Қадам 2 — бар жолдарды толтырамыз
op.execute("UPDATE courses SET level = CASE WHEN is_elective "
           "THEN 'beginner' ELSE 'intermediate' END")

# Қадам 3 — енді барлық жолда мән бар, NULL-ды тыюға болады
op.alter_column("courses", "level", nullable=False)
```

Бүкіл миграция бір транзакцияда жүгіреді — кез келген қадам сәтсіз болса, дерекқор `0001` нұсқасында қалады.

---

## Дерекқор Қатесі → HTTP Жауабы

Constraint бұзылулары constraint атауы арқылы дұрыс HTTP жауапқа айналдырылады (SQLSTATE емес, себебі барлық UNIQUE бұзылулар үшін бірдей):

| Constraint | Бұзылу | HTTP Жауабы |
|------------|--------|-------------|
| `students_email_key` | Email қайталанған | `409 Student with this email already exists` |
| `enrollments_course_id_student_id_key` | Қайта тіркелу | `409 Student is already enrolled in this course` |
| `enrollments_course_id_fkey` | Курс жоқ | `404 Course not found` |
| `enrollments_student_id_fkey` | Студент жоқ | `404 Student not found` |

```bash
# 5 жағдайды тексеру (сервер іске қосылған болуы керек)
python try_errors.py
# Күтілетін нәтиже: 5 of 5 as expected
```

---

## Басты Шешімдер

**Неліктен SQLSTATE емес, constraint атауы?**
SQLSTATE `23505` *кез келген* UNIQUE бұзылу кезінде шығады. Бізде екі UNIQUE constraint бар, сондықтан SQLSTATE жеткіліксіз. Constraint атауы дәл нақты.

**Неліктен `UPDATE SET likes = likes + 1`, оқу → өзгерту → жазу емес?**
Екі бір мезгілді сұраныс екеуі де `likes = 11` оқиды, екеуі де `12` жазады — бір like жоғалады. `UPDATE … SET likes = likes + 1` дерекқорға жіберілсе, жол құлыпталады — екі арттыру да саналады.

**Неліктен `SELECT` тексерусіз `commit()` кейін `IntegrityError` ұсталады?**
`SELECT` тексеруінде race condition бар — тексеру мен INSERT арасында басқа сұраныс бір мәнді кірістіре алады. Операцияны жасап, бас тартуды өңдеу қауіпсізірек.

---

## Эксперимент Журналы

| № | Эксперимент | Не болды | Себебі | Шешімі |
|---|-------------|----------|--------|--------|
| 1 | `naming_convention`-да `uq` шаблонын өзгерттім | `check_models.py` айырмашылық көрсетті: модельде `students_email_unique`, DB-да `students_email_key` | Шаблон PostgreSQL таңдаған атаудан өзгеше нәтиже берді | `%(table_name)s_%(column_0_N_name)s_key` қалпына келтірдім |
| 2 | `StudentIn`-нан `min_length=2` өшірдім, `N` атымен жібердім | `500 Internal Server Error`; логта: `students_name_check` constraint бұзылды | Pydantic тоқтатмады; DB CHECK іске тұсті, бірақ атауы `CONSTRAINT_ERRORS`-та жоқ → 500 | `Field(min_length=2)` қалпына келтірдім |
| 3 | `CONSTRAINT_ERRORS` кілтінде typo: `students_email_uniq` | `409` орнына `500` шықты; логта нақты атау `students_email_key` | Сөздік іздеуі сәтсіз → белгісіз бұзылу → 500 | Кілтті `students_email_key`-ге түзеттім |
| 4 | psql-де `ALTER TABLE courses ALTER COLUMN title DROP NOT NULL` жасадым | `alembic check` сәтсіз: `modify_nullable on courses.title` | Модель NOT NULL дейді, дерекқор nullable дейді — сәйкессіздік | `ALTER COLUMN title SET NOT NULL` жасадым |
| 5 | 0002-де бірден `nullable=False` қойдым | `IntegrityError: NotNullViolation — column "level" contains null values` | Бос емес кестеге default мәнсіз NOT NULL баған қосу мүмкін емес | 3 қадамды миграцияға қайта жаздым |
| 6 | `alembic/env.py`-дан `import models` өшірдім | Миграция барлық 3 кесте үшін `DROP TABLE` ұсынды | `Base.metadata` бос болды → Alembic барлық кестені "артық" деп санады | `0003_oops.py` жойдым, `import models` қалпына келтірдім |
| 7 | `Student`-қа миграциясыз `phone: Mapped[str \| None]` қостым | `alembic check` сәтсіз: `Detected added column 'students.phone'` | Модель дерекқордан алда — айырмашылық | `phone` өрісін алып тастадым |
| 8 | `0002`-ден тарамдалған екі миграция жасадым (0003 және 0004) | `alembic upgrade head` сәтсіз: `Multiple head revisions are present` | Алembic бір head күтеді, екі тәуелсіз тармақ бар | `alembic merge heads` → `0005`; эксперимент файлдарын жойдым |

---

## 0002 Миграциясының Өзін-өзі Тексеруі

| Нені тексеру | Нәтиже |
|--------------|--------|
| Мақсат және қадамдар | ✅ `courses` кестесіне `level TEXT NOT NULL` қосу. Үш қадам, әрқайсысының жеке жауапкершілігі бар. |
| Деректер | ✅ Бар 6 жол толтырылды: `is_elective=true` → `beginner`, қалғандары → `intermediate`. Деректер жоғалмады. |
| Атауын өзгерту және жою | ✅ Upgrade-та атауын өзгерту немесе жою жоқ. Downgrade бағанды жояды — деректер жоғалады (тренингтік DB үшін қолайлы). |
| Кері қайтару | ✅ `downgrade()` бағанды жояды. Тестіленді: downgrade → баған жоғалды, upgrade → баған дұрыс мәндермен қалпына келді. |
| Тексеру | ✅ `--sql` шығысы тексерілді. `alembic check` таза. upgrade → downgrade → upgrade цикл өтті. |
| Тарих | ✅ Жалғыз head: `alembic heads` → `0002 (head)`. Миграция модель және схема өзгерістерімен бірге commit жасалды. |
| Қолдану | ✅ `CourseOut` және `seed.sql` `level`-мен жаңартылды. `GET /courses?level=beginner` 2 курс қайтарады. |

---

## Бастапқы Деректерге Қайтару

```bash
psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql
```

> ⚠️ `TRUNCATE` барлық деректерді өшіреді. Тек тренингтік дерекқорлар үшін.
