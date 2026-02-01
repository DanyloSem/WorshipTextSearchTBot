"""Провайдер даних пісень з JSON-файлу для inline-пошуку."""

import json
from pathlib import Path

from logs.log_config import logger


class SongsDataProvider:
    """
    Завантажує та надає дані пісень з локального JSON-файлу.

    Використовується InlineSearch для пошуку по назві та тексту без API.
    """

    def __init__(self, songs_data_path: str) -> None:
        """
        Args:
            songs_data_path: Шлях до JSON-файлу з даними пісень.
        """
        self._path = Path(songs_data_path)
        self._songs_data: dict | None = None
        logger.debug('[LYRICS] SongsDataProvider ініціалізовано: path=%s', self._path)

    def get_songs_data(self) -> dict:
        """
        Повертає словник даних пісень (завантажує з файлу при першому виклику).

        Returns:
            Словник {song_id: {title: lyrics}}.
        """
        if self._songs_data is None:
            logger.info(
                '[LYRICS] Завантаження локальної бібліотеки пісень з файлу: path=%s',
                self._path,
            )
            with open(self._path, 'r', encoding='utf-8') as file:
                self._songs_data = json.load(file)
            logger.info(
                '[LYRICS] Локальна бібліотека завантажена вперше: пісень=%s',
                len(self._songs_data),
            )
        else:
            logger.debug(
                '[LYRICS] Використання кешу бібліотеки: пісень=%s',
                len(self._songs_data),
            )
        return self._songs_data

    @property
    def songs_data(self) -> dict:
        """Той самий словник даних пісень для зручності доступу з InlineSearch."""
        return self.get_songs_data()
