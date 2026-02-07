from typing import Any

from aiohttp import web
from aiogram import Bot, Dispatcher

from webhook.webhook_app import WebhookApp


def create_app(
    bot: Bot,
    dp: Dispatcher,
    pco_client: Any = None,
    repository: Any = None,
    pco_webhook_authenticity_secret: str | None = None,
) -> web.Application:
    """
    Створює aiohttp Application для прийому webhook від Telegram та PCO.

    Args:
        bot: Інстанс Bot.
        dp: Інстанс Dispatcher.
        pco_client: Опційно — клієнт PCO для /pco-webhook.
        repository: Опційно — репозиторій для /pco-webhook.
        pco_webhook_authenticity_secret: Опційно — секрет перевірки підпису PCO (з конфігу).

    Returns:
        Налаштований aiohttp.Application.
    """
    return WebhookApp.create_app(
        bot,
        dp,
        pco_client,
        repository,
        pco_webhook_authenticity_secret,
    )
