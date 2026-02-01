import language_tool_python
import re
from bot.songs_collector import SongCollector
from fuzzywuzzy import fuzz, process


class InlineSearch(SongCollector):
    def __init__(self):
        super().__init__()
        self.tool = language_tool_python.LanguageTool('uk')
        self.search_pattern = None

    def process_text(self, text):
        if not text:
            return ''
        # Корекція граматики та очищення тексту
        matches = self.tool.check(text)
        corrected_text = language_tool_python.utils.correct(text, matches)
        return re.sub(r"[^\w\s]", '', corrected_text)

    def search_content(self, content, query):
        """Шукає збіги в тексті (назва або лірика) і повертає фрагмент."""
        if not content or not isinstance(content, str):
            return None
        match = process.extractOne(query, content.split('\n'), scorer=fuzz.partial_ratio)
        if match and match[1] > 75:  # Threshold for match quality
            return match[0].strip()
        return None

    def search_songs(self, user_text):
        query = self.process_text(user_text)  # Очищення та корекція запиту
        print(f'Processed query: {query}')
        results = {}

        for song_id, song_data in self.songs_data.items():
            result = self.search_song_data(song_data, query)
            if result:
                results[song_id] = result
            if len(results) >= 50:
                break

        return results

    def search_song_data(self, song_data, query):
        """Циклічно обробляє назву та текст пісні."""
        for content in song_data.values():  # Обробляємо назву і текст пісні
            print(content)
            result = self.search_content(content, query)
            if result:
                return result
        return None

    def format_title(self, title):
        title = title.rstrip(' /')
        if len(title) > 40:
            title = title[:40].rstrip(' /') + "..."
        return title
