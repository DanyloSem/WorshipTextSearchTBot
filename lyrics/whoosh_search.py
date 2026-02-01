"""Пошук по Whoosh-індексу за текстом та назвою пісні."""

import json
import os
import re

from whoosh import highlight
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser


def open_existing_index(index_dir: str = 'indexdir'):
    """
    Відкриває існуючий Whoosh-індекс.

    Args:
        index_dir: Директорія з індексом.

    Returns:
        Відкритий індекс.

    Raises:
        FileNotFoundError: Якщо директорія індексу не існує.
    """
    if os.path.exists(index_dir):
        return open_dir(index_dir)
    raise FileNotFoundError('Index directory does not exist')


def find_best_sequence(text: str) -> str | None:
    """
    Витягує найкращий фрагмент з підсвіченого тексту (HTML-теги match).

    Args:
        text: Текст з тегами <b class="match termN">...</b>.

    Returns:
        Очищений фрагмент або None.
    """
    pattern = re.compile(r'((?:<b class="match term\d+">.*?</b>\s*){1,5})')
    matches = pattern.findall(text)
    if not matches:
        return None
    best_match = ''
    max_terms = 0
    for match in matches:
        terms = re.findall(r'<b class="match term\d+">.*?</b>', match)
        if len(terms) > max_terms:
            max_terms = len(terms)
            best_match = match
    remaining_text = text[text.find(best_match) + len(best_match) :].strip()
    next_words = ' '.join(re.split(r'\s+', remaining_text)[:4])
    return re.sub(r'<.*?>', '', best_match).strip() + ' ' + next_words


def _get_hits(hits) -> dict:
    """Перетворює результати пошуку в словник song_id -> {title, part}."""
    results = {}
    for hit in hits:
        text_snippet = hit.highlights('text')
        if not text_snippet:
            text_snippet = hit.highlights('title')
        results[hit['id']] = {
            'title': hit['title'],
            'part': text_snippet,
        }
    return results


def search_songs(query_str: str, index_dir: str = 'indexdir') -> dict:
    """
    Шукає пісні за текстом та назвою в Whoosh-індексі.

    Args:
        query_str: Рядок пошуку.
        index_dir: Директорія з індексом.

    Returns:
        Словник {song_id: {"title": str, "part": str}} з фрагментами збігів.
    """
    ix = open_existing_index(index_dir)
    with ix.searcher() as searcher:
        parser = MultifieldParser(['title', 'text'], schema=ix.schema)
        direct_query = parser.parse(f'"{query_str}"')
        direct_hits = searcher.search(direct_query)
        direct_hits.fragmenter.charlimit = None
        direct_hits.fragmenter = highlight.ContextFragmenter(maxchars=5)
        direct_hits_dict = _get_hits(direct_hits)
        indirect_query = parser.parse(query_str)
        indirect_hits = searcher.search(indirect_query)
        indirect_hits.fragmenter.charlimit = None
        indirect_hits_dict = _get_hits(indirect_hits)
        results = direct_hits_dict
        for song_id in indirect_hits_dict:
            if song_id not in results:
                results[song_id] = indirect_hits_dict[song_id]
    return results


if __name__ == '__main__':
    query = 'ми будемо співати'
    found_songs = search_songs(query)
    print(json.dumps(found_songs, ensure_ascii=False, indent=4))
