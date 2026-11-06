-- seed.sql: бастапқы деректер
-- ЕСКЕРТУ: TRUNCATE барлық деректерді өшіреді! Тек тренингтік DB үшін.
-- Іске қосу: psql -h localhost -U catalog_app -d course_catalog -v ON_ERROR_STOP=1 -f seed.sql

-- Кесте тазалау (тәуелділік тәртібімен: enrollments → students, courses)
-- RESTART IDENTITY — id санауыштарын 1-ден бастайды
TRUNCATE enrollments, students, courses RESTART IDENTITY;

-- ── Курстар (level бағаны қосылған — migration 0002) ─────────────────────────
INSERT INTO courses (id, title, description, credits, is_elective, likes, level) VALUES
  ('modern-frontend',
   'Modern Frontend: React & Next.js',
   'React 19, Server Components, and the App Router.',
   5, false, 24, 'intermediate'),

  ('backend-fastapi',
   'Backend Development: FastAPI',
   'Async REST APIs in Python with FastAPI and Pydantic.',
   5, false, 21, 'intermediate'),

  ('ai-integration',
   'AI/LLM Integration',
   'LLM features in an app via the OpenAI API.',
   5, true, 32, 'beginner'),

  ('api-design',
   'API Design: REST vs GraphQL',
   'Comparing REST and GraphQL in one hands-on project.',
   4, true, 11, 'beginner'),

  ('databases-postgresql',
   'Relational Databases: PostgreSQL',
   'Schemas, SQLAlchemy, and migrations with Alembic.',
   5, false, 15, 'intermediate'),

  ('web-security',
   'Web Security Fundamentals',
   'OWASP Top 10, auth, and secure coding practices.',
   4, false, 19, 'intermediate');

-- ── Студенттер ────────────────────────────────────────────────────────────────
INSERT INTO students (name, email) VALUES
  ('Aigerim Sadykova', 'aigerim@example.com'),
  ('Bekzat Nurlanов',  'bekzat@example.com'),
  ('Dana Seitkali',    'dana@example.com');

-- ── Тіркелулер ────────────────────────────────────────────────────────────────
INSERT INTO enrollments (course_id, student_id) VALUES
  ('modern-frontend',    1),
  ('ai-integration',     1),
  ('ai-integration',     2),
  ('backend-fastapi',    2),
  ('modern-frontend',    3),
  ('ai-integration',     3);
