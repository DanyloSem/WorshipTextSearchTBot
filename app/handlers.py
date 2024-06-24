from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.song_search as ss

router = Router()

class SongSelection(StatesGroup):
    search_method = State()
    search_query = State()

# Вибрати метод пошуку пісні 
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(f'Вітаю {message.from_user.first_name}!\nОберіть формат пошуку:',
                        reply_markup=kb.search_method_kb)
    await state.set_state(SongSelection.search_method)

# Зберегти метод пошуку в словник
@router.message(SongSelection.search_method)
async def process_search_method(message: Message, state: FSMContext):
    search_method = message.text
    if search_method in ['Пошук за назвою', 'Пошук за текстом']:
        await state.update_data(search_method = search_method)
        await message.answer('Введіть текст для пошуку:', reply_markup=kb.remove_kb)
        await state.set_state(SongSelection.search_query)
    else:
        await message.answer('Будь ласка, оберіть метод пошуку із запропонованих варіантів:')

# Зберегти текст в словник, передати словник в song_search.py
@router.message(SongSelection.search_query)
async def process_search_query(message: Message, state: FSMContext):
    search_text = message.text
    await state.update_data(search_text = search_text)
    search_data = await state.get_data()
    songs_dict = ss.get_songs_dict(search_data)

    for song_id, song_name in songs_dict.items():
        await message.answer(f"{song_id}. {song_name['title']}")
        
    await message.answer('Оберіть формат пошуку:', reply_markup=kb.search_method_kb)
    await state.set_state(SongSelection.search_method)


'''@router.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text('Твій каталог...', reply_markup=await kb.inline_cars())'''