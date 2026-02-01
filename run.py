import asyncio

from aiogram import Bot, Dispatcher

from bot.handlers import create_router
from config import load_config


async def main() -> None:
    """Запускає бота в режимі polling з інжекцією залежностей."""
    config = load_config()
    router = create_router(config=config)
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot closed')
