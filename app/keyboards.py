from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


remove_kb = ReplyKeyboardRemove()
# Створюємо клавіатуру, додаємо в неї кнопки
search_method_kb = ReplyKeyboardMarkup(keyboard = [
    [KeyboardButton(text='Пошук за назвою')],
    [KeyboardButton(text='Пошук за текстом')]
    ],
                           resize_keyboard=True,
                           input_field_placeholder='Оберіть формат:'
    )

async def inline_songs(songs_dict):
    builder = InlineKeyboardBuilder()
    for song_id, song_info in songs_dict.items():
        builder.add(InlineKeyboardButton(text=song_info['title'], 
                                         callback_data=f'{song_id}, {song_info['title']}, {song_info['url']}',
                                         ))
    return builder.adjust(1).as_markup()