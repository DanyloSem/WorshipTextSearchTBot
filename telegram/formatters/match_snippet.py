"""Фрагмент збігу для реплай-списку пісень (назва vs контекст, обрізка до 32 символів)."""

_DISPLAY_MAX = 32
_ELLIPSIS = '...'
_TITLE_MATCH_LABEL = 'Назва пісні'


def build_reply_match_snippet(
    processed_query: str,
    processed_title: str,
    description: str,
) -> str:
    """
    Будує короткий текст для рядка «Збіг» у реплай-списку.

    Якщо оброблений запит повністю збігається з назвою або входить у неї як підрядок —
    повертає статичну мітку «Назва пісні». Інакше застосовує «розумну обрізку» рядка
    збігу (до 32 символів разом із «...»).

    Args:
        processed_query: Запит після process_text (один раз на відповідь).
        processed_title: Назва після process_text (заздалегідь з пошуку).
        description: Рядок найкращого збігу з fuzzy-пошуку.

    Returns:
        Підготовлений текст без HTML-тегів (екранування далі у форматері).
    """
    pq = (processed_query or '').strip()
    pt = (processed_title or '').strip()
    if pq and (pq == pt or pq in pt):
        return _TITLE_MATCH_LABEL
    return _smart_truncate_fragment((description or '').strip(), pq)


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
