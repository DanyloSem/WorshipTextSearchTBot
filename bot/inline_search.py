import language_tool_python
import json
import re


class InlineSearch:
    def __init__(self):
        self.tool = language_tool_python.LanguageTool('uk')
        self.cleaned_songs = self.clean_songs()

    def words_corrector(self, text):
        matches = self.tool.check(text)
        corrected_text = language_tool_python.utils.correct(text, matches)
        user_text = self.clean_text(corrected_text)
        return user_text

    def get_songs_from_json(self):
        with open('songs_data.json', 'r', encoding='utf-8') as f:
            songs = json.load(f)
        return songs

    def clean_text(self, text):
        if not text:
            return ''
        # Видаляє всі розділові знаки, крім апострофів
        return re.sub(r"[^\w\s'’]", '', text).lower()

    def clean_songs(self):
        songs = self.get_songs_from_json()
        cleaned_songs = {}
        for song_id, song_data in songs.items():
            cleaned_song_data = {}
            for key, value in song_data.items():
                cleaned_key = self.clean_text(key)
                cleaned_value = self.clean_text(value)
                cleaned_song_data[cleaned_key] = cleaned_value
            cleaned_songs[song_id] = cleaned_song_data
        return cleaned_songs

    def search_songs(self, user_text):
        query = self.words_corrector(user_text)
        songs = self.cleaned_songs
        results = []
        for song_id, song_data in songs.items():
            for title, lyrics in song_data.items():
                if query in lyrics or query in title:
                    results.append(song_id)
                    if len(results) >= 50:  # Обмеження в 50 пісень
                        break
            if len(results) >= 50:  # Перевірка після внутрішнього циклу
                break
        return results


if __name__ == "__main__":
    search = InlineSearch()
    query = "всім серцем"
    results = search.search_songs(query)
    for song_id in results:
        print(song_id)
