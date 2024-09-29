from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from bot import keyboards as kb
from bot.song_search import SongSearchService
from logs.log_config import logger

router = Router()
sss = SongSearchService()


class UserState(StatesGroup):
    search_method = State()
    search_query = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer(f'Вітаю {message.from_user.first_name}!\nОберіть метод пошуку:',
                         reply_markup=kb.search_method)
    await state.set_state(UserState.search_method)


@router.message(UserState.search_method)
async def process_search_method(message: Message, state: FSMContext):
    search_method = message.text

    if search_method in ['📚 Пошук за назвою', '📝 Пошук за текстом']:
        await state.update_data(search_method=search_method)
        await message.answer('Введіть текст для пошуку:', reply_markup=kb.remove_keyboard)
        await state.set_state(UserState.search_query)
    else:
        await message.answer('Будь ласка, оберіть метод пошуку із запропонованих варіантів:')


def format_songs_list(chunk):
    return "\n".join([f"▶️ {index}. {song['title']}\nТекст: {song['url']}\n" for index, song in chunk.items()])


@router.message(UserState.search_query)
async def process_search_query(message: Message, state: FSMContext):
    search_text = message.text
    await state.update_data(search_text=search_text)
    search_data = await state.get_data()
    songs_dict = sss.get_songs_dict(search_data)
    await state.update_data(songs_dict=songs_dict)

    if songs_dict:
        chunks = [dict(list(songs_dict.items())[i:i+7]) for i in range(0, len(songs_dict), 7)]
        chunk = chunks[0]
        songs_list = format_songs_list(chunk)
        pagination_keyboard = kb.create_pagination_keyboard(0, len(chunks))
        answer = f"📖 Пісні від 1 до {min(7, len(songs_dict))}:\n\n{songs_list}"
        await message.answer(answer, reply_markup=pagination_keyboard)
    else:
        await message.answer('Жодної пісні не знайдено.', reply_markup=kb.search_method)
        await state.set_state(UserState.search_method)


@router.callback_query(lambda c: c.data and c.data.startswith('page_'))
async def process_page_callback(callback_query: CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split('_')[1])
    data = await state.get_data()
    songs_dict = data.get('songs_dict')
    chunks = [dict(list(songs_dict.items())[i:i+7]) for i in range(0, len(songs_dict), 7)]

    if page < len(chunks):
        chunk = chunks[page]
        songs_list = format_songs_list(chunk)
        pagination_keyboard = kb.create_pagination_keyboard(page, len(chunks))
        answer = f"📖 Пісні від {page*7+1} до {min((page+1)*7, len(songs_dict))}:\n\n{songs_list}"
        await callback_query.message.edit_text(answer, reply_markup=pagination_keyboard)
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith('http'))
async def process_song_selection(callback_query: CallbackQuery, state: FSMContext):
    song_url = callback_query.data

    lyrics = sss.get_song_text(song_url)

    await callback_query.message.answer(lyrics)
    await callback_query.answer()

    await callback_query.message.answer('Оберіть іншу пісню або метод пошуку:', reply_markup=kb.search_method)
    await state.set_state(UserState.search_method)


@router.callback_query(lambda c: c.data == "return_to_search_method")
async def return_to_search_method(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer('Оберіть метод пошуку:', reply_markup=kb.search_method)
    await state.set_state(UserState.search_method)
    await callback_query.answer()
