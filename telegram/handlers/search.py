"""Обробники пошуку та відображення списку пісень."""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from planning_center.constants import SEARCH_BY_LYRICS, SEARCH_BY_TITLE
from planning_center.song_search import SongSearchService
from telegram import keyboards as kb
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
            await message.answer('👇 Новий пошук — кнопка нижче', reply_markup=kb.return_to_search_keyboard)
        else:
            logger.info('[SEARCH] Результатів пошуку немає, запит нового тексту')
            await message.answer('Жодної пісні не знайдено. Введіть текст для пошуку:', reply_markup=kb.remove_keyboard)
            await state.set_state(UserState.search_query)

    @router.message(UserState.search_query, F.text == kb.RETURN_TO_SEARCH_TEXT)
    async def return_to_search_from_reply_in_query(message: Message, state: FSMContext) -> None:
        """Обробляє натискання «Повернутися до пошуку», коли стан вже search_query (наприклад після /id_*)."""
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SEARCH] Натиснуто «Повернутися до пошуку» у стані search_query: user_id=%s',
            user_id,
        )
        await message.answer('Введіть текст для пошуку:', reply_markup=kb.remove_keyboard)
        logger.debug('[SEARCH] Клавіатуру прибрано, очікуємо текст пошуку')

    @router.message(
        UserState.search_query,
        ~F.text.startswith('/id_'),
        F.text != kb.RETURN_TO_SEARCH_TEXT,
    )
    async def process_search_query(message: Message, state: FSMContext) -> None:
        """Шукає по назві та по тексту, обʼєднує результати без дублікатів."""
        search_text = message.text
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SEARCH] Введено текст пошуку: user_id=%s, search_text=%s',
            user_id,
            search_text,
        )
        await state.update_data(search_text=search_text)
        by_title = await song_search_service.get_songs_dict(
            {'search_method': SEARCH_BY_TITLE, 'search_text': search_text},
        )
        by_lyrics = await song_search_service.get_songs_dict(
            {'search_method': SEARCH_BY_LYRICS, 'search_text': search_text},
        )
        by_id: dict[str, dict] = {}
        for d in (by_title, by_lyrics):
            for song in d.values():
                by_id[song['id']] = song
        sorted_songs = sorted(by_id.values(), key=lambda s: s['title'].lower())
        songs_dict = {i: song for i, song in enumerate(sorted_songs, start=1)}
        logger.info(
            '[SEARCH] PCO: по назві=%s, по тексту=%s, після обʼєднання=%s',
            len(by_title),
            len(by_lyrics),
            len(songs_dict),
        )
        await state.update_data(songs_dict=songs_dict)
        await state.set_state(UserState.display_songs)
        await display_songs_list(message, state)

    @router.message(UserState.display_songs, F.text == kb.RETURN_TO_SEARCH_TEXT)
    async def return_to_search_from_reply(message: Message, state: FSMContext) -> None:
        """Обробляє натискання reply-кнопки «Повернутися до пошуку»."""
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SEARCH] Натиснуто «Повернутися до пошуку» (reply): user_id=%s',
            user_id,
        )
        await message.answer('Введіть текст для пошуку:', reply_markup=kb.remove_keyboard)
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
        await message.reply('`Оберіть пісню, або натисніть "🔍 Повернутися до пошуку".')

    return router
