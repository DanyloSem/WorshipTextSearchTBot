"""Сервіс пошуку пісень та отримання текстів через Planning Center API."""

from __future__ import annotations

import base64
import os
from typing import TYPE_CHECKING

import httpx

from logs.log_config import logger
from planning_center.constants import SEARCH_BY_LYRICS, SEARCH_BY_TITLE

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
        logger.debug('[PCO] GET %s', request_url[:120] + '...' if len(request_url) > 120 else request_url)
        async with httpx.AsyncClient() as client:
            response = await client.get(request_url, headers=self._headers)
            logger.info(
                '[PCO] Відповідь API: status_code=%s, url_len=%s',
                response.status_code,
                len(request_url),
            )
            if response.status_code == 200:
                data = response.json()
                meta = data.get('meta', {})
                logger.debug(
                    '[PCO] JSON meta: total_count=%s, next=%s',
                    meta.get('total_count'),
                    'next' in data.get('links', {}),
                )
                return data
            logger.warning(
                '[PCO] Помилка API: status_code=%s, response=%s',
                response.status_code,
                response.text[:500] if response.text else '',
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
            search_data: Містить search_method ('title' або 'lyrics') та search_text.

        Returns:
            Словник пісень з пагінації API.
        """
        logger.info(
            '[PCO] get_songs_dict: search_method=%s, search_text=%s',
            search_data.get('search_method'),
            search_data.get('search_text'),
        )
        search_url = self._choose_search_url(search_data)
        if not search_url:
            logger.warning('[PCO] Не підтримуваний search_method, порожній результат')
            return {}
        songs_data = await self._get_response_json(search_url)
        if not songs_data:
            logger.warning('[PCO] Перший запит повернув None або помилку')
            return {}
        songs_dict: dict = {}
        songs_dict = self._fetch_songs_dict(songs_data, songs_dict)
        page = 1
        logger.debug('[PCO] Сторінка %s: додано пісень=%s', page, len(songs_data.get('data', [])))
        while 'next' in songs_data.get('links', {}):
            next_url = songs_data['links']['next']
            page += 1
            songs_data = await self._get_response_json(next_url)
            if not songs_data:
                logger.warning('[PCO] Пагінація: сторінка %s повернула None', page)
                break
            songs_dict = self._fetch_songs_dict(songs_data, songs_dict)
            logger.debug('[PCO] Сторінка %s: додано пісень=%s, всього=%s', page, len(songs_data.get('data', [])), len(songs_dict))
        logger.info('[PCO] get_songs_dict результат: total_songs=%s', len(songs_dict))
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
        logger.debug('[PCO] get_song_text: song_id=%s', song_id)
        song_data = await self._get_response_json(url)
        if not song_data or not song_data.get('data'):
            logger.warning(
                '[PCO] get_song_text: немає даних для song_id=%s, data_empty=%s',
                song_id,
                not (song_data and song_data.get('data')),
            )
            return None
        lyrics = song_data['data'][0]['attributes'].get('lyrics', 'Текст пісні відсутній.')
        logger.debug('[PCO] get_song_text: song_id=%s, lyrics_len=%s', song_id, len(lyrics))
        return lyrics
