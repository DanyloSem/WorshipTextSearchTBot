"""Middleware: обмеження кількості оновлень на користувача (ковзне вікно)."""

import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Update

from logs.log_config import logger
from telegram.get_user_id import get_chat_id_from_update, get_user_id_from_update

if TYPE_CHECKING:
    from aiogram import Bot

THROTTLE_MESSAGE = 'Забагато запитів, почекайте %s с.'


class ThrottleMiddleware(BaseMiddleware):
    """
    Обмежує кількість оновлень на user_id у ковзному вікні (в памʼяті).

    При перевищенні ліміту handler не викликається; опційно відправляється повідомлення.
    """

    def __init__(
        self,
        rate_limit: int = 10,
        window_seconds: float = 20.0,
        bot: 'Bot | None' = None,
    ) -> None:
        self._rate_limit = rate_limit
        self._window_seconds = window_seconds
        self._bot = bot
        self._timestamps: dict[int, list[float]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: dict[str, Any],
    ) -> Any:
        """
        Перевіряє кількість подій у вікні; при перевищенні — не викликає handler, опційно відповідь.
        """
        user_id = get_user_id_from_update(event)
        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()
        timestamps = self._timestamps[user_id]
        cutoff = now - self._window_seconds
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= self._rate_limit:
            logger.warning(
                '[THROTTLE] Перевищено ліміт: user_id=%s, count=%s',
                user_id,
                len(timestamps),
            )
            bot = self._bot or data.get('bot')
            chat_id = get_chat_id_from_update(event)
            if bot and chat_id is not None and timestamps:
                wait_sec = max(1, int(self._window_seconds - (now - timestamps[0])))
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=THROTTLE_MESSAGE % wait_sec,
                    )
                except Exception:
                    logger.exception('[THROTTLE] Не вдалося відправити повідомлення')
            return None

        timestamps.append(now)
        return await handler(event, data)
