"""Форматує фрагмент словника пісень у текстовий список."""


def format_songs_list(chunk: dict) -> str:
    """
    Форматує фрагмент словника пісень у текстовий список.

    Args:
        chunk: Словник {index: {"title": str, "id": str, "description": str}}.

    Returns:
        Рядок з нумерованим списком пісень, фрагментом збігу та командою /id_{id}.
    """
    separator = '⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯'
    parts: list[str] = []
    for idx, (index, song) in enumerate(chunk.items()):
        if idx != 0:
            parts.append(separator)
        title = song.get('title', '')
        song_id = song.get('id', '')
        fragment = song.get('description') or ''
        parts.append(
            '\n'.join(
                [
                    f'▶️ {index}. {title}',
                    f'🔍 Фрагмент: {fragment}',
                    f'📄 Текст: /id_{song_id}',
                ],
            ),
        )
    return '\n'.join(parts)
