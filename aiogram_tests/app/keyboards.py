from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton, 
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

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

cars = ['Tesla', 'Mercedes', 'BMW']

async def inline_cars():
    keyboard = InlineKeyboardBuilder()
    for car in cars:
        keyboard.add(InlineKeyboardButton(text=car, url='https://www.youtube.com/'))
    return keyboard.adjust(2).as_markup()