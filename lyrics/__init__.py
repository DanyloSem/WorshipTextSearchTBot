"""Пакет роботи з текстами пісень: збереження, індекс, пошук."""

from lyrics.inline_search import InlineSearch
from lyrics.provider import SongsDataProvider
from lyrics.whoosh_index import create_index as create_whoosh_index
from lyrics.whoosh_search import open_existing_index, search_songs as whoosh_search_songs

__all__ = [
    'SongsDataProvider',
    'InlineSearch',
    'create_whoosh_index',
    'open_existing_index',
    'whoosh_search_songs',
]
