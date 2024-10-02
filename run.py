
import asyncio
from config import TELEGRAM_TOKEN
# from aiohttp import web
from aiogram import Bot, Dispatcher
# from webhook import create_app
from bot.handlers import router



async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

    # app = create_app(bot, dp)

    # runner = web.AppRunner(app)
    # await runner.setup()
    # site = web.TCPSite(runner, '0.0.0.0', int(os.getenv('PORT', 8080)))
    # await site.start()

    # print(f"Bot is running on {os.getenv('WEBHOOK_URL')}")
    # await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Bot closed')
