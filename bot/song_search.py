"""Сервіс пошуку пісень та отримання текстів через Planning Center API."""

from __future__ import annotations

import base64
import os
from typing import TYPE_CHECKING

import httpx

from bot.constants import SEARCH_BY_LYRICS, SEARCH_BY_TITLE
from logs.log_config import logger

if TYPE_CHECKING:
    from config import Config


class SongSearchService:
    """
    Робота з Planning Center API: пошук пісень за назвою/текстом та отримання лірики.

    Використовує async HTTP (httpx). Конфігурація через Config або змінні середовища.
    """

    BASE_URL = 'https://api.planningcenteronline.com/services/v2'
    SONGS_URL = f'{BASE_URL}/songs?per_page=100&order=title&where'

    def __init__(self, config: Config | None = None) -> None:
        """
        Args:
            config: Конфігурація з client_id та secret. Якщо None — читає з os.getenv.
        """
        if config is not None:
            self._client_id = config.client_id
            self._secret = config.secret
        else:
            self._client_id = os.getenv('CLIENT_ID', '')
            self._secret = os.getenv('SECRET', '')
        self._headers = self._get_headers()

    def _get_headers(self) -> dict[str, str]:
        """Повертає заголовки Basic Auth для API."""
        credentials = f'{self._client_id}:{self._secret}'
        credentials_b64 = base64.b64encode(credentials.encode()).decode()
        return {'Authorization': f'Basic {credentials_b64}'}

    async def _get_response_json(self, request_url: str) -> dict | None:
        """Виконує GET-запит і повертає JSON або None."""
        async with httpx.AsyncClient() as client:
            response = await client.get(request_url, headers=self._headers)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                'Помилка API: status_code=%s, response=%s',
                response.status_code,
                response.text,
            )
            return None

    def _choose_search_url(self, search_data: dict) -> str | None:
        """Повертає URL для пошуку за методом та текстом."""
        if search_data['search_method'] == SEARCH_BY_TITLE:
            return f'{self.SONGS_URL}[title]={search_data["search_text"]}'
        if search_data['search_method'] == SEARCH_BY_LYRICS:
            return f'{self.SONGS_URL}[lyrics]={search_data["search_text"]}'
        return None

    def _fetch_songs_dict(self, song_data: dict, songs_dict: dict) -> dict:
        """Доповнює songs_dict даними з відповіді API."""
        index = len(songs_dict)
        for song in song_data['data']:
            song_title = song['attributes']['title']
            song_url = song['links']['self']
            song_id = song_url.split('/')[-1]
            index += 1
            songs_dict[index] = {'title': song_title, 'id': song_id}
        return songs_dict

    async def get_songs_dict(self, search_data: dict) -> dict:
        """
        Повертає словник {index: {title, id}} пісень за пошуковими даними.

        Args:
            search_data: Містить search_method та search_text.

        Returns:
            Словник пісень з пагінації API.
        """
        search_url = self._choose_search_url(search_data)
        if not search_url:
            return {}
        songs_data = await self._get_response_json(search_url)
        if not songs_data:
            return {}
        songs_dict: dict = {}
        songs_dict = self._fetch_songs_dict(songs_data, songs_dict)
        while 'next' in songs_data.get('links', {}):
            next_url = songs_data['links']['next']
            songs_data = await self._get_response_json(next_url)
            if not songs_data:
                break
            songs_dict = self._fetch_songs_dict(songs_data, songs_dict)
        logger.info('Songs dict: %s', songs_dict)
        return songs_dict

    async def get_song_text(self, song_id: str) -> str | None:
        """
        Повертає текст пісні за ідентифікатором.

        Args:
            song_id: Ідентифікатор пісні в Planning Center.

        Returns:
            Лірика або None при помилці.
        """
        url = f'{self.BASE_URL}/songs/{song_id}/arrangements'
        song_data = await self._get_response_json(url)
        if not song_data or not song_data.get('data'):
            return None
        return song_data['data'][0]['attributes'].get('lyrics', 'Текст пісні відсутній.')
