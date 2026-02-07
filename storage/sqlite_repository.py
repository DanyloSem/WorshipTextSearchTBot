"""Репозиторій пісень на SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from logs.log_config import logger


class SQLiteSongRepository:
    """
    Реалізація репозиторію пісень на SQLite.

    Схема: songs (id, title, lyrics, updated_at, created_at);
    sync_meta (key, value) — час останньої синхронізації з API.
    """

    TABLE_NAME = 'songs'
    SYNC_META_TABLE = 'sync_meta'
    SYNC_META_KEY_LAST = 'last_synced_at'

    def __init__(self, db_path: str) -> None:
        """
        Args:
            db_path: Шлях до файлу БД (наприклад, data/songs.db).
        """
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.debug('[STORAGE] SQLiteSongRepository ініціалізовано: path=%s', self._path)

    def _get_connection(self) -> sqlite3.Connection:
        """Повертає з’єднання з БД."""
        return sqlite3.connect(self._path, check_same_thread=False)

    def _init_schema(self) -> None:
        """Створює таблиці songs та sync_meta якщо їх немає."""
        with self._get_connection() as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS songs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    lyrics TEXT,
                    updated_at TEXT,
                    created_at TEXT
                )
                ''',
            )
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS sync_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                ''',
            )
            conn.commit()
        logger.debug('[STORAGE] Схема перевірена/створена')

    def get_by_id(self, song_id: str) -> dict | None:
        """
        Повертає один запис пісні за ідентифікатором.

        Args:
            song_id: Ідентифікатор пісні (PCO id).

        Returns:
            Словник {id, title, lyrics} або None.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT id, title, lyrics FROM songs WHERE id = ?',
                (song_id,),
            ).fetchone()
        if row is None:
            return None
        return {'id': row['id'], 'title': row['title'], 'lyrics': row['lyrics'] or ''}

    def get_all(self) -> dict:
        """
        Повертає всі пісні у форматі {song_id: {title: lyrics}}.

        Returns:
            Словник для fuzzy-пошуку та інлайн/чат.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('SELECT id, title, lyrics FROM songs ORDER BY title').fetchall()
        result: dict = {}
        for row in rows:
            song_id = row['id']
            title = row['title'] or ''
            lyrics = row['lyrics'] or ''
            result[song_id] = {title: lyrics}
        logger.debug('[STORAGE] get_all: пісень=%s', len(result))
        return result

    def upsert_songs(self, songs: list[dict]) -> None:
        """
        Записує або оновлює записи пісень (INSERT OR REPLACE).

        Args:
            songs: Список словників з полями id, title, lyrics, опційно updated_at, created_at.
        """
        if not songs:
            logger.debug('[STORAGE] upsert_songs: порожній список, пропуск')
            return
        with self._get_connection() as conn:
            conn.executemany(
                '''
                INSERT OR REPLACE INTO songs (id, title, lyrics, updated_at, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''',
                [
                    (
                        s['id'],
                        s.get('title', ''),
                        s.get('lyrics', ''),
                        s.get('updated_at'),
                        s.get('created_at'),
                    )
                    for s in songs
                ],
            )
            conn.commit()
        logger.info('[STORAGE] upsert_songs: записано записів=%s', len(songs))

    def delete_song(self, song_id: str) -> None:
        """
        Видаляє пісню за ідентифікатором.

        Args:
            song_id: Ідентифікатор пісні (PCO id).
        """
        with self._get_connection() as conn:
            conn.execute('DELETE FROM songs WHERE id = ?', (song_id,))
            conn.commit()
        logger.info('[STORAGE] delete_song: видалено song_id=%s', song_id)

    def get_last_synced_at(self) -> datetime | None:
        """
        Повертає час останньої синхронізації БД з API (UTC).

        Returns:
            UTC datetime останньої синхронізації або None, якщо ще не було.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT value FROM sync_meta WHERE key = ?',
                (self.SYNC_META_KEY_LAST,),
            ).fetchone()
        if row is None:
            return None
        try:
            return datetime.fromisoformat(row[0].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

    def set_last_synced_at(self, dt: datetime) -> None:
        """
        Зберігає час останньої синхронізації БД з API.

        Args:
            dt: UTC datetime синхронізації.
        """
        value = dt.isoformat()
        with self._get_connection() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO sync_meta (key, value) VALUES (?, ?)',
                (self.SYNC_META_KEY_LAST, value),
            )
            conn.commit()
        logger.debug('[STORAGE] set_last_synced_at: %s', value)
