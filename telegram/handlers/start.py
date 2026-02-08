"""Обробник команди /start."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from telegram import keyboards as kb
from telegram.fsm import UserState

if TYPE_CHECKING:
    from storage.user_repository import UserRepository


def get_start_router(
    telegram_admins: tuple[int, ...] = (),
    user_repository: 'UserRepository | None' = None,
) -> Router:
    """
    Повертає роутер з обробником команди /start.

    При наявності user_repository виконує upsert користувача в БД та показує
    кнопку «Адміністрування» для користувачів з telegram_admins.
    """
    router = Router()

    @router.message(CommandStart())
    async def cmd_start(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return
        user = message.from_user
        user_id = user.id
        first_name = user.first_name or 'Користувач'
        logger.info(
            '[START] Користувач натиснув /start: user_id=%s, first_name=%s',
            user_id,
            first_name,
        )

        if user_repository is not None:
            now_iso = datetime.now(timezone.utc).isoformat()
            is_admin = user_id in telegram_admins
            user_repository.upsert_from_telegram_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone_number,
                is_admin=is_admin,
                now_iso=now_iso,
            )
            reply_markup = (
                kb.return_to_search_with_admin_keyboard
                if is_admin
                else kb.remove_keyboard
            )
        else:
            reply_markup = kb.remove_keyboard

        await message.answer(
            f'👋 Слава Ісусу Христу, {first_name}!\nДля пошуку, введи фрагмент тексту або назву пісні:',
            reply_markup=reply_markup,
        )
        await state.set_state(UserState.search_query)
        logger.debug('[START] Стан встановлено: UserState.search_query')

    return router
