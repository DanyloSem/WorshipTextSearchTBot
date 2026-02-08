"""Точка входу: запуск бота в режимі webhook (aiohttp) з ендпоінтом POST /pco-webhook."""

import asyncio
import os

from aiohttp import web
from dotenv import load_dotenv

_run_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_run_dir, '.env')
if os.path.isfile(_env_path):
    load_dotenv(_env_path)
else:
    load_dotenv()

from logs.log_config import apply_log_level, logger

from aiogram import Bot, Dispatcher
from config import load_config
from lyrics.fuzzy_search import FuzzySearchService
from planning_center.song_search import SongSearchService
from storage.sqlite_repository import SQLiteSongRepository
from storage.user_repository import UserRepository
from sync import run_once as sync_run_once
from sync.scheduler import start_scheduler
from telegram.handlers import create_router
from telegram.middleware import (
    BlockedCheckMiddleware,
    ThrottleMiddleware,
    UpdateLastActiveMiddleware,
)
from webhook import create_app


def main() -> None:
    """Збирає aiohttp Application з PCO webhook та запускає сервер."""
    logger.info('Завантаження конфігурації (webhook-режим)')
    config = load_config()
    apply_log_level(config.log_level)
    logger.info(
        'Конфіг завантажено: data_path=%s, port=%s',
        config.data_path,
        config.port,
    )
    repository = SQLiteSongRepository(config.data_path)
    user_repository = UserRepository(config.data_path)
    pco_client = SongSearchService(config)

    async def startup_sync_and_scheduler(app: web.Application) -> None:
        logger.info('Синхронізація з PCO при старті')
        await sync_run_once(pco_client, repository)
        start_scheduler(pco_client, repository)

    fuzzy_search_service = FuzzySearchService()
    router = create_router(
        repository=repository,
        fuzzy_search_service=fuzzy_search_service,
        telegram_admins=config.telegram_admins,
        user_repository=user_repository,
    )
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()
    dp.update.middleware(BlockedCheckMiddleware(user_repository))
    dp.update.middleware(UpdateLastActiveMiddleware(user_repository))
    dp.update.middleware(
        ThrottleMiddleware(
            rate_limit=5,
            window_seconds=20.0,
            bot=bot,
        ),
    )
    dp.include_router(router)

    app = create_app(bot, dp, pco_client=pco_client, repository=repository)
    app.on_startup.append(startup_sync_and_scheduler)

    logger.info('Запуск webhook-сервера на порту %s', config.port)
    web.run_app(app, port=config.port)


if __name__ == '__main__':
    main()
