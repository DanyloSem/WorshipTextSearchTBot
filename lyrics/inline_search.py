"""Інлайн-пошук пісень по локальних даних з корекцією та fuzzy-збігом."""

import re

import language_tool_python
from fuzzywuzzy import fuzz, process

from logs.log_config import logger
from lyrics.provider import SongsDataProvider


class InlineSearch:
    """
    Пошук пісень по тексту для інлайн-запитів.

    Використовує провайдер даних (JSON), корекцію мови (LanguageTool)
    та fuzzy-збіг (fuzzywuzzy). Не залежить від SongSearchService.
    """

    def __init__(self, data_provider: SongsDataProvider) -> None:
        """
        Args:
            data_provider: Джерело даних пісень для пошуку.
        """
        self._provider = data_provider
        self._tool = language_tool_python.LanguageTool('uk')

    @property
    def songs_data(self) -> dict:
        """Словник даних пісень для зворотної сумісності з обробниками."""
        return self._provider.songs_data

    def process_text(self, text: str) -> str:
        """Корекція граматики та очищення запиту."""
        if not text:
            return ''
        logger.debug('[LYRICS] process_text вхід: text=%s', text)
        matches = self._tool.check(text)
        corrected = language_tool_python.utils.correct(text, matches)
        result = re.sub(r'[^\w\s]', '', corrected)
        logger.debug(
            '[LYRICS] process_text вихід: matches_count=%s, corrected=%s, result=%s',
            len(matches),
            corrected,
            result,
        )
        return result

    def search_content(self, content: str | None, query: str) -> str | None:
        """Шукає збіги в тексті (назва або лірика) і повертає фрагмент."""
        if not content or not isinstance(content, str):
            return None
        match = process.extractOne(query, content.split('\n'), scorer=fuzz.partial_ratio)
        if match and match[1] > 75:
            return match[0].strip()
        return None

    def search_song_data(self, song_data: dict, query: str) -> str | None:
        """Шукає збіг у назві або тексті однієї пісні."""
        for content in song_data.values():
            result = self.search_content(content, query)
            if result:
                return result
        return None

    def search_songs(self, user_text: str) -> dict[str, str]:
        """
        Повертає словник {song_id: description} для інлайн-результатів.

        Args:
            user_text: Текст запиту користувача.

        Returns:
            До 50 пар song_id -> фрагмент збігу.
        """
        query = self.process_text(user_text)
        logger.info(
            '[LYRICS] search_songs: user_text=%s, query_after_process=%s',
            user_text,
            query,
        )
        results: dict[str, str] = {}
        songs_data = self._provider.get_songs_data()
        logger.debug('[LYRICS] search_songs: перебираємо пісень=%s', len(songs_data))
        for song_id, song_data in songs_data.items():
            result = self.search_song_data(song_data, query)
            if result:
                results[song_id] = result
            if len(results) >= 50:
                logger.debug('[LYRICS] search_songs: досягнуто ліміт 50 результатів')
                break
        logger.info('[LYRICS] search_songs результат: знайдено=%s', len(results))
        return results

    def format_title(self, title: str) -> str:
        """Обрізає назву до 40 символів для відображення в інлайн-результаті."""
        title = title.rstrip(' /')
        if len(title) > 40:
            title = title[:40].rstrip(' /') + '...'
        return title
