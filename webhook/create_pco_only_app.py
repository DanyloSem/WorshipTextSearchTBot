from typing import Any

from aiohttp import web

from webhook.webhook_app import WebhookApp


def create_pco_only_app(pco_client: Any, repository: Any) -> web.Application:
    """
    Створює мінімальний aiohttp Application лише для прийому PCO webhooks (POST /pco-webhook).

    Використовується в run.py при режимі Telegram polling + PCO webhook. Без маршрутів Telegram
    та без lifecycle (set_webhook/delete_webhook). Перевірка підпису — по секрету з .env для кожного
    типу події (наприклад SERVICES_V2_EVENTS_ARRANGEMENT_UPDATED).

    Args:
        pco_client: Клієнт PCO для fetch_song_by_id.
        repository: Репозиторій пісень для upsert_songs/delete_song.

    Returns:
        Налаштований aiohttp.Application з одним маршрутом /pco-webhook.
    """
    app = web.Application()
    app['pco_client'] = pco_client
    app['repository'] = repository
    app.router.add_post('/pco-webhook', WebhookApp.handle_pco_webhook)
    return app
