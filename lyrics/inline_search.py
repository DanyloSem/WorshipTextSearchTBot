"""Інлайн-пошук пісень по локальних даних (обгортка над FuzzySearchService та провайдером)."""

from logs.log_config import logger
from lyrics.fuzzy_search import FuzzySearchService
from lyrics.provider import SongsDataProvider


class InlineSearch:
    """
    Пошук пісень по тексту для інлайн-запитів.

    Використовує провайдер даних (репозиторій) та спільний FuzzySearchService.
    """

    def __init__(
        self,
        data_provider: SongsDataProvider,
        fuzzy_search_service: FuzzySearchService | None = None,
    ) -> None:
        """
        Args:
            data_provider: Джерело даних пісень (репозиторій).
            fuzzy_search_service: Сервіс fuzzy-пошуку; якщо None — створюється внутрішньо.
        """
        self._provider = data_provider
        self._fuzzy = fuzzy_search_service or FuzzySearchService()

    @property
    def songs_data(self) -> dict:
        """Словник даних пісень для зворотної сумісності з обробниками."""
        return self._provider.songs_data

    def search_songs(self, user_text: str) -> list[tuple[str, str]]:
        """
        Повертає список пар (song_id, description) для інлайн-результатів у порядку сортування.

        Порядок: спочатку найточніший збіг, при однаковому score — за назвою (алфавіт).

        Args:
            user_text: Текст запиту користувача.

        Returns:
            До 50 пар (song_id, фрагмент збігу) у відсортованому порядку.
        """
        songs_data = self._provider.get_songs_data()
        results = self._fuzzy.search(user_text, songs_data, max_results=50)
        ordered = [(r['song_id'], r['description']) for r in results]
        logger.info('[LYRICS] search_songs результат: знайдено=%s', len(ordered))
        return ordered

    def format_title(self, title: str) -> str:
        """Обрізає назву до 40 символів для відображення в інлайн-результаті."""
        return self._fuzzy.format_title(title, max_length=40)
