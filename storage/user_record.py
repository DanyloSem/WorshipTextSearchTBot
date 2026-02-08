"""Модель запису користувача в БД."""

from dataclasses import dataclass


@dataclass
class UserRecord:
    """
    Запис користувача з таблиці users.

    Атрибути:
        user_id: Telegram user id.
        username: Username (nullable).
        first_name: Ім'я (nullable).
        last_name: Прізвище (nullable).
        phone: Номер телефону (nullable).
        is_admin: Чи є адміністратором.
        is_blocked: Чи заблокований.
        blocked_at: ISO-час блокування (nullable).
        last_active_at: ISO-час останньої активності.
    """

    user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    phone: str | None
    is_admin: bool
    is_blocked: bool
    blocked_at: str | None
    last_active_at: str
