"""Стани FSM для діалогу пошуку пісень."""

from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    """Стани користувача в діалозі пошуку пісень."""

    search_query = State()
    display_songs = State()
