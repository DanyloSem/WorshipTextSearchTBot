"""Фрагмент збігу для реплай-списку пісень (назва vs контекст, обрізка до 32 символів)."""

_DISPLAY_MAX = 32
_ELLIPSIS = '...'
_TITLE_MATCH_LABEL = 'Назва пісні'


def _fragment_matches_title(fragment: str, title: str) -> bool:
    """
    Перевіряє, чи фрагмент збігу відповідає назві (повний збіг або фрагмент у назві).

    Порівняння без LanguageTool — сирі рядки після strip.

    Args:
        fragment: Рядок збігу з fuzzy-пошуку.
        title: Оригінальна назва пісні.

    Returns:
        True, якщо збіг по назві (ідентичність або входження фрагмента в назву).
    """
    f = (fragment or '').strip()
    t = (title or '').strip()
    if not f or not t:
        return False
    return f == t or f in t


def build_reply_match_snippet(
    title: str,
    description: str,
    processed_query: str,
) -> str:
    """
    Будує короткий текст для рядка «Збіг» у реплай-списку.

    Якщо фрагмент збігу збігається з назвою (повністю або як підрядок у назві) —
    повертає статичну мітку «Назва пісні». Інакше — «розумну обрізку» рядка збігу
    (до 32 символів разом із «...») з урахуванням уже обробленого запиту.

    Args:
        title: Оригінальна назва пісні.
        description: Рядок найкращого збігу з fuzzy-пошуку.
        processed_query: Запит після process_text (один раз на пошук).

    Returns:
        Підготовлений текст без HTML-тегів (екранування далі у форматері).
    """
    if _fragment_matches_title(description, title):
        return _TITLE_MATCH_LABEL
    return _smart_truncate_fragment((description or '').strip(), (processed_query or '').strip())


def _smart_truncate_fragment(description: str, processed_query: str) -> str:
    """Обрізає рядок збігу до 32 символів з урахуванням положення запиту."""
    if not description:
        return ''
    if len(description) <= _DISPLAY_MAX:
        return description

    pq = (processed_query or '').strip()
    lower_desc = description.lower()
    idx = lower_desc.find(pq.lower()) if pq else -1
    matched_len = len(pq) if idx >= 0 else 0
    if idx < 0:
        return description[: _DISPLAY_MAX - len(_ELLIPSIS)] + _ELLIPSIS

    matched_end = min(idx + matched_len, len(description))

    if idx == 0:
        return description[: _DISPLAY_MAX - len(_ELLIPSIS)] + _ELLIPSIS

    if matched_end == len(description):
        tail_len = _DISPLAY_MAX - len(_ELLIPSIS)
        return _ELLIPSIS + description[-tail_len:]

    inner = _DISPLAY_MAX - 2 * len(_ELLIPSIS)
    center = idx + matched_len // 2
    half = inner // 2
    start = max(0, center - half)
    end = start + inner
    if end > len(description):
        end = len(description)
        start = max(0, end - inner)
    if start == 0:
        return description[: _DISPLAY_MAX - len(_ELLIPSIS)] + _ELLIPSIS
    snippet = description[start:end]
    return _ELLIPSIS + snippet + _ELLIPSIS
