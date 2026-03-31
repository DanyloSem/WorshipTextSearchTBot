"""Обробник інлайн-запитів."""

from aiogram import Router
from aiogram.types import InlineQuery, InputTextMessageContent, InlineQueryResultArticle

from logs.log_config import logger
from lyrics.inline_search import InlineSearch


def get_inline_router(inline_search: InlineSearch) -> Router:
    """Повертає роутер з обробником інлайн-запитів."""
    router = Router()

    @router.inline_query()
    async def inline_echo(inline_query: InlineQuery) -> None:
        text = inline_query.query.strip()
        user_id = inline_query.from_user.id if inline_query.from_user else None
        logger.info(
            '[INLINE] Інлайн-запит: user_id=%s, query=%s',
            user_id,
            text,
        )
        if not text:
            logger.debug('[INLINE] Порожній запит, ігноруємо')
            return

        ordered_songs = inline_search.search_songs(text)
        logger.info(
            '[INLINE] Пошук по локальній бібліотеці: знайдено результатів=%s',
            len(ordered_songs),
        )

        if not ordered_songs:
            logger.debug('[INLINE] Результатів немає, відповідь "Пісню не знайдено"')
            results = [
                InlineQueryResultArticle(
                    id='0',
                    title='Пісню не знайдено',
                    input_message_content=InputTextMessageContent(
                        message_text='Пісню не знайдено. Спробуй інший запит.',
                    ),
                ),
            ]
            await inline_query.answer(results=results, cache_time=0)
            return

        results = []
        for song_id, description in ordered_songs:
            title = list(inline_search.songs_data[song_id].keys())[0]
            title = inline_search.format_title(title)
            lyrics = list(inline_search.songs_data[song_id].values())[0]
            if not isinstance(lyrics, str) or not lyrics.strip():
                lyrics = 'Текст пісні відсутній.'
            results.append(
                InlineQueryResultArticle(
                    id=song_id,
                    title=title,
                    input_message_content=InputTextMessageContent(message_text=lyrics),
                    description=description,
                ),
            )
        logger.debug('[INLINE] Відповідь: results_count=%s', len(results))
        await inline_query.answer(results=results, cache_time=0)

    return router
