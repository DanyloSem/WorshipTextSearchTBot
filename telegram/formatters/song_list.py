"""Форматує фрагмент словника пісень у текстовий список."""

from __future__ import annotations

from html import escape

from telegram.formatters.match_snippet import build_reply_match_snippet


def format_songs_list(chunk: dict, processed_query: str) -> str:
    """
    Форматує фрагмент словника пісень у текстовий список для реплай-режиму.

    Заголовок сторінки формується окремо; тут лише блоки пісень (HTML: курсив у фрагменті збігу).
    processed_query має бути обчислений один раз (LanguageTool) і збережений у FSM.

    Args:
        chunk: Словник {index: {"title", "id", "description"}}.
        processed_query: Запит після process_text (один раз на пошук).

    Returns:
        Рядок з нумерованим списком пісень (HTML: курсив у фрагменті збігу).
    """
    blocks: list[str] = []
    for index, song in chunk.items():
        title = song.get('title', '') or ''
        song_id = song.get('id', '') or ''
        description = song.get('description', '') or ''
        inner = build_reply_match_snippet(title, description, processed_query)
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
