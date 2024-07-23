import os
import logging
import asyncio
from dotenv import load_dotenv
from aiohttp import web  # Додано імпорт web з aiohttp
from aiogram import Bot, Dispatcher
from webhook import create_app
from bot.handlers import router

async def main():
    #load_dotenv()
    bot = Bot(token=os.getenv('TOKEN'))
    dp = Dispatcher()
    dp.include_router(router)

    app = create_app(bot, dp)

    runner = web.AppRunner(app)  # Тут використовується web
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
    await site.start()

    print(f"Bot is running on {os.getenv('WEBHOOK_URL')}")
    await asyncio.Event().wait()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot closed')
