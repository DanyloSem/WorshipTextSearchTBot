"""Клавіатури бота: reply та inline з пагінацією та адмінка."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

if TYPE_CHECKING:
    from storage.user_record import UserRecord

TEXT_SEARCH_BTN = '🔍 Текстовий пошук'
RETURN_TO_SEARCH_TEXT = TEXT_SEARCH_BTN

ADMIN_BTN_ADMINISTRATION = '🛠️ Адміністрування'
ADMIN_BTN_BLOCK_USER = '🚫 Заблокувати користувача'
ADMIN_BTN_UNBLOCK_USER = '🔓 Розблокувати користувача'
ADMIN_BTN_BACK = '◀️ Повернутись'


class Keyboards:
    """
    Константи розміток та фабрика клавіатури пагінації.

    До 5 кнопок сторінок (поточну в центрі при багатьох сторінках).
    Кнопка «🔍 Текстовий пошук» — reply; для адміна також «Повернутись» під час пошуку.
    """

    remove_keyboard = ReplyKeyboardRemove()

    return_to_search_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=TEXT_SEARCH_BTN)]],
        resize_keyboard=True,
    )

    MAX_PAGINATION_BUTTONS = 5

    @staticmethod
    def create_pagination_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
        """
        Створює inline-клавіатуру пагінації з до 5 кнопок сторінок.

        При total_pages <= 5 показує всі номери; інакше — вікно навколо current_page
        з кнопками «<<1» та «>>N» по краях.

        Args:
            current_page: Поточна сторінка (0-based).
            total_pages: Загальна кількість сторінок.

        Returns:
            InlineKeyboardMarkup лише з кнопками сторінок.
        """
        buttons: list[InlineKeyboardButton] = []

        if total_pages <= Keyboards.MAX_PAGINATION_BUTTONS:
            for i in range(total_pages):
                label = f'-{i + 1}-' if i == current_page else str(i + 1)
                buttons.append(InlineKeyboardButton(text=label, callback_data=f'page_{i}'))
        else:
            half = Keyboards.MAX_PAGINATION_BUTTONS // 2
            start = max(0, min(current_page - half, total_pages - Keyboards.MAX_PAGINATION_BUTTONS))
            end = min(start + Keyboards.MAX_PAGINATION_BUTTONS, total_pages)

            if start > 0:
                buttons.append(InlineKeyboardButton(text='<<1', callback_data='page_0'))

            for i in range(start, end):
                label = f'-{i + 1}-' if i == current_page else str(i + 1)
                buttons.append(InlineKeyboardButton(text=label, callback_data=f'page_{i}'))

            if end < total_pages:
                buttons.append(
                    InlineKeyboardButton(
                        text=f'>>{total_pages}',
                        callback_data=f'page_{total_pages - 1}',
                    ),
                )

        return InlineKeyboardMarkup(inline_keyboard=[buttons])

    return_to_search_with_admin_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=TEXT_SEARCH_BTN)],
            [KeyboardButton(text=ADMIN_BTN_ADMINISTRATION)],
        ],
        resize_keyboard=True,
    )

    admin_menu_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ADMIN_BTN_BLOCK_USER)],
            [KeyboardButton(text=ADMIN_BTN_UNBLOCK_USER)],
            [KeyboardButton(text=ADMIN_BTN_BACK)],
        ],
        resize_keyboard=True,
    )

    admin_back_only_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=ADMIN_BTN_BACK)]],
        resize_keyboard=True,
    )

    @staticmethod
    def create_admin_user_list_keyboard(users: 'list[UserRecord]') -> tuple[ReplyKeyboardMarkup, dict[str, int]]:
        """
        Клавіатура: одна кнопка на користувача (ПІБ / username / ID) + [Повернутись].

        Унікальність текстів забезпечується додаванням (user_id) при дублікатах.

        Args:
            users: Список UserRecord (всі або лише заблоковані).

        Returns:
            (ReplyKeyboardMarkup, маппінг текст_кнопки -> user_id для FSM).
        """
        from storage.user_record import UserRecord

        def label_for(r: UserRecord) -> str:
            parts = [r.first_name or '', r.last_name or '']
            name = ' '.join(p.strip() for p in parts).strip()
            if name:
                return name
            if r.username:
                return r.username
            return str(r.user_id)

        labels_raw = [label_for(r) for r in users]
        seen: dict[str, int] = {}
        labels: list[str] = []
        text_to_user_id: dict[str, int] = {}
        for r, raw in zip(users, labels_raw):
            count = seen.get(raw, 0) + 1
            seen[raw] = count
            text = raw if count == 1 else f'{raw} ({r.user_id})'
            text_to_user_id[text] = r.user_id
            labels.append(text)
        rows = [[KeyboardButton(text=t)] for t in labels]
        rows.append([KeyboardButton(text=ADMIN_BTN_BACK)])
        return (
            ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True),
            text_to_user_id,
        )


remove_keyboard = Keyboards.remove_keyboard
return_to_search_keyboard = Keyboards.return_to_search_keyboard
create_pagination_keyboard = Keyboards.create_pagination_keyboard
return_to_search_with_admin_keyboard = Keyboards.return_to_search_with_admin_keyboard
admin_menu_keyboard = Keyboards.admin_menu_keyboard
admin_back_only_keyboard = Keyboards.admin_back_only_keyboard
create_admin_user_list_keyboard = Keyboards.create_admin_user_list_keyboard
