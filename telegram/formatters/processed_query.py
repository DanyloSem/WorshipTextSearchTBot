"""Доступ до нормалізованого пошукового запиту з FSM (один виклик LanguageTool на пошук)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lyrics.fuzzy_search import FuzzySearchService


def get_processed_query_from_state_data(
    data: dict,
    fuzzy_search_service: 'FuzzySearchService',
) -> str:
    """
    Повертає `search_query_processed` зі state або обчислює fallback (для старого state).

    Args:
        data: Словник даних FSM.
        fuzzy_search_service: Сервіс fuzzy для fallback.

    Returns:
        Рядок після process_text для поточного запиту.
    """
    cached = data.get('search_query_processed')
    if isinstance(cached, str):
        return cached
    search_text = data.get('search_text') or ''
    if not search_text:
        return ''
    return fuzzy_search_service.process_text(search_text)
