"""Фабрика aiohttp-додатку для webhook-режиму бота."""

import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update


class WebhookApp:
    """
    Обгортка aiohttp Application для прийому webhook від Telegram.

    Єдина публічна сутність модуля — фабрика create_app.
    """

    @staticmethod
    async def handle(request: web.Request) -> web.Response:
        """Обробляє POST /webhook: передає Update диспетчеру."""
        bot = request.app['bot']
        dp = request.app['dp']
        update_dict = await request.json()
        update = Update(**update_dict)
        await dp.feed_update(bot, update)
        return web.Response()

    @staticmethod
    async def on_startup(app: web.Application) -> None:
        """Встановлює webhook URL при старті."""
        bot = app['bot']
        webhook_url = os.getenv('WEBHOOK_URL')
        if webhook_url:
            await bot.set_webhook(webhook_url)

    @staticmethod
    async def on_shutdown(app: web.Application) -> None:
        """Видаляє webhook при зупинці."""
        bot = app['bot']
        await bot.delete_webhook()

    @staticmethod
    def create_app(bot: Bot, dp: Dispatcher) -> web.Application:
        """
        Створює aiohttp Application для webhook.

        Args:
            bot: Інстанс Bot.
            dp: Інстанс Dispatcher.

        Returns:
            Налаштований aiohttp.Application.
        """
        app = web.Application()
        app['bot'] = bot
        app['dp'] = dp
        app.router.add_post('/webhook', WebhookApp.handle)
        app.on_startup.append(WebhookApp.on_startup)
        app.on_shutdown.append(WebhookApp.on_shutdown)
        return app


def create_app(bot: Bot, dp: Dispatcher) -> web.Application:
    """
    Створює aiohttp Application для прийому webhook від Telegram.

    Args:
        bot: Інстанс Bot.
        dp: Інстанс Dispatcher.

    Returns:
        Налаштований aiohttp.Application.
    """
    return WebhookApp.create_app(bot, dp)
