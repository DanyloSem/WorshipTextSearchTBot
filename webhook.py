import os
from aiohttp import web  # Переконайтеся, що імпортовано web з aiohttp
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

# curl -F "url=https://expert-garbanzo-pjr9qqj976qw36jgq-8080.app.github.dev/webhook" https://api.telegram.org/bot6812047735:AAGrM8maAsy4phXcVcRkJHCYSfzDw9k--Lw/setWebhook
# curl https://api.telegram.org/bot6812047735:AAGrM8maAsy4phXcVcRkJHCYSfzDw9k--Lw/getWebhookInfo
# curl -X POST https://expert-garbanzo-pjr9qqj976qw36jgq-8080.app.github.dev/webhook -d '{"update_id": 1, "message": {"message_id": 1, "from": {"id": 1, "is_bot": false, "first_name": "John", "last_name": "Doe", "username": "johndoe", "language_code": "en"}, "chat": {"id": 1, "first_name": "John", "last_name": "Doe", "username": "johndoe", "type": "private"}, "date": 1615464368, "text": "Hello World!"}}'


