"""Обробник команди /id_*."""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from planning_center.song_search import SongSearchService
from telegram import keyboards as kb
from telegram.fsm import UserState


def get_song_router(song_search_service: SongSearchService) -> Router:
    """Повертає роутер з обробником команди /id_*."""
    router = Router()

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
            logger.debug('[SONG] Запит тексту з PCO: song_id=%s', song_id)
            lyrics = await song_search_service.get_song_text(song_id)
            if lyrics:
                logger.info(
                    '[SONG] Текст отримано: song_id=%s, length=%s',
                    song_id,
                    len(lyrics),
                )
                await message.answer(lyrics, reply_markup=kb.search_method)
            else:
                logger.warning('[SONG] Текст пісні не знайдено в PCO: song_id=%s', song_id)
                await message.answer('Текст пісні не знайдено.', reply_markup=kb.search_method)
            await state.set_state(UserState.search_method)
            logger.debug('[SONG] Стан встановлено: UserState.search_method')
        else:
            logger.warning('[SONG] Невалідний song_id (не цифри): raw=%s', song_id)

    return router
