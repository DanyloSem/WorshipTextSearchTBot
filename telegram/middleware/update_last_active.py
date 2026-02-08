"""Middleware: оновлення last_active_at при кожній події (тільки для не заблокованих)."""

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update

from telegram.get_user_id import get_user_id_from_update

from storage.user_repository import UserRepository


class UpdateLastActiveMiddleware(BaseMiddleware):
    """
    Викликає user_repository.touch_last_active(user_id, now_iso) для кожної події.

    Працює після BlockedCheckMiddleware, тому доходить лише для не заблокованих.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self._user_repository = user_repository

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        """
        Оновлює last_active_at та передає подію далі.
        """
        user_id = get_user_id_from_update(event)
        if user_id is not None:
            now_iso = datetime.now(timezone.utc).isoformat()
            self._user_repository.touch_last_active(user_id, now_iso)
        return await handler(event, data)
