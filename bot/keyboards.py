from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardRemove, InlineKeyboardButton,
                           InlineKeyboardMarkup)
# from aiogram.utils.keyboard import InlineKeyboardBuilder

remove_keyboard = ReplyKeyboardRemove()

search_method = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📚 Пошук за назвою')],
        [KeyboardButton(text='📝 Пошук за текстом')]
    ],
    resize_keyboard=True,
    # input_field_placeholder='Оберіть метод пошуку:'
)

# async def inline_songs(songs_dict):
#     keyboard = InlineKeyboardBuilder()
#     for song_id, song_info in songs_dict.items():
#         keyboard.add(
#             InlineKeyboardButton(
#                 text=f'{song_id}. {song_info["title"]}',
#                 callback_data=f'{song_info["url"]}'
#             )
#         )
#     return keyboard.adjust(1).as_markup()


def create_pagination_keyboard(current_page, total_pages):
    buttons = []

    # Якщо сторінок 5 або менше
    if total_pages <= 5:
        for i in range(total_pages):
            if i == current_page:
                buttons.append(InlineKeyboardButton(text=f"-{i + 1}-", callback_data=f"page_{i}"))
            else:
                buttons.append(InlineKeyboardButton(text=f"{i + 1}", callback_data=f"page_{i}"))
    else:
        # Перша сторінка
        if current_page == 0 and total_pages > 5:
            buttons.append(InlineKeyboardButton(text="-1-", callback_data="page_0"))
            buttons.append(InlineKeyboardButton(text="2", callback_data="page_1"))
            buttons.append(InlineKeyboardButton(text="3", callback_data="page_2"))
            buttons.append(InlineKeyboardButton(text="4", callback_data="page_3"))
            buttons.append(InlineKeyboardButton(text=f">>{total_pages}", callback_data=f"page_{total_pages - 1}"))
        # Друга сторінка
        elif current_page == 1 and total_pages > 5:
            buttons.append(InlineKeyboardButton(text="1", callback_data="page_0"))
            buttons.append(InlineKeyboardButton(text="-2-", callback_data="page_1"))
            buttons.append(InlineKeyboardButton(text="3", callback_data="page_2"))
            buttons.append(InlineKeyboardButton(text="4", callback_data="page_3"))
            buttons.append(InlineKeyboardButton(text=f">>{total_pages}", callback_data=f"page_{total_pages - 1}"))
        # Третя сторінка
        elif current_page == 2 and total_pages > 5:
            buttons.append(InlineKeyboardButton(text="1", callback_data="page_0"))
            buttons.append(InlineKeyboardButton(text="2", callback_data="page_1"))
            buttons.append(InlineKeyboardButton(text="-3-", callback_data="page_2"))
            buttons.append(InlineKeyboardButton(text="4", callback_data="page_3"))
            buttons.append(InlineKeyboardButton(text=f">>{total_pages}", callback_data=f"page_{total_pages - 1}"))
        # Третя з кінця сторінка
        elif current_page == total_pages - 3 and total_pages > 5:
            buttons.append(InlineKeyboardButton(text="<<1", callback_data="page_0"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages - 3}", callback_data=f"page_{total_pages - 4}"))
            buttons.append(InlineKeyboardButton(text=f"-{total_pages - 2}-", callback_data=f"page_{total_pages - 3}"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages - 1}", callback_data=f"page_{total_pages - 2}"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages}", callback_data=f"page_{total_pages - 1}"))
        # Передостання сторінка
        elif current_page == total_pages - 2 and total_pages > 5:
            buttons.append(InlineKeyboardButton(text="<<1", callback_data="page_0"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages - 3}", callback_data=f"page_{total_pages - 4}"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages - 2}", callback_data=f"page_{total_pages - 3}"))
            buttons.append(InlineKeyboardButton(text=f"-{total_pages - 1}-", callback_data=f"page_{total_pages - 2}"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages}", callback_data=f"page_{total_pages - 1}"))
        # Остання сторінка
        elif current_page == total_pages - 1 and total_pages > 5:
            buttons.append(InlineKeyboardButton(text="<<1", callback_data="page_0"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages - 3}", callback_data=f"page_{total_pages - 4}"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages - 2}", callback_data=f"page_{total_pages - 3}"))
            buttons.append(InlineKeyboardButton(text=f"{total_pages - 1}", callback_data=f"page_{total_pages - 2}"))
            buttons.append(InlineKeyboardButton(text=f"-{total_pages}-", callback_data=f"page_{total_pages - 1}"))
        else:
            # Перша сторінка
            if current_page > 1:
                buttons.append(InlineKeyboardButton(text="<<1", callback_data="page_0"))
            # Попередня сторінка
            if current_page > 0:
                buttons.append(InlineKeyboardButton(text=f"{current_page}", callback_data=f"page_{current_page - 1}"))
            # Теперішня сторінка
            buttons.append(InlineKeyboardButton(text=f"-{current_page + 1}-", callback_data=f"page_{current_page}"))
            # Наступна сторінка
            if current_page < total_pages - 1:
                buttons.append(InlineKeyboardButton(text=f"{current_page + 2}", callback_data=f"page_{current_page + 1}"))
            # Остання сторінка
            if current_page < total_pages - 2:
                buttons.append(InlineKeyboardButton(text=f">>{total_pages}", callback_data=f"page_{total_pages - 1}"))

    # Додати кнопку повернення до етапу вибору методу пошуку
    return_button = InlineKeyboardButton(text="🔍 Повернутися до пошуку", callback_data="return_to_search_method")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons, [return_button]])
    return keyboard
