from typing import Any

from aiohttp import web

from webhook.webhook_app import WebhookApp


def create_pco_only_app(
    pco_client: Any,
    repository: Any,
    pco_webhook_authenticity_secret: str | None,
) -> web.Application:
    """
    Створює мінімальний aiohttp Application лише для прийому PCO webhooks (POST /pco-webhook).

    Використовується в run.py при режимі Telegram polling + PCO webhook. Без маршрутів Telegram
    та без lifecycle (set_webhook/delete_webhook).

    Args:
        pco_client: Клієнт PCO для fetch_song_by_id.
        repository: Репозиторій пісень для upsert_songs/delete_song.
        pco_webhook_authenticity_secret: Секрет перевірки підпису X-PCO-Webhooks-Authenticity.

    Returns:
        Налаштований aiohttp.Application з одним маршрутом /pco-webhook.
    """
    app = web.Application()
    app['pco_client'] = pco_client
    app['repository'] = repository
    app['pco_webhook_authenticity_secret'] = pco_webhook_authenticity_secret
    app.router.add_post('/pco-webhook', WebhookApp.handle_pco_webhook)
    return app
