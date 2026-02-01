"""Логіка пагінації списку пісень."""

PAGE_SIZE = 7


def chunk_songs(songs_dict: dict, page_size: int = PAGE_SIZE) -> list[dict]:
    """
    Розбиває словник пісень на сторінки (chunks).

    Args:
        songs_dict: Словник {index: song_data}.
        page_size: Кількість пісень на сторінці.

    Returns:
        Список словників — по одному на сторінку.
    """
    items = list(songs_dict.items())
    return [dict(items[i : i + page_size]) for i in range(0, len(items), page_size)]


def get_page_range(page: int, total_pages: int, total_items: int) -> tuple[int, int]:
    """
    Повертає діапазон індексів елементів для сторінки (1-based для відображення).

    Args:
        page: Номер сторінки (0-based).
        total_pages: Загальна кількість сторінок.
        total_items: Загальна кількість елементів.

    Returns:
        Кортеж (start, end) для відображення «Пісні від start до end».
    """
    start = page * PAGE_SIZE + 1
    end = min((page + 1) * PAGE_SIZE, total_items)
    return start, end
