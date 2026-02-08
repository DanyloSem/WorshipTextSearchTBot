"""Утиліти отримання user_id та chat_id з події (Update) для middleware."""

from aiogram.types import Update


def get_user_id_from_update(update: Update) -> int | None:
    """
    Повертає Telegram user_id з оновлення.

    Перевіряє message, callback_query, inline_query та повертає from_user.id.

    Args:
        update: Об'єкт оновлення від Telegram.

    Returns:
        user_id або None, якщо користувача немає (наприклад, channel_post).
    """
    if update.message and update.message.from_user:
        return update.message.from_user.id
    if update.callback_query and update.callback_query.from_user:
        return update.callback_query.from_user.id
    if update.inline_query and update.inline_query.from_user:
        return update.inline_query.from_user.id
    if update.edited_message and update.edited_message.from_user:
        return update.edited_message.from_user.id
    return None


def get_chat_id_from_update(update: Update) -> int | None:
    """
    Повертає chat_id для відправки відповіді (повідомлення або callback).

    Для inline_query немає чату — повертає None.

    Args:
        update: Об'єкт оновлення від Telegram.

    Returns:
        chat_id або None.
    """
    if update.message and update.message.chat:
        return update.message.chat.id
    if update.callback_query and update.callback_query.message and update.callback_query.message.chat:
        return update.callback_query.message.chat.id
    if update.edited_message and update.edited_message.chat:
        return update.edited_message.chat.id
    return None
