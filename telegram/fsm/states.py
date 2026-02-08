"""Стани FSM для діалогу пошуку пісень та адмінки."""

from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    """Стани користувача в діалозі пошуку пісень."""

    search_query = State()
    display_songs = State()


class AdminState(StatesGroup):
    """Стани адмін-меню (вибір блокування/розблокування)."""

    admin_menu = State()
    block_choose_user = State()
    unblock_choose_user = State()
