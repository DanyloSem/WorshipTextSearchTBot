from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser
from whoosh import highlight
import json
import os
import re


# Відкриваємо існуючий індекс
def open_existing_index():
    if os.path.exists("indexdir"):
        return open_dir("indexdir")
    else:
        raise Exception("Index directory does not exist")

def find_best_sequence(text):
    pattern = re.compile(r"((?:<b class=\"match term\d+\">.*?</b>\s*){1,5})")
    matches = pattern.findall(text)

    if not matches:
        return None

    best_match = ""
    max_terms = 0

    for match in matches:
        terms = re.findall(r"<b class=\"match term\d+\">.*?</b>", match)
        if len(terms) > max_terms:
            max_terms = len(terms)
            best_match = match

    # Знайдемо наступні 4 слова після останнього знайденого терміну
    remaining_text = text[text.find(best_match) + len(best_match):].strip()
    next_words = ' '.join(re.split(r'\s+', remaining_text)[:4])

    return re.sub(r'<.*?>', '', best_match).strip() + ' ' + next_words

# Приклад використання
# text = 'І славити Його Ім\'я.\n\n<b class="match term0">Ми</b> будем танцювати,\n<b class="match term0">Ми</b> <b class="match term1">будемо</b> <b class="match term2">співати</b>,\n<b class="match term0">Ми</b> будем прославляти,\n<b class="match term0">Ми</b> <b class="match term1">будемо</b> радіти'
# result = find_best_sequence(text)
# print(result)

# Функція для пошуку за текстом та назвою пісні
def search_songs(query_str):
    ix = open_existing_index()
    with ix.searcher() as searcher:
        parser = MultifieldParser(["title", "text"], schema=ix.schema)

        # Пошук точного співпадіння
        direct_query = parser.parse(f'"{query_str}"') # - пошук за точним запитом
        direct_hits = searcher.search(direct_query)
        direct_hits.fragmenter.charlimit = None  # Відключаємо обмеження на кількість символів
        direct_hits.fragmenter = highlight.ContextFragmenter(maxchars=5)
        print(f"-----------------------------{direct_hits}")
        direct_hits_dict = get_hits(direct_hits)
        print(f"-----------------------------{direct_hits_dict}")
        # print(direct_hits_dict)

        # Пошук за окремими словами
        indirect_query = parser.parse(query_str)  # - пошук за кожним окремим словом
        indirect_hits = searcher.search(indirect_query)
        indirect_hits.fragmenter.charlimit = None  # Відключаємо обмеження на кількість символів
        indirect_hits_dict = get_hits(indirect_hits)
        # print(indirect_hits_dict)

        # formatted_direct_hits = {}
        # for direct_hit in direct_hits_dict:
        #     formatted_direct_hit = find_best_sequence(direct_hits_dict[direct_hit]["part"])
        #     formatted_direct_hits[direct_hit] = {
        #         "title": direct_hits_dict[direct_hit]["title"],
        #         "part": formatted_direct_hit
        #     }

        # Об'єднуємо результати
        # Якщо пісня знайдена за точним запитом, використовуємо її
        # Якщо ні, використовуємо результати пошуку за окремими словами
        results = direct_hits_dict
        for song_id in indirect_hits_dict:
            if song_id not in results:
                results[song_id] = indirect_hits_dict[song_id]
        # query = parser.parse(query_str) - пошук за кожним окремим словом
    return results


def get_hits(hits):
    results = {}
    for hit in hits:
        # Використовуємо highlight() з об'єктом hit
        # text_snippet = get_highlight_with_next_words(highlighted_text)
        text_snippet = hit.highlights("text")
        if not text_snippet:
            text_snippet = hit.highlights("title")
        results[hit["id"]] = {
            "title": hit["title"],  # Повертаємо назву пісні
            # "text": hit["text"],  # Повертаємо текст пісні
            "part": text_snippet  # Повертаємо фрагмент тексту
        }
    return results

# Відкриваємо існуючий індекс


# Пошук за запитом
query = "ми будемо співати"
found_songs = search_songs(query)
print(json.dumps(found_songs, ensure_ascii=False, indent=4))
