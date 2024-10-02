import hashlib
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineQuery, InputTextMessageContent, InlineQueryResultArticle
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from bot import keyboards as kb
from bot.song_search import SongSearchService
from logs.log_config import logger
from bot.inline_search import InlineSearch
import concurrent.futures


router = Router()
sss = SongSearchService()
inlinesearch = InlineSearch()


class UserState(StatesGroup):
    search_method = State()
    search_query = State()
    display_songs = State()


def format_songs_list(chunk):
    return "\n".join([f"▶️ {index}. {song['title']}\nТекст пісні: /id_{song['id']}\n" for index, song in chunk.items()])

def generate_unique_id(text):
    return hashlib.md5(text.encode()).hexdigest()

def fetch_song_text(song_id):
    # Функція для отримання тексту пісні
    return sss.get_song_text(song_id)


async def display_songs_list(message: Message, state: FSMContext):
    data = await state.get_data()
    songs_dict = data.get('songs_dict')

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


@router.inline_query()
async def inline_echo(inline_query: InlineQuery):
    # Отримуємо текст користувача:
    text = inline_query.query

    songs_list = inlinesearch.get_songs_by_text(text)

    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Виконуємо завдання паралельно
        future_to_song = {executor.submit(fetch_song_text, song['id']): song for song in songs_list}

        for future in concurrent.futures.as_completed(future_to_song):
            song = future_to_song[future]
            try:
                song_text = future.result()
            except Exception as exc:
                logger.error(f"Помилка при отриманні тексту пісні {song['id']}: {exc}")
                song_text = "Текст пісні не знайдено."

            result_id = generate_unique_id(song['attributes']['title'])
            logger.info(f"Result ID: {result_id}")
            logger.info(f"Song_id: {song['id']}")
            logger.info(f"Song text: {song_text}")

            input_content = InputTextMessageContent(message_text=song_text)

            result = InlineQueryResultArticle(
                id=result_id,
                input_message_content=input_content,
                title=song['attributes']['title'],
                # description='Опис пісні',
                # url='https://www.google.com',
                # thumb_url='https://www.google.com/favicon.ico'
            )
            results.append(result)

    # Відправляємо результат, в якому results - список з результатами:
    await inline_query.answer(results=results)


@router.message(F.text.startswith('/id_'))
async def process_song_id(message: Message, state: FSMContext):
    logger.info(f'User input: {message.text}')
    song_id = message.text[4:]  # Видаляємо перші 4 символи '/'
    # Перевірка, чи є решта тексту ідентифікатором пісні
    if song_id.isdigit():
        logger.info(f'Song ID: {song_id}')
        lyrics = sss.get_song_text(song_id)

        if lyrics:
            await message.answer(lyrics, reply_markup=kb.search_method)
        else:
            await message.answer('Текст пісні не знайдено.', reply_markup=kb.search_method)
        await state.set_state(UserState.search_method)


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


@router.message(UserState.search_query)
async def process_search_query(message: Message, state: FSMContext):
    search_text = message.text
    await state.update_data(search_text=search_text)
    search_data = await state.get_data()
    songs_dict = sss.get_songs_dict(search_data)
    await state.update_data(songs_dict=songs_dict)

    # Переводимо користувача в стан display_songs
    await state.set_state(UserState.display_songs)
    await display_songs_list(message, state)


@router.callback_query(F.data.startswith('page_'))
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


@router.message(UserState.display_songs)
async def handle_display_songs(message: Message):
    await message.reply("I don't understand you :(")


@router.callback_query(F.data == "return_to_search_method")
async def return_to_search_method(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer('Оберіть метод пошуку:', reply_markup=kb.search_method)
    await state.set_state(UserState.search_method)
    await callback_query.answer()
