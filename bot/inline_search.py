import language_tool_python
import re
from bot.songs_collector import SongCollector


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

    def create_flexible_pattern(self, query):
        # Створюємо регулярний вираз, що ігнорує розділові знаки
        flexible_pattern = r'.*' + r'\W*'.join(re.escape(word) for word in query.split()) + r'.*'
        return re.compile(flexible_pattern, re.IGNORECASE)

    def search_content(self, content):
        """Шукає збіги в тексті (назва або лірика) і повертає фрагмент."""
        if not content or not isinstance(content, str):
            return None
        match = self.search_pattern.search(content)
        if match:
            start = content.rfind('\n', 0, match.start()) + 1
            end = content.find('\n', match.end())
            print(f'Start: {start}, End: {end}')
            return content[start:end if end != -1 else len(content)].strip()
        return None

    def search_songs(self, user_text):
        query = self.process_text(user_text)  # Очищення та корекція запиту
        print(f'Processed query: {query}')
        self.search_pattern = self.create_flexible_pattern(query)  # Створення гнучкого патерну
        results = {}

        for song_id, song_data in self.songs_data.items():
            result = self.search_song_data(song_data)
            if result:
                results[song_id] = result
            if len(results) >= 50:
                break

        return results

    def search_song_data(self, song_data):
        """Циклічно обробляє назву та текст пісні."""
        for content in song_data.values():  # Обробляємо назву і текст пісні
            print(content)
            result = self.search_content(content)
            if result:
                return result
        return None

    def format_title(self, title):
        title = title.rstrip(' /')
        if len(title) > 40:
            title = title[:40].rstrip(' /') + "..."
        return title