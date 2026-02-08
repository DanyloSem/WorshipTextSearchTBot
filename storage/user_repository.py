"""Репозиторій користувачів бота в SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from logs.log_config import logger

from storage.user_record import UserRecord


class UserRepository:
    """
    Репозиторій користувачів бота (таблиця users у тому ж SQLite, що й пісні).

    Схема: user_id, username, first_name, last_name, phone, is_admin, is_blocked,
    blocked_at, last_active_at, created_at.
    """

    TABLE_NAME = 'users'

    def __init__(self, db_path: str) -> None:
        """
        Args:
            db_path: Шлях до файлу БД (наприклад, data/songs.db).
        """
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.debug('[STORAGE] UserRepository ініціалізовано: path=%s', self._path)

    def _get_connection(self) -> sqlite3.Connection:
        """Повертає з'єднання з БД."""
        return sqlite3.connect(self._path, check_same_thread=False)

    def _init_schema(self) -> None:
        """Створює таблицю users, якщо її немає."""
        with self._get_connection() as conn:
            conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    is_admin INTEGER NOT NULL DEFAULT 0,
                    is_blocked INTEGER NOT NULL DEFAULT 0,
                    blocked_at TEXT,
                    last_active_at TEXT NOT NULL,
                    created_at TEXT
                )
                ''',
            )
            conn.commit()
        logger.debug('[STORAGE] Схема users перевірена/створена')

    def upsert_from_telegram_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        phone: str | None,
        is_admin: bool,
        now_iso: str,
    ) -> None:
        """
        Вставляє або оновлює запис після /start.

        Оновлює всі поля з Telegram та is_admin, last_active_at.
        Якщо is_admin=True, встановлює is_blocked=0.

        Args:
            user_id: Telegram user id.
            username: Username (nullable).
            first_name: Ім'я (nullable).
            last_name: Прізвище (nullable).
            phone: Телефон (nullable).
            is_admin: Чи є адміністратором.
            now_iso: ISO-час для last_active_at та created_at при INSERT.
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT is_blocked FROM users WHERE user_id = ?',
                (user_id,),
            ).fetchone()
            if row is not None:
                # UPDATE: is_blocked=0 тільки якщо is_admin; інакше зберігаємо поточне значення
                new_blocked = 0 if is_admin else row['is_blocked']
                conn.execute(
                    '''
                    UPDATE users SET
                        username = ?, first_name = ?, last_name = ?, phone = ?,
                        is_admin = ?, is_blocked = ?, last_active_at = ?
                    WHERE user_id = ?
                    ''',
                    (username, first_name, last_name, phone, 1 if is_admin else 0, new_blocked, now_iso, user_id),
                )
            else:
                # INSERT: новий користувач завжди is_blocked=0
                conn.execute(
                    '''
                    INSERT INTO users (
                        user_id, username, first_name, last_name, phone,
                        is_admin, is_blocked, blocked_at, last_active_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, NULL, ?, ?)
                    ''',
                    (
                        user_id,
                        username,
                        first_name,
                        last_name,
                        phone,
                        1 if is_admin else 0,
                        now_iso,
                        now_iso,
                    ),
                )
            conn.commit()
        logger.debug('[STORAGE] upsert_from_telegram_user: user_id=%s, is_admin=%s', user_id, is_admin)

    def touch_last_active(self, user_id: int, now_iso: str) -> None:
        """
        Оновлює тільки last_active_at для існуючого запису.

        Args:
            user_id: Telegram user id.
            now_iso: ISO-час останньої активності.
        """
        with self._get_connection() as conn:
            conn.execute(
                'UPDATE users SET last_active_at = ? WHERE user_id = ?',
                (now_iso, user_id),
            )
            conn.commit()

    def is_blocked(self, user_id: int) -> bool:
        """
        Перевіряє, чи користувач заблокований.

        Args:
            user_id: Telegram user id.

        Returns:
            True, якщо is_blocked=1.
        """
        with self._get_connection() as conn:
            row = conn.execute(
                'SELECT is_blocked FROM users WHERE user_id = ?',
                (user_id,),
            ).fetchone()
        return row is not None and row[0] == 1

    def set_blocked(self, user_id: int, blocked_at_iso: str) -> None:
        """
        Встановлює користувача як заблокованого.

        Викликати лише для не-адмінів (перевірка в хендлері).

        Args:
            user_id: Telegram user id.
            blocked_at_iso: ISO-час блокування.
        """
        with self._get_connection() as conn:
            conn.execute(
                'UPDATE users SET is_blocked = 1, blocked_at = ? WHERE user_id = ?',
                (blocked_at_iso, user_id),
            )
            conn.commit()
        logger.info('[STORAGE] set_blocked: user_id=%s', user_id)

    def set_unblocked(self, user_id: int) -> None:
        """
        Знімає блокування з користувача.

        Args:
            user_id: Telegram user id.
        """
        with self._get_connection() as conn:
            conn.execute(
                'UPDATE users SET is_blocked = 0, blocked_at = NULL WHERE user_id = ?',
                (user_id,),
            )
            conn.commit()
        logger.info('[STORAGE] set_unblocked: user_id=%s', user_id)

    def list_all_ordered_by_last_active(self) -> list[UserRecord]:
        """
        Повертає всіх користувачів, відсортованих за last_active_at DESC.

        Returns:
            Список UserRecord для кнопок «Заблокувати».
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''
                SELECT user_id, username, first_name, last_name, phone,
                       is_admin, is_blocked, blocked_at, last_active_at
                FROM users ORDER BY last_active_at DESC
                '''
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def list_blocked_ordered_by_blocked_at(self) -> list[UserRecord]:
        """
        Повертає заблокованих користувачів, ORDER BY blocked_at DESC.

        Returns:
            Список UserRecord для кнопок «Розблокувати».
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''
                SELECT user_id, username, first_name, last_name, phone,
                       is_admin, is_blocked, blocked_at, last_active_at
                FROM users WHERE is_blocked = 1 ORDER BY blocked_at DESC
                '''
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> UserRecord:
        """Перетворює рядок БД на UserRecord."""
        return UserRecord(
            user_id=row['user_id'],
            username=row['username'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            phone=row['phone'],
            is_admin=bool(row['is_admin']),
            is_blocked=bool(row['is_blocked']),
            blocked_at=row['blocked_at'],
            last_active_at=row['last_active_at'],
        )
