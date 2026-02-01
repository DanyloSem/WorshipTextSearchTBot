"""Обробник команди /start."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from telegram import keyboards as kb
from telegram.fsm import UserState


def get_start_router() -> Router:
    """Повертає роутер з обробником команди /start."""
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext) -> None:
        user_id = message.from_user.id if message.from_user else None
        first_name = message.from_user.first_name if message.from_user else 'Користувач'
        logger.info(
            '[START] Користувач натиснув /start: user_id=%s, first_name=%s',
            user_id,
            first_name,
        )
        await message.answer(
            f'Вітаю, {first_name}!\nДля пошуку, введіть фрагмент тексту або назву пісні:',
            reply_markup=kb.remove_keyboard,
        )
        await state.set_state(UserState.search_query)
        logger.debug('[START] Стан встановлено: UserState.search_query')

    return router
