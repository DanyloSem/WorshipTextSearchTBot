"""Обробники пагінації та повернення до пошуку."""

from typing import TYPE_CHECKING

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from telegram import keyboards as kb
from telegram.formatters import format_songs_list, format_songs_page_title
from telegram.fsm import UserState
from telegram.pagination import PAGE_SIZE, chunk_songs

if TYPE_CHECKING:
    from lyrics.fuzzy_search import FuzzySearchService


def get_pagination_router(
    fuzzy_search_service: 'FuzzySearchService',
    telegram_admins: tuple[int, ...] = (),
) -> Router:
    """Повертає роутер з обробниками пагінації та повернення до пошуку."""
    router = Router()
    admin_ids = frozenset(telegram_admins)

    @router.callback_query(F.data.startswith('page_'))
    async def process_page_callback(callback_query: CallbackQuery, state: FSMContext) -> None:
        page = int(callback_query.data.split('_')[1])
        user_id = callback_query.from_user.id if callback_query.from_user else None
        logger.info(
            '[PAGINATION] Натиснуто кнопку сторінки: user_id=%s, callback_data=%s, page=%s',
            user_id,
            callback_query.data,
            page,
        )
        data = await state.get_data()
        songs_dict = data.get('songs_dict')
        search_text = data.get('search_text') or ''
        if not songs_dict:
            logger.warning('[PAGINATION] Немає songs_dict у state, пропуск')
            await callback_query.answer()
            return
        chunks = chunk_songs(songs_dict, page_size=PAGE_SIZE)
        logger.debug(
            '[PAGINATION] chunks=%s, total_songs=%s',
            len(chunks),
            len(songs_dict),
        )
        if page < len(chunks):
            chunk = chunks[page]
            songs_list = format_songs_list(chunk, fuzzy_search_service, search_text)
            pagination_keyboard = kb.create_pagination_keyboard(page, len(chunks))
            total = len(songs_dict)
            logger.info(
                '[PAGINATION] Відображення сторінки: page=%s, total_pages=%s, total_songs=%s',
                page + 1,
                len(chunks),
                total,
            )
            answer = f'{format_songs_page_title(total)}\n\n{songs_list}'
            await callback_query.message.edit_text(
                answer,
                reply_markup=pagination_keyboard,
                parse_mode=ParseMode.HTML,
            )
        await callback_query.answer()

    @router.callback_query(F.data == 'return_to_search_method')
    async def return_to_search_method(callback_query: CallbackQuery, state: FSMContext) -> None:
        user_id = callback_query.from_user.id if callback_query.from_user else None
        logger.info(
            '[PAGINATION] Натиснуто "Текстовий пошук": user_id=%s',
            user_id,
        )
        reply_markup = (
            kb.admin_search_keyboard
            if callback_query.from_user and callback_query.from_user.id in admin_ids
            else kb.return_to_search_keyboard
        )
        await callback_query.message.answer(
            'Введи текст для пошуку:',
            reply_markup=reply_markup,
        )
        await state.set_state(UserState.search_query)
        logger.debug('[PAGINATION] Стан встановлено: UserState.search_query')
        await callback_query.answer()

    return router
