"""Константи для текстів кнопок та методів пошуку."""

SEARCH_BY_TITLE = '📚 Пошук за назвою'
SEARCH_BY_LYRICS = '📝 Пошук за текстом'

VALID_SEARCH_METHODS = (SEARCH_BY_TITLE, SEARCH_BY_LYRICS)

SEARCH_METHOD_TO_API = {
    SEARCH_BY_TITLE: 'title',
    SEARCH_BY_LYRICS: 'lyrics',
}
