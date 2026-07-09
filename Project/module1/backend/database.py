from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite

STORAGE_DIR = Path(__file__).parent / "storage"
DB_PATH = STORAGE_DIR / "profile.db"
RESUME_DIR = STORAGE_DIR / "resumes"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profile_fields (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
"""


async def init_db() -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_SCHEMA)
        await db.commit()


async def get_profile() -> dict[str, str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT key, value FROM profile_fields")
        rows = await cursor.fetchall()
        return {key: value for key, value in rows}


async def get_profile_value(key: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM profile_fields WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else None


async def upsert_profile_fields(data: dict[str, str]) -> None:
    if not data:
        return
    now = datetime.now(timezone.utc).isoformat()
    rows = [(key, value, now) for key, value in data.items()]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """
            INSERT INTO profile_fields (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            rows,
        )
        await db.commit()


async def delete_profile_field(key: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM profile_fields WHERE key = ?", (key,))
        await db.commit()
