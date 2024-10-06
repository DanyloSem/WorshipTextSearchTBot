from bot.songs_collector import SongCollector
import language_tool_python


class InlineSearch(SongCollector):
    def __init__(self):
        super().__init__()
        self.tool = language_tool_python.LanguageTool('uk')

    def words_corrector(self, text):
        matches = self.tool.check(text)
        corrected_text = language_tool_python.utils.correct(text, matches)
        user_text = self.clean_text(corrected_text)
        return user_text

    def search_songs(self, user_text):
        query = self.words_corrector(user_text)
        songs = self.modified_songs
        song_ids = []
        for song_id, song_data in songs.items():
            for title, lyrics in song_data.items():
                if query in lyrics or query in title:
                    song_ids.append(song_id)
                    if len(song_ids) >= 50:  # Обмеження в 50 пісень
                        break
            if len(song_ids) >= 50:  # Перевірка після внутрішнього циклу
                break
        return song_ids
