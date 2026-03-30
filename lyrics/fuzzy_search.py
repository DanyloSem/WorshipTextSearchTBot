"""Спільний fuzzy-пошук пісень (LanguageTool + fuzzywuzzy + регулярка)."""

import re

import language_tool_python
from fuzzywuzzy import fuzz, process

from logs.log_config import logger


def _is_mainly_english(text: str) -> bool:
    """
    Повертає True, якщо текст виглядає переважно англійською (немає кирилиці).

    Використовується, щоб не «виправляти» англійські запити через LanguageTool (uk).
    """
    if not text.strip():
        return True
    cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    return cyrillic == 0


class FuzzySearchService:
    """
    Пошук пісень по фрагменту тексту: корекція (LanguageTool для української), регулярка, fuzzy-збіг.

    Англійські запити не проходять через LanguageTool — лише очищення для пошуку.
    """

    def __init__(self, language: str = 'uk') -> None:
        """
        Args:
            language: Код мови для LanguageTool (за замовчуванням українська).
        """
        self._tool = language_tool_python.LanguageTool(language)

    def process_text(self, text: str) -> str:
        """
        Корекція граматики (лише для української) та очищення запиту (прибирання розділових знаків).

        Якщо запит англійською — LanguageTool не використовується, щоб не спотворювати пошук.

        Args:
            text: Вхідний текст користувача.

        Returns:
            Виправлений і очищений рядок для пошуку.
        """
        if not text:
            return ''
        logger.debug('[FUZZY] process_text вхід: text=%s', text)
        cleaned = re.sub(r'[^\w\s]', '', text.strip())
        if _is_mainly_english(text):
            logger.debug('[FUZZY] process_text вихід (EN, без LT): result=%s', cleaned)
            return cleaned
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

    def _search_content(self, content: str | None, query: str) -> tuple[str, int] | None:
        """Шукає збіг у тексті (назва або лірика); повертає (фрагмент, score) або None."""
        if not content or not isinstance(content, str):
            return None
        match = process.extractOne(query, content.split('\n'), scorer=fuzz.partial_ratio)
        if match and match[1] > 75:
            return (match[0].strip(), match[1])
        return None

    def _search_song_data(self, song_data: dict, query: str) -> tuple[str, int] | None:
        """Шукає збіг у назві або тексті однієї пісні; повертає (фрагмент, найкращий score) або None."""
        best: tuple[str, int] | None = None
        for content in (*song_data.keys(), *song_data.values()):
            result = self._search_content(content, query)
            if result and (best is None or result[1] > best[1]):
                best = result
        return best

    def search(
        self,
        user_text: str,
        songs_data: dict,
        max_results: int | None = 50,
        *,
        processed_query: str | None = None,
    ) -> list[dict]:
        """
        Повертає список збігів по фрагменту тексту (LanguageTool + fuzzywuzzy).

        Відсортовано: спочатку за точністю збігу (спад), при однаковому score — за назвою (алфавіт).

        Args:
            user_text: Текст запиту користувача.
            songs_data: Словник {song_id: {title: lyrics}}.
            max_results: Максимум результатів (50 для інлайну, None — без обмеження для чату).
            processed_query: Якщо задано — використовується замість повторного process_text(user_text).

        Returns:
            Список словників {song_id, title, lyrics, description}; description — фрагмент збігу.
        """
        query = processed_query if processed_query is not None else self.process_text(user_text)
        logger.info(
            '[FUZZY] search: user_text=%s, query_after_process=%s',
            user_text,
            query,
        )
        results: list[dict] = []
        for song_id, song_data in songs_data.items():
            found = self._search_song_data(song_data, query)
            if found:
                description, score = found
                title = next(iter(song_data.keys()), '')
                lyrics = next(iter(song_data.values()), '')
                results.append(
                    {
                        'song_id': song_id,
                        'title': title,
                        'lyrics': lyrics,
                        'description': description,
                        '_score': score,
                    },
                )
        # При однаковому score — спочатку довший збіг (точніший), потім за назвою
        results.sort(
            key=lambda r: (
                -r['_score'],
                -len(r.get('description', '')),
                (r.get('title') or '').lower(),
            ),
        )
        for r in results:
            r.pop('_score', None)
        if max_results is not None:
            results = results[:max_results]
        logger.info('[FUZZY] search результат: знайдено=%s', len(results))
        return results

    def format_title(self, title: str, max_length: int = 40) -> str:
        """Обрізає назву для відображення в інлайн-результаті."""
        title = title.rstrip(' /')
        if len(title) > max_length:
            title = title[:max_length].rstrip(' /') + '...'
        return title
