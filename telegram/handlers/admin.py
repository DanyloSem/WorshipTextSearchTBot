"""Обробники адмін-меню: блокування та розблокування користувачів."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from logs.log_config import logger
from telegram import keyboards as kb
from telegram.fsm import AdminState

if TYPE_CHECKING:
    from storage.user_repository import UserRepository


def get_admin_router(
    telegram_admins: tuple[int, ...],
    user_repository: 'UserRepository',
) -> Router:
    """
    Роутер адмінки: тільки для telegram_admins.

    Флоу: Адміністрування -> [Заблокувати], [Розблокувати], [Повернутись].
    Заблокувати: список усіх за last_active_at; адміна блокувати неможливо.
    Розблокувати: список заблокованих за blocked_at.
    """
    router = Router()
    admin_ids_set = frozenset(telegram_admins)

    def admin_filter(message: Message) -> bool:
        """Фільтр: обробляти лише повідомлення від адмінів (щоб не перехоплювати пошук)."""
        return message.from_user is not None and message.from_user.id in admin_ids_set

    def is_admin(user_id: int) -> bool:
        return user_id in admin_ids_set

    @router.message(F.text == kb.ADMIN_BTN_ADMINISTRATION, admin_filter)
    async def admin_enter(message: Message, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(AdminState.admin_menu)
        await message.answer(
            'Обери дію:',
            reply_markup=kb.admin_menu_keyboard,
        )

    @router.message(AdminState.admin_menu, F.text == kb.ADMIN_BTN_BLOCK_USER, admin_filter)
    async def admin_block_list(message: Message, state: FSMContext) -> None:
        users = user_repository.list_all_ordered_by_last_active()
        keyboard, text_to_user_id = kb.create_admin_user_list_keyboard(users)
        await state.set_state(AdminState.block_choose_user)
        await state.update_data(button_to_user_id=text_to_user_id)
        await message.answer(
            'Обери користувача для блокування:',
            reply_markup=keyboard,
        )

    @router.message(AdminState.admin_menu, F.text == kb.ADMIN_BTN_UNBLOCK_USER, admin_filter)
    async def admin_unblock_list(message: Message, state: FSMContext) -> None:
        users = user_repository.list_blocked_ordered_by_blocked_at()
        if not users:
            await message.answer(
                'Нікого не заблоковано.',
                reply_markup=kb.admin_menu_keyboard,
            )
            return
        keyboard, text_to_user_id = kb.create_admin_user_list_keyboard(users)
        await state.set_state(AdminState.unblock_choose_user)
        await state.update_data(button_to_user_id=text_to_user_id)
        await message.answer(
            'Обери користувача для розблокування:',
            reply_markup=keyboard,
        )

    @router.message(AdminState.admin_menu, F.text == kb.ADMIN_BTN_BACK, admin_filter)
    async def admin_back_to_main(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(
            'Ось головне меню.',
            reply_markup=kb.return_to_search_with_admin_keyboard,
        )

    @router.message(AdminState.block_choose_user, F.text, admin_filter)
    async def admin_block_confirm(message: Message, state: FSMContext) -> None:
        if not message.text:
            return
        if message.text == kb.ADMIN_BTN_BACK:
            await state.set_state(AdminState.admin_menu)
            await message.answer(
                'Обери дію:',
                reply_markup=kb.admin_menu_keyboard,
            )
            return
        data = await state.get_data()
        button_to_user_id = data.get('button_to_user_id') or {}
        target_user_id = button_to_user_id.get(message.text)
        if target_user_id is None:
            await message.answer('Обери користувача зі списку або натисни «Повернутись».')
            return
        if is_admin(target_user_id):
            await message.answer(
                'Заблокувати адміністратора неможливо.',
                reply_markup=kb.admin_menu_keyboard,
            )
            await state.set_state(AdminState.admin_menu)
            return
        now_iso = datetime.now(timezone.utc).isoformat()
        user_repository.set_blocked(target_user_id, now_iso)
        logger.info('[ADMIN] Заблоковано user_id=%s', target_user_id)
        await state.set_state(AdminState.admin_menu)
        await message.answer(
            f'Користувача (id={target_user_id}) заблоковано.',
            reply_markup=kb.admin_menu_keyboard,
        )

    @router.message(AdminState.unblock_choose_user, F.text, admin_filter)
    async def admin_unblock_confirm(message: Message, state: FSMContext) -> None:
        if not message.text:
            return
        if message.text == kb.ADMIN_BTN_BACK:
            await state.set_state(AdminState.admin_menu)
            await message.answer(
                'Обери дію:',
                reply_markup=kb.admin_menu_keyboard,
            )
            return
        data = await state.get_data()
        button_to_user_id = data.get('button_to_user_id') or {}
        target_user_id = button_to_user_id.get(message.text)
        if target_user_id is None:
            await message.answer('Обери користувача зі списку або натисни «Повернутись».')
            return
        user_repository.set_unblocked(target_user_id)
        logger.info('[ADMIN] Розблоковано user_id=%s', target_user_id)
        await state.set_state(AdminState.admin_menu)
        await message.answer(
            f'Користувача (id={target_user_id}) розблоковано.',
            reply_markup=kb.admin_menu_keyboard,
        )

    return router
