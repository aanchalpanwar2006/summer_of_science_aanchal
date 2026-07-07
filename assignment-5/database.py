from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent / "tasks.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_profile (
    id          INTEGER PRIMARY KEY,
    name        TEXT,
    email       TEXT,
    phone       TEXT,
    address     TEXT,
    resume_text TEXT
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_SCHEMA)
        await db.commit()


async def get_profile() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM user_profile WHERE id = 1")
        row = await cursor.fetchone()
        if row is None:
            return {}
        return dict(row)


async def upsert_profile(data: dict) -> None:
    data["id"] = 1
    columns = ", ".join(data.keys())
    placeholders = ", ".join(f":{k}" for k in data.keys())
    sql = f"INSERT OR REPLACE INTO user_profile ({columns}) VALUES ({placeholders})"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(sql, data)
        await db.commit()
