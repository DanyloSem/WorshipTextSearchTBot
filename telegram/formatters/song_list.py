"""Форматує фрагмент словника пісень у текстовий список."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING

from telegram.formatters.match_snippet import build_reply_match_snippet

if TYPE_CHECKING:
    from lyrics.fuzzy_search import FuzzySearchService


def format_songs_list(
    chunk: dict,
    fuzzy_search_service: 'FuzzySearchService',
    search_text: str,
) -> str:
    """
    Форматує фрагмент словника пісень у текстовий список для реплай-режиму.

    Заголовок сторінки формується окремо; тут лише блоки пісень (HTML: курсив у фрагменті збігу).

    Args:
        chunk: Словник {index: {"title", "id", "description", опціонально "title_processed"}}.
        fuzzy_search_service: Сервіс нормалізації запиту (process_text викликається один раз).
        search_text: Оригінальний текст запиту користувача.

    Returns:
        Рядок з нумерованим списком пісень (HTML: курсив у фрагменті збігу).
    """
    processed_query = fuzzy_search_service.process_text(search_text or '')
    blocks: list[str] = []
    for index, song in chunk.items():
        title = song.get('title', '') or ''
        song_id = song.get('id', '') or ''
        description = song.get('description', '') or ''
        processed_title = song.get('title_processed')
        if processed_title is None:
            processed_title = fuzzy_search_service.process_text(title)
        inner = build_reply_match_snippet(
            processed_query,
            processed_title,
            description,
        )
        blocks.append(
            '\n'.join(
                [
                    f'▶️ {index}. {escape(title)}',
                    f'🎯 Збіг: <i>{escape(inner)}</i>',
                    f'📝 Текст: /id_{song_id}',
                ],
            ),
        )
    return '\n\n'.join(blocks)


def _uk_songs_word(count: int) -> str:
    """Повертає слово після числа для «Знайдено N …»."""
    n100 = count % 100
    if 11 <= n100 <= 14:
        return 'пісень'
    n10 = count % 10
    if n10 == 1:
        return 'пісню'
    if 2 <= n10 <= 4:
        return 'пісні'
    return 'пісень'


def format_songs_page_title(total: int) -> str:
    """
    Формує HTML-заголовок списку знайдених пісень (жирний шрифт).

    Args:
        total: Загальна кількість знайдених пісень.

    Returns:
        Рядок з тегом <b> для Telegram HTML.
    """
    word = _uk_songs_word(total)
    return f'<b>📖 Знайдено {total} {word}:</b>'
