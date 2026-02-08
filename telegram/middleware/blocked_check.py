"""Middleware: ігнорування оновлень від заблокованих користувачів."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update

from telegram.get_user_id import get_user_id_from_update

from storage.user_repository import UserRepository


class BlockedCheckMiddleware(BaseMiddleware):
    """
    Якщо користувач заблокований (UserRepository.is_blocked), handler не викликається.
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
        Перевіряє is_blocked; якщо так — не викликає handler.
        """
        user_id = get_user_id_from_update(event)
        if user_id is None:
            return await handler(event, data)
        if self._user_repository.is_blocked(user_id):
            return None
        return await handler(event, data)
