"""Протокол репозиторію пісень."""

from datetime import datetime
from typing import Protocol


class SongRepository(Protocol):
    """
    Контракт для читання та запису пісень.

    Пошук по фрагменту тексту (fuzzy) виконується в Python поверх get_all();
    репозиторій лише віддає дані.
    """

    def get_by_id(self, song_id: str) -> dict | None:
        """
        Повертає один запис пісні за ідентифікатором.

        Args:
            song_id: Ідентифікатор пісні (PCO id).

        Returns:
            Словник {id, title, lyrics} або None.
        """
        ...

    def get_all(self) -> dict:
        """
        Повертає всі пісні для fuzzy-пошуку.

        Returns:
            Словник {song_id: {title: lyrics}}.
        """
        ...

    def upsert_songs(self, songs: list[dict]) -> None:
        """
        Записує або оновлює записи пісень (для sync).

        Args:
            songs: Список словників з полями id, title, lyrics, опційно updated_at, created_at.
        """
        ...

    def delete_song(self, song_id: str) -> None:
        """
        Видаляє пісню за ідентифікатором (для webhook-події destroyed).

        Args:
            song_id: Ідентифікатор пісні (PCO id).
        """
        ...

    def get_last_synced_at(self) -> datetime | None:
        """
        Повертає час останньої синхронізації БД з API.

        Returns:
            UTC datetime останньої синхронізації або None, якщо ще не було.
        """
        ...

    def set_last_synced_at(self, dt: datetime) -> None:
        """
        Зберігає час останньої синхронізації БД з API.

        Args:
            dt: UTC datetime синхронізації.
        """
        ...
