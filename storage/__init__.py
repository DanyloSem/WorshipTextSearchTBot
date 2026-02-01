"""Пакет сховища пісень (репозиторій)."""

from storage.repository import SongRepository
from storage.sqlite_repository import SQLiteSongRepository

__all__ = ['SongRepository', 'SQLiteSongRepository']
