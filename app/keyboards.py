from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)

# Створюємо клавіатуру, додаємо в неї кнопки
main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Каталог')], # Перший ряд з однію кнопкою
    [KeyboardButton(text='Смітник'), KeyboardButton(text='Контакти')] # Другий ряд з двома кнопками
],
                           resize_keyboard=True,
                           input_field_placeholder='Виберіть формат пошуку.',
                           )

settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Youtube', url='https://www.youtube.com/')]
    ])