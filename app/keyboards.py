from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           ReplyKeyboardRemove, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder

remove_kb = ReplyKeyboardRemove()

search_method_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='📚Пошук за назвою')],
        [KeyboardButton(text='📝Пошук за текстом')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Оберіть метод пошуку:'
)

async def inline_songs(songs_dict):
    keyboard = InlineKeyboardBuilder()
    for song_id, song_info in songs_dict.items():
        keyboard.add(
            InlineKeyboardButton(
                text=f'{song_id}. {song_info["title"]}', 
                callback_data=f'{song_info["url"]}'
            )
        )
    return keyboard.adjust(1).as_markup()