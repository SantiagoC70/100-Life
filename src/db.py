"""Persistencia SQLite local, aislada por usuario."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def database_path() -> Path:
    return Path(os.environ.get("LIFE_DB_PATH", "data/life.db"))


@contextmanager
def connect(path: str | Path | None = None):
    target = Path(path) if path else database_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(target)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
 password_hash TEXT NOT NULL, password_salt TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profiles (
 user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 student_type TEXT NOT NULL CHECK(student_type IN ('general','atleta')),
 study_preference TEXT NOT NULL, sleep_start TEXT NOT NULL, sleep_end TEXT NOT NULL,
 dietary_preferences TEXT NOT NULL DEFAULT '', dietary_restrictions TEXT NOT NULL DEFAULT '',
 water_goal_ml INTEGER NOT NULL DEFAULT 2000 CHECK(water_goal_ml BETWEEN 250 AND 10000)
);
CREATE TABLE IF NOT EXISTS activities (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 kind TEXT NOT NULL CHECK(kind IN ('clase','tarea','examen','entrenamiento','personal','estudio')),
 title TEXT NOT NULL, starts_at TEXT NOT NULL, ends_at TEXT NOT NULL,
 priority INTEGER NOT NULL DEFAULT 2 CHECK(priority BETWEEN 1 AND 3), deadline TEXT,
 completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)), notes TEXT NOT NULL DEFAULT '',
 perceived_intensity INTEGER CHECK(perceived_intensity BETWEEN 1 AND 5),
 fatigue INTEGER CHECK(fatigue BETWEEN 1 AND 5), pain INTEGER NOT NULL DEFAULT 0 CHECK(pain IN (0,1)),
 CHECK(ends_at > starts_at)
);
CREATE INDEX IF NOT EXISTS idx_activities_user_time ON activities(user_id, starts_at, ends_at);
CREATE TABLE IF NOT EXISTS hydration (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 consumed_at TEXT NOT NULL, amount_ml INTEGER NOT NULL CHECK(amount_ml BETWEEN 1 AND 5000)
);
CREATE INDEX IF NOT EXISTS idx_hydration_user_time ON hydration(user_id, consumed_at);
"""


def init_db(path: str | Path | None = None) -> None:
    with connect(path) as db:
        db.executescript(SCHEMA)
