from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import aiosqlite

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cache_entries (
  key TEXT PRIMARY KEY,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  source_status TEXT NOT NULL
);
"""


class SQLiteCache:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)

    async def init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path.as_posix()) as conn:
            await conn.execute(CREATE_TABLE_SQL)
            await conn.commit()

    async def get(self, key: str) -> tuple[dict[str, object], bool] | None:
        async with aiosqlite.connect(self._db_path.as_posix()) as conn:
            cursor = await conn.execute(
                "SELECT payload, expires_at FROM cache_entries WHERE key = ?",
                (key,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None

        payload_text, expires_at_text = row
        payload = __import__("json").loads(payload_text)
        expires_at = datetime.fromisoformat(expires_at_text)
        is_expired = datetime.now(UTC) > expires_at
        return payload, is_expired

    async def set(
        self, key: str, payload: dict[str, object], ttl_seconds: int, source_status: str
    ) -> None:
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl_seconds)
        payload_text = __import__("json").dumps(payload, ensure_ascii=False)
        async with aiosqlite.connect(self._db_path.as_posix()) as conn:
            await conn.execute(
                """
                INSERT INTO cache_entries (key, payload, updated_at, expires_at, source_status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                  payload = excluded.payload,
                  updated_at = excluded.updated_at,
                  expires_at = excluded.expires_at,
                  source_status = excluded.source_status
                """,
                (
                    key,
                    payload_text,
                    now.isoformat(),
                    expires_at.isoformat(),
                    source_status,
                ),
            )
            await conn.commit()

    async def delete(self, key: str) -> None:
        async with aiosqlite.connect(self._db_path.as_posix()) as conn:
            await conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            await conn.commit()
