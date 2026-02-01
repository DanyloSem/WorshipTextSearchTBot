"""Спільний fuzzy-пошук пісень (LanguageTool + fuzzywuzzy + регулярка)."""

import re

import language_tool_python
from fuzzywuzzy import fuzz, process

from logs.log_config import logger


class FuzzySearchService:
    """
    Пошук пісень по фрагменту тексту: корекція (LanguageTool), регулярка, fuzzy-збіг.

    Використовується для інлайн-пошуку та основного пошуку в чаті; приймає словник
    пісень і повертає список збігів з фрагментом (description).
    """

    def __init__(self, language: str = 'uk') -> None:
        """
        Args:
            language: Код мови для LanguageTool (за замовчуванням українська).
        """
        self._tool = language_tool_python.LanguageTool(language)

    def process_text(self, text: str) -> str:
        """
        Корекція граматики та очищення запиту (прибирання розділових знаків).

        Args:
            text: Вхідний текст користувача.

        Returns:
            Виправлений і очищений рядок для пошуку.
        """
        if not text:
            return ''
        logger.debug('[FUZZY] process_text вхід: text=%s', text)
        matches = self._tool.check(text)
        corrected = language_tool_python.utils.correct(text, matches)
        result = re.sub(r'[^\w\s]', '', corrected)
        logger.debug(
            '[FUZZY] process_text вихід: matches_count=%s, corrected=%s, result=%s',
            len(matches),
            corrected,
            result,
        )
        return result

    def _search_content(self, content: str | None, query: str) -> str | None:
        """Шукає збіг у тексті (назва або лірика) і повертає фрагмент."""
        if not content or not isinstance(content, str):
            return None
        match = process.extractOne(query, content.split('\n'), scorer=fuzz.partial_ratio)
        if match and match[1] > 75:
            return match[0].strip()
        return None

    def _search_song_data(self, song_data: dict, query: str) -> str | None:
        """Шукає збіг у назві або тексті однієї пісні; повертає фрагмент або None."""
        for content in song_data.values():
            result = self._search_content(content, query)
            if result:
                return result
        return None

    def search(
        self,
        user_text: str,
        songs_data: dict,
        max_results: int | None = 50,
    ) -> list[dict]:
        """
        Повертає список збігів по фрагменту тексту (LanguageTool + fuzzywuzzy).

        Args:
            user_text: Текст запиту користувача.
            songs_data: Словник {song_id: {title: lyrics}}.
            max_results: Максимум результатів (50 для інлайну, None — без обмеження для чату).

        Returns:
            Список словників {song_id, title, lyrics, description}; description — фрагмент збігу.
        """
        query = self.process_text(user_text)
        logger.info(
            '[FUZZY] search: user_text=%s, query_after_process=%s',
            user_text,
            query,
        )
        results: list[dict] = []
        for song_id, song_data in songs_data.items():
            description = self._search_song_data(song_data, query)
            if description:
                title = next(iter(song_data.keys()), '')
                lyrics = next(iter(song_data.values()), '')
                results.append(
                    {
                        'song_id': song_id,
                        'title': title,
                        'lyrics': lyrics,
                        'description': description,
                    },
                )
            if max_results is not None and len(results) >= max_results:
                logger.debug('[FUZZY] search: досягнуто max_results=%s', max_results)
                break
        logger.info('[FUZZY] search результат: знайдено=%s', len(results))
        return results

    def format_title(self, title: str, max_length: int = 40) -> str:
        """Обрізає назву для відображення в інлайн-результаті."""
        title = title.rstrip(' /')
        if len(title) > max_length:
            title = title[:max_length].rstrip(' /') + '...'
        return title
