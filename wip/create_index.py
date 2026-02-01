from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
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


def get_songs_from_json():
    with open('transformed_songs_data.json', 'r', encoding='utf-8') as file:
        songs = json.load(file)
        return songs


# Дані про пісні
songs = get_songs_from_json()

# Створюємо індекс
create_index(songs)