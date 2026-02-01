"""Точка входу: запуск бота в режимі polling."""

import asyncio

# Логування має налаштовуватись до імпорту aiogram, інакше basicConfig() нічого не зробить
from logs.log_config import logger

from aiogram import Bot, Dispatcher

from config import load_config
from lyrics.inline_search import InlineSearch
from lyrics.provider import SongsDataProvider
from planning_center.song_search import SongSearchService
from telegram.handlers import create_router


async def main() -> None:
    """Запускає бота в режимі polling з інжекцією залежностей."""
    logger.info('Завантаження конфігурації')
    config = load_config()
    logger.info(
        'Конфіг завантажено: songs_data_path=%s, webhook_url=%s',
        config.songs_data_path,
        config.webhook_url,
    )
    logger.info('Створення SongSearchService (PCO API)')
    song_search_service = SongSearchService(config)
    logger.info('Створення SongsDataProvider: path=%s', config.songs_data_path)
    provider = SongsDataProvider(config.songs_data_path)
    logger.info('Створення InlineSearch')
    inline_search = InlineSearch(provider)
    logger.info('Збирання роутера з обробниками')
    router = create_router(
        song_search_service=song_search_service,
        inline_search=inline_search,
    )
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()
    dp.include_router(router)
    logger.info('Webhook скинуто, запуск polling')
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot closed')
