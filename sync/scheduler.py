"""Планувальник синхронізації: запуск о 03:00, 06:00, 09:00, 12:00."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from logs.log_config import logger
from planning_center.song_search import SongSearchService

from sync.song_sync import run_once

if TYPE_CHECKING:
    from storage.repository import SongRepository

_SCHEDULED_HOURS = (0, 3, 6, 9, 12, 15, 18, 21)


def _seconds_until_next_run() -> float:
    """Повертає кількість секунд до наступної години з набору 0, 3, 6, 9, 12, 15, 18, 21."""
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    for h in _SCHEDULED_HOURS:
        if current_hour < h:
            next_run = now.replace(hour=h, minute=0, second=0, microsecond=0)
            return (next_run - now).total_seconds()
    next_run = now.replace(hour=_SCHEDULED_HOURS[0], minute=0, second=0, microsecond=0)
    next_run += timedelta(days=1)
    return (next_run - now).total_seconds()


async def _scheduler_loop(
    pco_client: SongSearchService,
    repository: 'SongRepository',
) -> None:
    """Цикл: sleep до наступної години 0/3/6/9/12/15/18/21, виклик run_once, повтор."""
    while True:
        delay = _seconds_until_next_run()
        logger.info('[SCHEDULER] Наступний запуск синхронізації через %.0f с (години 0, 3, 6, 9, 12, 15, 18, 21)', delay)
        await asyncio.sleep(delay)
        try:
            await run_once(pco_client, repository)
        except Exception:
            logger.exception('[SCHEDULER] Помилка синхронізації за розкладом')


def start_scheduler(
    pco_client: SongSearchService,
    repository: 'SongRepository',
) -> asyncio.Task:
    """
    Запускає фонову задачу синхронізації за розкладом "оновлення кожні три години".

    Args:
        pco_client: Клієнт PCO API.
        repository: Репозиторій пісень.

    Returns:
        asyncio.Task фонової задачі.
    """
    task = asyncio.create_task(_scheduler_loop(pco_client, repository))
    logger.info('[SCHEDULER] Планувальник синхронізації (0/3/6/9/12/15/18/21) запущено')
    return task
