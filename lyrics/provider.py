"""Провайдер даних пісень для inline-пошуку (репозиторій)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from logs.log_config import logger

if TYPE_CHECKING:
    from storage.repository import SongRepository


class SongsDataProvider:
    """
    Надає дані пісень з репозиторію у форматі {song_id: {title: lyrics}}.

    Використовується InlineSearch та інлайн-хендлером для доступу до пісень.
    """

    def __init__(self, repository: 'SongRepository') -> None:
        """
        Args:
            repository: Репозиторій пісень (наприклад, SQLite).
        """
        self._repository = repository
        logger.debug('[LYRICS] SongsDataProvider ініціалізовано з репозиторієм')

    def get_songs_data(self) -> dict:
        """
        Повертає словник даних пісень з репозиторію.

        Returns:
            Словник {song_id: {title: lyrics}}.
        """
        data = self._repository.get_all()
        logger.debug('[LYRICS] get_songs_data: пісень=%s', len(data))
        return data

    @property
    def songs_data(self) -> dict:
        """Той самий словник даних пісень для зручності доступу з InlineSearch."""
        return self.get_songs_data()
