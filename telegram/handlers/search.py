"""Обробники пошуку та відображення списку пісень."""

from typing import TYPE_CHECKING

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from lyrics.fuzzy_search import FuzzySearchService
from telegram import keyboards as kb
from telegram.formatters import format_songs_list
from telegram.fsm import UserState
from telegram.pagination import PAGE_SIZE, chunk_songs, get_page_range

if TYPE_CHECKING:
    from storage.repository import SongRepository


def get_search_router(
    fuzzy_search_service: FuzzySearchService,
    repository: 'SongRepository',
    telegram_admins: tuple[int, ...] = (),
) -> Router:
    """Повертає роутер з обробниками пошуку (fuzzy по локальній БД) та відображення списку пісень."""
    router = Router()
    admin_ids = frozenset(telegram_admins)

    def _search_reply_markup(message: Message):
        if message.from_user and message.from_user.id in admin_ids:
            return kb.admin_back_only_keyboard
        return kb.return_to_search_keyboard

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
            await message.answer(
                '👇 Новий пошук — кнопка нижче',
                reply_markup=_search_reply_markup(message),
            )
        else:
            logger.info('[SEARCH] Результатів пошуку немає, запит нового тексту')
            await message.answer(
                'Жодної пісні не знайдено. Введи текст для пошуку:',
                reply_markup=_search_reply_markup(message),
            )
            await state.set_state(UserState.search_query)

    @router.message(UserState.search_query, F.text == kb.TEXT_SEARCH_BTN)
    async def return_to_search_from_reply_in_query(message: Message, state: FSMContext) -> None:
        """Обробляє натискання «Текстовий пошук», коли стан вже search_query (повторний ввід)."""
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SEARCH] Натиснуто «Текстовий пошук» у стані search_query: user_id=%s',
            user_id,
        )
        await message.answer(
            'Введи текст для пошуку:',
            reply_markup=_search_reply_markup(message),
        )
        logger.debug('[SEARCH] Очікуємо текст пошуку')

    @router.message(
        UserState.search_query,
        ~F.text.startswith('/id_'),
        F.text != kb.TEXT_SEARCH_BTN,
    )
    async def process_search_query(message: Message, state: FSMContext) -> None:
        """Шукає по фрагменту тексту (fuzzy) по локальній БД, показує список пісень."""
        search_text = message.text
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SEARCH] Введено текст пошуку: user_id=%s, search_text=%s',
            user_id,
            search_text,
        )
        await state.update_data(search_text=search_text)
        songs_data = repository.get_all()
        results = fuzzy_search_service.search(
            search_text,
            songs_data,
            max_results=None,
        )
        sorted_results = sorted(results, key=lambda r: r['title'].lower())
        songs_dict = {
            i: {'title': r['title'], 'id': r['song_id']}
            for i, r in enumerate(sorted_results, start=1)
        }
        logger.info(
            '[SEARCH] Fuzzy по локальній БД: знайдено=%s',
            len(songs_dict),
        )
        await state.update_data(songs_dict=songs_dict)
        await state.set_state(UserState.display_songs)
        await display_songs_list(message, state)

    @router.message(UserState.display_songs, F.text == kb.TEXT_SEARCH_BTN)
    async def return_to_search_from_reply(message: Message, state: FSMContext) -> None:
        """Обробляє натискання reply-кнопки «Текстовий пошук»."""
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SEARCH] Натиснуто «Текстовий пошук» (reply): user_id=%s',
            user_id,
        )
        await message.answer(
            'Введи текст для пошуку:',
            reply_markup=_search_reply_markup(message),
        )
        await state.set_state(UserState.search_query)
        logger.debug('[SEARCH] Стан встановлено: UserState.search_query')

    @router.message(UserState.display_songs, ~F.text.startswith('/id_'))
    async def handle_display_songs(message: Message) -> None:
        """Реагує лише на повідомлення, що не є командою /id_* (її обробляє song router)."""
        user_id = message.from_user.id if message.from_user else None
        logger.warning(
            '[SEARCH] Користувач у стані display_songs надіслав незрозуміле повідомлення: user_id=%s, text=%s',
            user_id,
            message.text,
        )
        await message.reply(f'Будь ласка обери пісню або натисни:\n{kb.TEXT_SEARCH_BTN}.')

    return router
