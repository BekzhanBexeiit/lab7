"""
Дерекқормен байланысты тексереді.
Іске қосу: python check_db.py
Күтілетін нәтиже: connected to course_catalog as catalog_app, PostgreSQL ...
"""
from sqlalchemy import text

from db import engine

with engine.connect() as conn:
    # Дерекқор аты мен пайдаланушы атын сұраймыз
    name, user = conn.execute(text("SELECT current_database(), current_user")).one()
    # PostgreSQL нұсқасы
    version = conn.execute(text("SHOW server_version")).scalar_one()

print(f"connected to {name} as {user}, PostgreSQL {version}")
