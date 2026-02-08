"""Обробник команди /id_*."""

from typing import TYPE_CHECKING

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from telegram import keyboards as kb
from telegram.fsm import UserState

if TYPE_CHECKING:
    from storage.repository import SongRepository


def get_song_router(
    repository: 'SongRepository',
    telegram_admins: tuple[int, ...] = (),
) -> Router:
    """Повертає роутер з обробником команди /id_* (точний пошук по id з локальної БД)."""
    router = Router()
    admin_ids = frozenset(telegram_admins)

    def _reply_markup(message: Message):
        if message.from_user and message.from_user.id in admin_ids:
            return kb.admin_search_keyboard
        return kb.return_to_search_keyboard

    @router.message(F.text.startswith('/id_'))
    async def process_song_id(message: Message, state: FSMContext) -> None:
        user_id = message.from_user.id if message.from_user else None
        logger.info(
            '[SONG] Користувач запросив текст пісні: user_id=%s, command=%s',
            user_id,
            message.text,
        )
        song_id = message.text[4:]
        if song_id.isdigit():
            logger.debug('[SONG] Запит тексту з локальної БД: song_id=%s', song_id)
            record = repository.get_by_id(song_id)
            reply_markup = _reply_markup(message)
            if record and record.get('lyrics'):
                logger.info(
                    '[SONG] Текст отримано: song_id=%s, length=%s',
                    song_id,
                    len(record['lyrics']),
                )
                await message.answer(record['lyrics'], reply_markup=reply_markup)
            else:
                logger.warning('[SONG] Текст пісні не знайдено в локальній БД: song_id=%s', song_id)
                await message.answer('Текст пісні не знайдено.', reply_markup=reply_markup)
            await state.set_state(UserState.search_query)
            logger.debug('[SONG] Стан встановлено: UserState.search_query')
        else:
            logger.warning('[SONG] Невалідний song_id (не цифри): raw=%s', song_id)

    return router
