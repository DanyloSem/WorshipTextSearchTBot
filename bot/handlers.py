from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import bot.keyboards as kb
import bot.song_search as ss

router = Router()

class SongSelection(StatesGroup):
    search_method = State()
    search_query = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(f'Вітаю {message.from_user.first_name}!\nОберіть метод пошуку:',
                        reply_markup=kb.search_method_kb)
    await state.set_state(SongSelection.search_method)

@router.message(SongSelection.search_method)
async def process_search_method(message: Message, state: FSMContext):
    search_method = message.text
    if search_method in ['📚Пошук за назвою', '📝Пошук за текстом']:
        await state.update_data(search_method=search_method)
        await message.answer('Введіть текст для пошуку:', reply_markup=kb.remove_kb)
        await state.set_state(SongSelection.search_query)
    else:
        await message.answer('Будь ласка, оберіть метод пошуку із запропонованих варіантів:')

@router.message(SongSelection.search_query)
async def process_search_query(message: Message, state: FSMContext):
    search_text = message.text
    await state.update_data(search_text=search_text)
    search_data = await state.get_data()
    songs_dict = ss.get_songs_dict(search_data)
    
    if songs_dict:
        chunks = [dict(list(songs_dict.items())[i:i+20]) for i in range(0, len(songs_dict), 20)]

        total_songs = len(songs_dict)
        for i, chunk in enumerate(chunks):
            inline_keyboard = await kb.inline_songs(chunk)
            start = i * 20 + 1
            end = min((i + 1) * 20, total_songs)
            await message.answer(f'Пісні від {start} до {end}:', reply_markup=inline_keyboard)
    else:
        await message.answer('Жодної пісні не знайдено.')
        await message.answer('Оберіть метод пошуку:', reply_markup=kb.search_method_kb)
        await state.set_state(SongSelection.search_method)

@router.callback_query(lambda c: c.data.startswith('http'))
async def process_song_selection(callback_query: CallbackQuery, state: FSMContext):
    song_url = callback_query.data

    lyrics = ss.get_song_text(song_url)
    
    await callback_query.message.answer(lyrics)
    await callback_query.answer()
    
    await callback_query.message.answer('Оберіть іншу пісню або метод пошуку:', reply_markup=kb.search_method_kb)
    await state.set_state(SongSelection.search_method)