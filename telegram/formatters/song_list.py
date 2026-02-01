"""Форматує фрагмент словника пісень у текстовий список."""


def format_songs_list(chunk: dict) -> str:
    """
    Форматує фрагмент словника пісень у текстовий список.

    Args:
        chunk: Словник {index: {"title": str, "id": str}}.

    Returns:
        Рядок з нумерованим списком пісень та командою /id_{id}.
    """
    return '\n'.join(
        f"▶️ {index}. {song['title']}\nТекст пісні: /id_{song['id']}\n"
        for index, song in chunk.items()
    )
