"""Пакет обробників бота. Збирає роутер з усіх під-роутерів та інжектує залежності."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

from logs.log_config import logger
from lyrics.fuzzy_search import FuzzySearchService
from lyrics.inline_search import InlineSearch
from lyrics.provider import SongsDataProvider
from telegram.handlers.inline import get_inline_router
from telegram.handlers.pagination import get_pagination_router
from telegram.handlers.search import get_search_router
from telegram.handlers.song import get_song_router
from telegram.handlers.start import get_start_router

if TYPE_CHECKING:
    from storage.repository import SongRepository


def create_router(
    repository: 'SongRepository',
    fuzzy_search_service: FuzzySearchService | None = None,
    inline_search: InlineSearch | None = None,
) -> Router:
    """
    Створює головний роутер з підключеними обробниками та залежностями.

    Усі пошуки працюють з локальною базою (репозиторій); PCO не викликається в обробниках.

    Args:
        repository: Репозиторій пісень (SQLite).
        fuzzy_search_service: Сервіс fuzzy-пошуку; якщо None — створюється внутрішньо.
        inline_search: Сервіс інлайн-пошуку; якщо None — створюється з провайдера та fuzzy.

    Returns:
        Router з усіма обробниками.
    """
    fuzzy = fuzzy_search_service or FuzzySearchService()
    provider = SongsDataProvider(repository)
    inlinesearch = inline_search or InlineSearch(provider, fuzzy)
    logger.debug(
        'Роутер: репозиторій, FuzzySearch, InlineSearch=%s',
        'інжектовано' if inline_search else 'створено',
    )

    router = Router()
    router.include_router(get_start_router())
    router.include_router(get_song_router(repository))
    router.include_router(get_search_router(fuzzy, repository))
    router.include_router(get_inline_router(inlinesearch))
    router.include_router(get_pagination_router())

    return router
