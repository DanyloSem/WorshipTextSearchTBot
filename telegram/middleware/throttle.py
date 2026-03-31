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

THROTTLE_MESSAGE = (
    'Забагато кліків. Зачекай трохи і спробуй ще раз 😉'
)
WARNING_COOLDOWN_SECONDS = 10.0


class ThrottleMiddleware(BaseMiddleware):
    """
    Обмежує кількість оновлень на user_id у ковзному вікні (в памʼяті).

    При перевищенні ліміту handler не викликається; опційно відправляється повідомлення.
    Саме попередження надсилається не частіше раз на WARNING_COOLDOWN_SECONDS на користувача.
    """

    def __init__(
        self,
        rate_limit: int = 1,
        window_seconds: float = 0.5,
        bot: 'Bot | None' = None,
        warning_cooldown_seconds: float = WARNING_COOLDOWN_SECONDS,
    ) -> None:
        self._rate_limit = rate_limit
        self._window_seconds = window_seconds
        self._bot = bot
        self._warning_cooldown = warning_cooldown_seconds
        self._timestamps: dict[int, list[float]] = defaultdict(list)
        self._last_warning_at: dict[int, float] = {}

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
            last = self._last_warning_at.get(user_id, 0.0)
            if now - last >= self._warning_cooldown:
                bot = self._bot or data.get('bot')
                chat_id = get_chat_id_from_update(event)
                if bot and chat_id is not None:
                    try:
                        await bot.send_message(chat_id=chat_id, text=THROTTLE_MESSAGE)
                        self._last_warning_at[user_id] = now
                    except Exception:
                        logger.exception('[THROTTLE] Не вдалося відправити повідомлення')
            return None

        timestamps.append(now)
        return await handler(event, data)
