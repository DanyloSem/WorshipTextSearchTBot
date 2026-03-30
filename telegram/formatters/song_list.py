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

    Заголовок сторінки формується окремо; тут лише блоки пісень (HTML для жирного/підкреслення
    задається в обробниках через parse_mode).

    Args:
        chunk: Словник {index: {"title": str, "id": str, "description": str}}.
        fuzzy_search_service: Сервіс узгодженої нормалізації запиту з пошуком.
        search_text: Оригінальний текст запиту користувача (для рядка «Збіг»).

    Returns:
        Рядок з нумерованим списком пісень (HTML: підкреслення у фрагменті збігу).
    """
    blocks: list[str] = []
    for index, song in chunk.items():
        title = song.get('title', '') or ''
        song_id = song.get('id', '') or ''
        description = song.get('description', '') or ''
        inner = build_reply_match_snippet(
            fuzzy_search_service,
            search_text,
            title,
            description,
        )
        blocks.append(
            '\n'.join(
                [
                    f'▶️ {index}. {escape(title)}',
                    f'🎯 Збіг: <u>{escape(inner)}</u>',
                    f'📝 Текст: /id_{song_id}',
                ],
            ),
        )
    return '\n\n'.join(blocks)


def format_songs_page_title(start: int, end: int) -> str:
    """
    Формує HTML-заголовок сторінки списку пісень (жирний шрифт).

    Args:
        start: Перший номер у списку (1-based).
        end: Останній номер на сторінці.

    Returns:
        Рядок з тегом <b> для Telegram HTML.
    """
    return f'<b>📖 Пісні від {start} до {end}:</b>'
