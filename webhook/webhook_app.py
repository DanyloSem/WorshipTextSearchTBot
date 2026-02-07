import os
from typing import Any

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from logs.log_config import logger

from webhook.parse_pco_webhook_event import parse_pco_webhook_event
from webhook.verify_pco_webhook_signature import verify_pco_webhook_signature


PCO_AUTHENTICITY_HEADER = 'X-PCO-Webhooks-Authenticity'


class WebhookApp:
    """
    Обгортка aiohttp Application для прийому webhook від Telegram та PCO.

    Публічна фабрика — create_app (у модулі create_app).
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
        Обробляє POST /pco-webhook: перевірка підпису, парсинг події, оновлення/видалення одного треку в SQLite.
        """
        body = await request.read()
        app = request.app
        secret = app.get('pco_webhook_authenticity_secret')
        if secret:
            signature = request.headers.get(PCO_AUTHENTICITY_HEADER)
            if not verify_pco_webhook_signature(body, signature, secret):
                logger.warning('[WEBHOOK] PCO webhook: невалідний або відсутній підпис')
                return web.Response(status=401)
        else:
            logger.debug(
                '[WEBHOOK] PCO webhook: authenticity secret не налаштовано, перевірку підпису пропущено',
            )

        action, song_id = parse_pco_webhook_event(body)
        if action is None or song_id is None:
            logger.info('[WEBHOOK] PCO webhook: подія не для song або id відсутній, ігноруємо')
            return web.Response()

        pco_client = app.get('pco_client')
        repository = app.get('repository')
        if pco_client is None or repository is None:
            logger.warning('[WEBHOOK] PCO webhook: pco_client або repository не передані в app')
            return web.Response()

        try:
            if action == 'destroyed':
                repository.delete_song(song_id)
                logger.info('[WEBHOOK] PCO webhook: видалено пісню song_id=%s', song_id)
            else:
                song = await pco_client.fetch_song_by_id(song_id)
                if song is None:
                    logger.warning(
                        '[WEBHOOK] PCO webhook: не вдалося отримати пісню з API song_id=%s',
                        song_id,
                    )
                    return web.Response(status=500)
                repository.upsert_songs([song])
                logger.info('[WEBHOOK] PCO webhook: оновлено пісню song_id=%s action=%s', song_id, action)
        except Exception:
            logger.exception('[WEBHOOK] PCO webhook: помилка обробки події song_id=%s', song_id)
            return web.Response(status=500)

        return web.Response()

    @staticmethod
    def create_app(
        bot: Bot,
        dp: Dispatcher,
        pco_client: Any = None,
        repository: Any = None,
        pco_webhook_authenticity_secret: str | None = None,
    ) -> web.Application:
        """
        Створює aiohttp Application для webhook.

        Args:
            bot: Інстанс Bot.
            dp: Інстанс Dispatcher.
            pco_client: Опційно — клієнт PCO для обробки подій song у /pco-webhook.
            repository: Опційно — репозиторій пісень для upsert/delete з /pco-webhook.
            pco_webhook_authenticity_secret: Опційно — секрет для перевірки X-PCO-Webhooks-Authenticity.

        Returns:
            Налаштований aiohttp.Application.
        """
        app = web.Application()
        app['bot'] = bot
        app['dp'] = dp
        app['pco_client'] = pco_client
        app['repository'] = repository
        app['pco_webhook_authenticity_secret'] = pco_webhook_authenticity_secret
        app.router.add_post('/webhook', WebhookApp.handle)
        app.router.add_post('/pco-webhook', WebhookApp.handle_pco_webhook)
        app.on_startup.append(WebhookApp.on_startup)
        app.on_shutdown.append(WebhookApp.on_shutdown)
        return app
