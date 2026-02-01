"""Обробники пошуку та відображення списку пісень."""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from planning_center.song_search import SongSearchService
from telegram import keyboards as kb
from telegram.constants import SEARCH_METHOD_TO_API, VALID_SEARCH_METHODS
from telegram.formatters import format_songs_list
from telegram.fsm import UserState
from telegram.pagination import PAGE_SIZE, chunk_songs, get_page_range


def get_search_router(song_search_service: SongSearchService) -> Router:
    """Повертає роутер з обробниками пошуку та відображення списку пісень."""
    router = Router()

    async def display_songs_list(message: Message, state: FSMContext) -> None:
        """Відображає першу сторінку результатів пошуку."""
        data = await state.get_data()
        songs_dict = data.get('songs_dict')
        logger.debug(
            '[SEARCH] display_songs_list: songs_dict keys count=%s',
            len(songs_dict) if songs_dict else 0,
        )
        if songs_dict:
            chunks = chunk_songs(songs_dict, page_size=PAGE_SIZE)
            chunk = chunks[0]
            songs_list = format_songs_list(chunk)
            pagination_keyboard = kb.create_pagination_keyboard(0, len(chunks))
            start, end = get_page_range(0, len(chunks), len(songs_dict))
            logger.info(
                '[SEARCH] Відображення списку пісень: total=%s, chunks=%s, page 1 range %s-%s',
                len(songs_dict),
                len(chunks),
                start,
                end,
            )
            answer = f'📖 Пісні від {start} до {end}:\n\n{songs_list}'
            await message.answer(answer, reply_markup=pagination_keyboard)
        else:
            logger.info('[SEARCH] Результатів пошуку немає, показ кнопок методу пошуку')
            await message.answer('Жодної пісні не знайдено.', reply_markup=kb.search_method)
            await state.set_state(UserState.search_method)

    @router.message(UserState.search_method)
    async def process_search_method(message: Message, state: FSMContext) -> None:
        search_method = message.text
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SEARCH] Натиснуто кнопку методу пошуку: user_id=%s, text=%s',
            user_id,
            search_method,
        )
        if search_method in VALID_SEARCH_METHODS:
            api_key = SEARCH_METHOD_TO_API[search_method]
            await state.update_data(search_method=search_method)
            logger.debug(
                '[SEARCH] Метод збережено в state: search_method=%s, api_key=%s',
                search_method,
                api_key,
            )
            await message.answer('Введіть текст для пошуку:', reply_markup=kb.remove_keyboard)
            await state.set_state(UserState.search_query)
        else:
            logger.warning(
                '[SEARCH] Невідомий метод пошуку: text=%s, valid=%s',
                search_method,
                VALID_SEARCH_METHODS,
            )
            await message.answer('Будь ласка, оберіть метод пошуку із запропонованих варіантів:')

    @router.message(UserState.search_query)
    async def process_search_query(message: Message, state: FSMContext) -> None:
        search_text = message.text
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SEARCH] Введено текст пошуку: user_id=%s, search_text=%s',
            user_id,
            search_text,
        )
        await state.update_data(search_text=search_text)
        search_data = await state.get_data()
        api_search_data = {
            'search_method': SEARCH_METHOD_TO_API[search_data['search_method']],
            'search_text': search_data['search_text'],
        }
        logger.info(
            '[SEARCH] Запит до PCO API: api_search_data=%s',
            api_search_data,
        )
        songs_dict = await song_search_service.get_songs_dict(api_search_data)
        logger.info(
            '[SEARCH] PCO повернув пісень: count=%s',
            len(songs_dict),
        )
        await state.update_data(songs_dict=songs_dict)
        await state.set_state(UserState.display_songs)
        await display_songs_list(message, state)

    @router.message(UserState.display_songs, ~F.text.startswith('/id_'))
    async def handle_display_songs(message: Message) -> None:
        """Реагує лише на повідомлення, що не є командою /id_* (її обробляє song router)."""
        user_id = message.from_user.id if message.from_user else None
        logger.warning(
            '[SEARCH] Користувач у стані display_songs надіслав незрозуміле повідомлення: user_id=%s, text=%s',
            user_id,
            message.text,
        )
        await message.reply("I don't understand you :(")

    return router
