"""Синхронізація пісень з PCO у локальну БД."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from logs.log_config import logger
from planning_center.song_search import SongSearchService

if TYPE_CHECKING:
    from storage.repository import SongRepository


SYNC_SKIP_WINDOW_HOURS = 3


async def run_once(
    pco_client: SongSearchService,
    repository: 'SongRepository',
) -> None:
    """
    Один прохід синхронізації: завантажити всі пісні з PCO і записати в репозиторій.

    Викликається при старті, за розкладом (3/6/9/12) та (пізніше) з webhook.
    Якщо БД вже синхронізована протягом останніх SYNC_SKIP_WINDOW_HOURS годин — повний sync пропускається.

    Args:
        pco_client: Клієнт Planning Center API (тільки для sync).
        repository: Репозиторій пісень (SQLite) для запису.
    """
    now_utc = datetime.now(timezone.utc)
    last_synced = repository.get_last_synced_at()
    if last_synced is not None:
        if last_synced.tzinfo is None:
            last_synced = last_synced.replace(tzinfo=timezone.utc)
        if now_utc - last_synced < timedelta(hours=SYNC_SKIP_WINDOW_HOURS):
            logger.info(
                '[SYNC] Пропуск синхронізації: остання синхронізація %s тому (< %s год)',
                now_utc - last_synced,
                SYNC_SKIP_WINDOW_HOURS,
            )
            return
    logger.info('[SYNC] Запуск синхронізації з PCO')
    try:
        songs = await pco_client.fetch_all_songs_with_lyrics()
        if not songs:
            logger.warning('[SYNC] PCO повернув порожній список пісень')
            return
        repository.upsert_songs(songs)
        repository.set_last_synced_at(now_utc)
        logger.info('[SYNC] Синхронізація завершена: записано пісень=%s', len(songs))
    except Exception:
        logger.exception('[SYNC] Помилка під час синхронізації')
        raise
