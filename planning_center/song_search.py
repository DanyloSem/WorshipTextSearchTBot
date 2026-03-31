from __future__ import annotations

import base64
import os
from typing import TYPE_CHECKING

import httpx

from logs.log_config import logger
from planning_center.constants import SEARCH_BY_LYRICS, SEARCH_BY_TITLE
from planning_center.rate_limiter import PcoRateLimiter

if TYPE_CHECKING:
    from config import Config


class SongSearchService:
    """
    Робота з Planning Center API: пошук пісень за назвою/текстом та отримання лірики.

    Використовує async HTTP (httpx). Конфігурація через Config або змінні середовища.
    """

    BASE_URL = 'https://api.planningcenteronline.com/services/v2'
    SONGS_URL = f'{BASE_URL}/songs?per_page=100&order=title&where'
    ALL_SONGS_URL = f'{BASE_URL}/songs?per_page=100&order=title'

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
        self._rate_limiter = PcoRateLimiter(max_requests=90, window_seconds=20.0)

    def _get_headers(self) -> dict[str, str]:
        """Повертає заголовки Basic Auth для API."""
        credentials = f'{self._client_id}:{self._secret}'
        credentials_b64 = base64.b64encode(credentials.encode()).decode()
        return {'Authorization': f'Basic {credentials_b64}'}

    async def _get_response_json(self, request_url: str) -> dict | None:
        """Виконує GET-запит і повертає JSON або None. Дотримується rate limit (90/20 с)."""
        await self._rate_limiter.acquire()
        async with httpx.AsyncClient() as client:
            response = await client.get(request_url, headers=self._headers)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                '[PCO] API error: status_code=%s, response=%s',
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
        search_url = self._choose_search_url(search_data)
        if not search_url:
            logger.warning('[PCO] Unsupported search_method, empty result')
            return {}
        songs_data = await self._get_response_json(search_url)
        if not songs_data:
            logger.warning('[PCO] First request returned None or error')
            return {}
        songs_dict: dict = {}
        songs_dict = self._fetch_songs_dict(songs_data, songs_dict)
        while 'next' in songs_data.get('links', {}):
            next_url = songs_data['links']['next']
            songs_data = await self._get_response_json(next_url)
            if not songs_data:
                break
            songs_dict = self._fetch_songs_dict(songs_data, songs_dict)
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
        lyrics_raw = song_data['data'][0]['attributes'].get('lyrics')
        return lyrics_raw

    async def fetch_song_by_id(self, song_id: str) -> dict | None:
        """
        Повертає одну пісню з PCO у форматі для синхронізації (upsert_songs).

        Використовується при обробці webhook-подій created/updated.

        Args:
            song_id: Ідентифікатор пісні в Planning Center.

        Returns:
            Словник {id, title, lyrics, updated_at?, created_at?} або None при помилці API.
        """
        url = f'{self.BASE_URL}/songs/{song_id}'
        data = await self._get_response_json(url)
        if not data or not data.get('data'):
            logger.warning('[PCO] fetch_song_by_id: не вдалося отримати пісню song_id=%s', song_id)
            return None
        song = data['data']
        attrs = song.get('attributes', {})
        title = attrs.get('title', '')
        lyrics = await self.get_song_text(song_id)
        return {
            'id': song_id,
            'title': title,
            'lyrics': lyrics,
            'updated_at': attrs.get('updated_at'),
            'created_at': attrs.get('created_at'),
        }

    async def fetch_all_songs_with_lyrics(self) -> list[dict]:
        """
        Повертає всі пісні з PCO з текстами (для синхронізації в локальну БД).

        Пагінує список пісень, для кожної отримує lyrics з arrangements.
        Використовується тільки в sync-модулі, не в обробниках запитів.

        Returns:
            Список словників {id, title, lyrics, updated_at?, created_at?}.
        """
        all_songs: list[dict] = []
        url: str | None = self.ALL_SONGS_URL
        total_planned: int | None = None
        while url:
            data = await self._get_response_json(url)
            if not data or not data.get('data'):
                break
            if total_planned is None:
                total_planned = data.get('meta', {}).get('total_count')
            for song in data['data']:
                attrs = song.get('attributes', {})
                title = attrs.get('title', '')
                song_url = song.get('links', {}).get('self', '')
                song_id = song_url.split('/')[-1] if song_url else ''
                if not song_id:
                    continue
                lyrics = await self.get_song_text(song_id)
                status = 'success' if lyrics else 'error'
                current = len(all_songs) + 1
                progress = f'{current}/{total_planned}' if total_planned is not None else str(current)
                title_part = title if title else '(no title)'
                logger.info(
                    'Parsing song %s (%s) completed. Status: %s. Progress: %s',
                    song_id,
                    title_part,
                    status,
                    progress,
                )
                all_songs.append(
                    {
                        'id': song_id,
                        'title': title,
                        'lyrics': lyrics,
                        'updated_at': attrs.get('updated_at'),
                        'created_at': attrs.get('created_at'),
                    },
                )
            url = data.get('links', {}).get('next')
        return all_songs
