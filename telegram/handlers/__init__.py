"""Пакет обробників бота. Збирає роутер з усіх під-роутерів та інжектує залежності."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

from logs.log_config import logger
from lyrics.inline_search import InlineSearch
from lyrics.provider import SongsDataProvider
from planning_center.song_search import SongSearchService
from telegram.handlers.inline import get_inline_router
from telegram.handlers.pagination import get_pagination_router
from telegram.handlers.search import get_search_router
from telegram.handlers.song import get_song_router
from telegram.handlers.start import get_start_router

if TYPE_CHECKING:
    from config import Config


def create_router(
    song_search_service: SongSearchService | None = None,
    inline_search: InlineSearch | None = None,
    songs_data_path: str = 'songs_data.json',
    config: 'Config | None' = None,
) -> Router:
    """
    Створює головний роутер з підключеними обробниками та залежностями.

    Args:
        song_search_service: Сервіс пошуку пісень по API. Якщо None — створюється з config або env.
        inline_search: Сервіс інлайн-пошуку. Якщо None — створюється з провайдера.
        songs_data_path: Шлях до JSON з даними пісень для inline (якщо inline_search None).
        config: Конфігурація для створення сервісів при відсутності song_search_service.

    Returns:
        Router з усіма обробниками.
    """
    if config is not None:
        path = config.songs_data_path
    else:
        path = songs_data_path
    sss = song_search_service or SongSearchService(config)
    logger.debug('PCO SongSearchService: %s', 'інжектовано' if song_search_service else 'створено з config')
    if inline_search is None:
        provider = SongsDataProvider(path)
        inlinesearch = InlineSearch(provider)
        logger.debug('InlineSearch створено з провайдером, path=%s', path)
    else:
        inlinesearch = inline_search
        logger.debug('InlineSearch інжектовано')

    router = Router()
    router.include_router(get_start_router())
    router.include_router(get_search_router(sss))
    router.include_router(get_song_router(sss))
    router.include_router(get_inline_router(inlinesearch))
    router.include_router(get_pagination_router())

    return router
