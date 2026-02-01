"""Клавіатури бота: reply та inline з пагінацією."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from telegram.constants import SEARCH_BY_LYRICS, SEARCH_BY_TITLE


class Keyboards:
    """
    Константи розміток та фабрика клавіатури пагінації.

    До 5 кнопок сторінок (поточну в центрі при багатьох сторінках),
    плюс кнопка «Повернутися до пошуку».
    """

    remove_keyboard = ReplyKeyboardRemove()

    search_method = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SEARCH_BY_TITLE)],
            [KeyboardButton(text=SEARCH_BY_LYRICS)],
        ],
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
            InlineKeyboardMarkup з кнопками сторінок та «Повернутися до пошуку».
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

        return_button = InlineKeyboardButton(
            text='🔍 Повернутися до пошуку',
            callback_data='return_to_search_method',
        )
        return InlineKeyboardMarkup(inline_keyboard=[buttons, [return_button]])


remove_keyboard = Keyboards.remove_keyboard
search_method = Keyboards.search_method
create_pagination_keyboard = Keyboards.create_pagination_keyboard
