"""Створення Whoosh-індексу для пошуку по текстах пісень."""

import json
import os

from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import ID, TEXT, Schema
from whoosh.index import create_in


def get_schema() -> Schema:
    """Повертає схему індексу для пісень."""
    return Schema(
        id=ID(stored=True),
        title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
        text=TEXT(stored=True, analyzer=StemmingAnalyzer()),
    )


def create_index(songs: dict, index_dir: str = 'indexdir') -> 'whoosh.index.Index':
    """
    Створює Whoosh-індекс з даних пісень.

    Args:
        songs: Словник {song_id: {"title": str, "text": str}}.
        index_dir: Директорія для збереження індексу.

    Returns:
        Відкритий індекс Whoosh.
    """
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    schema = get_schema()
    ix = create_in(index_dir, schema)
    writer = ix.writer()
    for song_id, song_data in songs.items():
        writer.add_document(
            id=song_id,
            title=song_data['title'],
            text=song_data['text'],
        )
    writer.commit()
    return ix


def get_songs_from_json(path: str = 'transformed_songs_data.json') -> dict:
    """
    Завантажує дані пісень з JSON-файлу для індексації.

    Args:
        path: Шлях до JSON-файлу.

    Returns:
        Словник {song_id: {"title": str, "text": str}}.
    """
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


if __name__ == '__main__':
    songs = get_songs_from_json()
    create_index(songs)
