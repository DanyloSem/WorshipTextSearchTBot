import language_tool_python
import re
from bot.songs_collector import SongCollector


class InlineSearch(SongCollector):
    def __init__(self):
        super().__init__()
        self.tool = language_tool_python.LanguageTool('uk')

    def process_text(self, text):
        if not text:
            return ''
        # Корекція граматики та очищення тексту
        matches = self.tool.check(text)
        corrected_text = language_tool_python.utils.correct(text, matches)
        return re.sub(r"[^\w\s]", '', corrected_text)

    def create_flexible_pattern(self, query):
        # Очищуємо запит користувача від розділових знаків
        cleaned_query = re.sub(r"[^\w\s]", '', query)
        # Створюємо регулярний вираз, що ігнорує розділові знаки
        flexible_pattern = r'.*' + r'\W*'.join(re.escape(word) for word in cleaned_query.split()) + r'.*'
        return re.compile(flexible_pattern, re.IGNORECASE)

    def search_content(self, content, search_pattern, query):
        """Шукає збіги в тексті (назва або лірика) і повертає фрагмент."""
        if not content or not isinstance(content, str):
            return None
        match = search_pattern.search(content)
        if match:
            original_match = re.search(re.escape(query), content, re.IGNORECASE)
            if original_match:
                start = content.rfind('\n', 0, original_match.start()) + 1
                end = content.find('\n', original_match.end())
                return content[start:end if end != -1 else len(content)].strip()
        return None

    def search_songs(self, user_text):
        query = self.process_text(user_text)  # Очищення та корекція запиту
        search_pattern = self.create_flexible_pattern(query)  # Створення гнучкого патерну
        results = {}

        for song_id, song_data in self.songs_data.items():
            result = self.search_song_data(song_data, search_pattern, query)
            if result:
                results[song_id] = result
            if len(results) >= 50:
                break

        return results

    def search_song_data(self, song_data, search_pattern, query):
        """Шукає збіги в назві або ліриці пісні."""
        for content in song_data.values():  # Обробляємо назву і текст пісні
            result = self.search_content(content, search_pattern, query)
            if result:
                return result
        return None
