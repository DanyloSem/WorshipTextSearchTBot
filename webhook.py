"""Фабрика aiohttp-додатку для webhook-режиму бота."""

import os
from typing import Any

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from logs.log_config import logger


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
    async def handle_pco_webhook(request: web.Request) -> web.Response:
        """
        Обробляє POST /pco-webhook: заглушка для майбутньої інтеграції з PCO webhooks.

        Логує виклик і опційно запускає синхронізацію, якщо в app передані pco_client та repository.
        """
        logger.info('[WEBHOOK] PCO webhook received')
        app = request.app
        pco_client = app.get('pco_client')
        repository = app.get('repository')
        if pco_client is not None and repository is not None:
            from sync.song_sync import run_once

            try:
                await run_once(pco_client, repository)
            except Exception:
                logger.exception('[WEBHOOK] Помилка синхронізації з PCO webhook')
                return web.Response(status=500)
        return web.Response()

    @staticmethod
    def create_app(
        bot: Bot,
        dp: Dispatcher,
        pco_client: Any = None,
        repository: Any = None,
    ) -> web.Application:
        """
        Створює aiohttp Application для webhook.

        Args:
            bot: Інстанс Bot.
            dp: Інстанс Dispatcher.
            pco_client: Опційно — клієнт PCO для виклику sync з /pco-webhook.
            repository: Опційно — репозиторій пісень для sync.

        Returns:
            Налаштований aiohttp.Application.
        """
        app = web.Application()
        app['bot'] = bot
        app['dp'] = dp
        app['pco_client'] = pco_client
        app['repository'] = repository
        app.router.add_post('/webhook', WebhookApp.handle)
        app.router.add_post('/pco-webhook', WebhookApp.handle_pco_webhook)
        app.on_startup.append(WebhookApp.on_startup)
        app.on_shutdown.append(WebhookApp.on_shutdown)
        return app


def create_app(
    bot: Bot,
    dp: Dispatcher,
    pco_client: Any = None,
    repository: Any = None,
) -> web.Application:
    """
    Створює aiohttp Application для прийому webhook від Telegram.

    Args:
        bot: Інстанс Bot.
        dp: Інстанс Dispatcher.
        pco_client: Опційно — клієнт PCO для /pco-webhook.
        repository: Опційно — репозиторій для sync з /pco-webhook.

    Returns:
        Налаштований aiohttp.Application.
    """
    return WebhookApp.create_app(bot, dp, pco_client, repository)
