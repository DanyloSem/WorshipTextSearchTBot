"""Точка входу: запуск бота в режимі polling."""

import asyncio
import os

from dotenv import load_dotenv

_run_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_run_dir, '.env')
if os.path.isfile(_env_path):
    load_dotenv(_env_path)
else:
    load_dotenv()

# Логування має налаштовуватись до імпорту aiogram, інакше basicConfig() нічого не зробить
from aiohttp import web
from logs.log_config import apply_log_level, logger

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramUnauthorizedError

from config import load_config
from lyrics.fuzzy_search import FuzzySearchService
from planning_center.song_search import SongSearchService
from storage.sqlite_repository import SQLiteSongRepository
from sync import run_once as sync_run_once
from sync.scheduler import start_scheduler
from telegram.handlers import create_router
from webhook import create_pco_only_app


async def _run_pco_webhook_server(pco_app: web.Application, port: int) -> None:
    """Запускає aiohttp-сервер для PCO webhooks у фоні; при скасуванні задачі виконує cleanup."""
    runner = web.AppRunner(pco_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info('PCO webhook сервер слухає на порту %s', port)
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()


async def main() -> None:
    """Запускає бота в режимі polling з інжекцією залежностей та PCO webhook у фоні."""
    logger.info('Завантаження конфігурації')
    config = load_config()
    apply_log_level(config.log_level)
    logger.info(
        'Конфіг завантажено: songs_data_path=%s, data_path=%s, webhook_url=%s, log_level=%s',
        config.songs_data_path,
        config.data_path,
        config.webhook_url,
        config.log_level,
    )
    repository = SQLiteSongRepository(config.data_path)
    pco_client = SongSearchService(config)
    logger.info('Синхронізація з PCO при старті')
    await sync_run_once(pco_client, repository)
    start_scheduler(pco_client, repository)

    pco_app = create_pco_only_app(
        pco_client,
        repository,
        config.pco_webhook_authenticity_secret,
    )
    pco_task = asyncio.create_task(_run_pco_webhook_server(pco_app, config.port))

    fuzzy_search_service = FuzzySearchService()
    logger.info('Збирання роутера з обробниками (локальна БД + fuzzy-пошук)')
    router = create_router(
        repository=repository,
        fuzzy_search_service=fuzzy_search_service,
    )
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()
    dp.include_router(router)
    logger.info('Webhook скинуто, запуск polling')
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except TelegramUnauthorizedError:
        logger.error(
            '[BOT] TELEGRAM_TOKEN невалідний або відкликаний. '
            'Перевірте .env та отримайте новий токен у @BotFather.',
        )
        raise
    finally:
        pco_task.cancel()
        try:
            await pco_task
        except asyncio.CancelledError:
            pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot closed')
