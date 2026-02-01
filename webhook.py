import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update

async def handle(request):
    bot = request.app['bot']
    dp = request.app['dp']
    update_dict = await request.json()
    update = Update(**update_dict)
    await dp.feed_update(bot, update)
    return web.Response()

async def on_startup(app):
    bot = app['bot']
    webhook_url = os.getenv('WEBHOOK_URL')
    await bot.set_webhook(webhook_url)

async def on_shutdown(app):
    bot = app['bot']
    await bot.delete_webhook()

def create_app(bot: Bot, dp: Dispatcher):
    app = web.Application()
    app['bot'] = bot
    app['dp'] = dp
    app.router.add_post('/webhook', handle)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    return app