from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from whoosh.analysis import StemmingAnalyzer
import json
import os

# Створюємо схему для збереження даних
schema = Schema(id=ID(stored=True), title=TEXT(stored=True, analyzer=StemmingAnalyzer()),
                text=TEXT(stored=True, analyzer=StemmingAnalyzer()))


# Функція для створення індексу
def create_index(songs):
    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
    ix = create_in("indexdir", schema)
    writer = ix.writer()

    for song_id, song_data in songs.items():
        writer.add_document(id=song_id, title=song_data["title"], text=song_data["text"])

    writer.commit()
    return ix


# Відкриваємо існуючий індекс
def open_existing_index():
    if os.path.exists("indexdir"):
        return open_dir("indexdir")
    else:
        raise Exception("Index directory does not exist")


# Функція для пошуку за текстом та назвою пісні
def search_songs(ix, query_str):
    results = {}
    with ix.searcher() as searcher:
        parser = MultifieldParser(["title", "text"], schema=ix.schema)
        query = parser.parse(query_str)
        hits = searcher.search(query)

        for hit in hits:
            # Використовуємо highlight() з об'єктом hit
            text_snippet = hit.highlights("text") or hit["text"]
            results[hit["id"]] = {
                "title": hit["title"],
                "text": hit["text"],
                "part": text_snippet
            }
    return results


def get_songs_from_json():
    with open('transformed_songs_data.json', 'r', encoding='utf-8') as file:
        songs = json.load(file)
        return songs


# Дані про пісні
songs = get_songs_from_json()

# Створюємо індекс
# ix = create_index(songs)

# Відкриваємо існуючий індекс
ix = open_existing_index()

# Пошук за запитом
query = "ім'я твоє"
found_songs = search_songs(ix, query)
print(found_songs)
