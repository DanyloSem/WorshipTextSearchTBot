"""Обробник команди /start та входу в сценарії (Текстовий пошук / Повернутись)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from aiogram import F, Router
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
    Повертає роутер з обробником /start та входу в сценарій пошуку.

    Після /start показує меню вибору (Текстовий пошук + Адміністрування для адміна).
    Обробник «Текстовий пошук» входить у пошук; «Повернутись» у стані пошуку (адмін) повертає в меню.
    """
    router = Router()
    admin_ids = frozenset(telegram_admins)

    def is_admin(uid: int) -> bool:
        return uid in admin_ids

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
            user_repository.upsert_from_telegram_user(
                user_id=user_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=getattr(user, 'phone_number', None),
                is_admin=is_admin(user_id),
                now_iso=now_iso,
            )
            reply_markup = (
                kb.return_to_search_with_admin_keyboard
                if is_admin(user_id)
                else kb.return_to_search_keyboard
            )
        else:
            reply_markup = kb.return_to_search_keyboard

        await state.clear()
        await message.answer(
            f'👋 Слава Ісусу Христу, {first_name}!\nНатисни «🔍 Текстовий пошук» для пошуку пісень.',
            reply_markup=reply_markup,
        )
        logger.debug('[START] Меню вибору сценаріїв')

    @router.message(F.text == kb.TEXT_SEARCH_BTN)
    async def enter_text_search(message: Message, state: FSMContext) -> None:
        if not message.from_user:
            return
        user_id = message.from_user.id
        await state.set_state(UserState.search_query)
        reply_markup = (
            kb.admin_back_only_keyboard
            if is_admin(user_id)
            else kb.return_to_search_keyboard
        )
        await message.answer(
            'Введи фрагмент тексту або назву пісні:',
            reply_markup=reply_markup,
        )
        logger.debug('[START] Вхід у сценарій пошуку: user_id=%s', user_id)

    @router.message(UserState.search_query, F.text == kb.ADMIN_BTN_BACK)
    async def back_to_menu_from_search_query(message: Message, state: FSMContext) -> None:
        if not message.from_user or not is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            'Обери дію:',
            reply_markup=kb.return_to_search_with_admin_keyboard,
        )
        logger.debug('[START] Адмін повернувся в меню вибору зі стану search_query')

    @router.message(UserState.display_songs, F.text == kb.ADMIN_BTN_BACK)
    async def back_to_menu_from_display_songs(message: Message, state: FSMContext) -> None:
        if not message.from_user or not is_admin(message.from_user.id):
            return
        await state.clear()
        await message.answer(
            'Обери дію:',
            reply_markup=kb.return_to_search_with_admin_keyboard,
        )
        logger.debug('[START] Адмін повернувся в меню вибору зі стану display_songs')

    def main_menu_any_text_filter(message: Message, data: dict) -> bool:
        """Пропускає лише в головному меню (стан порожній), не на кнопки вибору."""
        state = data.get('state')
        if not isinstance(state, FSMContext) or state.get_state() is not None:
            return False
        if message.text in (kb.TEXT_SEARCH_BTN, kb.ADMIN_BTN_ADMINISTRATION):
            return False
        return True

    @router.message(F.text, main_menu_any_text_filter)
    async def main_menu_reminder(message: Message, state: FSMContext) -> None:
        """Заглушка: нагадування обрати дію кнопкою, якщо в головному меню написали текст."""
        if not message.from_user:
            return
        reply_markup = (
            kb.return_to_search_with_admin_keyboard
            if is_admin(message.from_user.id)
            else kb.return_to_search_keyboard
        )
        await message.answer(
            'Будь ласка, обери дію, натиснувши кнопку нижче 👇',
            reply_markup=reply_markup,
        )

    return router
