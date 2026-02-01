"""Обробники пагінації та повернення до пошуку."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from telegram import keyboards as kb
from telegram.formatters import format_songs_list
from telegram.fsm import UserState
from telegram.pagination import PAGE_SIZE, chunk_songs, get_page_range


def get_pagination_router() -> Router:
    """Повертає роутер з обробниками пагінації та повернення до пошуку."""
    router = Router()

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
            songs_list = format_songs_list(chunk)
            pagination_keyboard = kb.create_pagination_keyboard(page, len(chunks))
            start, end = get_page_range(page, len(chunks), len(songs_dict))
            logger.info(
                '[PAGINATION] Відображення сторінки: page=%s, total_pages=%s, range %s-%s',
                page + 1,
                len(chunks),
                start,
                end,
            )
            answer = f'📖 Пісні від {start} до {end}:\n\n{songs_list}'
            await callback_query.message.edit_text(answer, reply_markup=pagination_keyboard)
        await callback_query.answer()

    @router.callback_query(F.data == 'return_to_search_method')
    async def return_to_search_method(callback_query: CallbackQuery, state: FSMContext) -> None:
        user_id = callback_query.from_user.id if callback_query.from_user else None
        logger.info(
            '[PAGINATION] Натиснуто "Повернутися до пошуку": user_id=%s',
            user_id,
        )
        await callback_query.message.answer('Введіть текст для пошуку:', reply_markup=kb.remove_keyboard)
        await state.set_state(UserState.search_query)
        logger.debug('[PAGINATION] Стан встановлено: UserState.search_query')
        await callback_query.answer()

    return router
