import requests
import base64
# from logs.log_config import logger
from config import CLIENT_ID, SECRET
import concurrent.futures
import language_tool_python


class InlineSearch:
    def __init__(self):
        self.headers = self._get_headers()
        self.tool = language_tool_python.LanguageTool('uk')
        self.url = 'https://api.planningcenteronline.com/services/v2/songs?per_page=100&order=title&where'

    def _get_response_json(self, request_url):
        response = requests.get(request_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Помилка {response.status_code}: {response.text}')
            return None

    def _get_headers(self):
        credentials = f'{CLIENT_ID}:{SECRET}'
        credentials_b64 = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {credentials_b64}'
        }
        return headers

    def correct_word(self, text):
        matches = self.tool.check(text)
        corrected_text = language_tool_python.utils.correct(text, matches)
        return corrected_text

    def get_songs_by_text(self, word):
        # Перевірка орфографії та виправлення слова
        corrected_word = self.correct_word(word)
        print(f'Corrected word: {corrected_word}')

        def fetch_songs(param):
            search_url = f'{self.url}[{param}]={corrected_word}'
            response = self._get_response_json(search_url)
            return response['data']

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_title = executor.submit(fetch_songs, 'title')
            future_lyrics = executor.submit(fetch_songs, 'lyrics')

            songs_by_title_list = future_title.result()
            songs_by_lyrics_list = future_lyrics.result()

        # Об'єднуємо списки
        merged_songs = songs_by_title_list + songs_by_lyrics_list

        # Використовуємо list comprehension для фільтрації унікальних пісень
        unique_ids = set()
        all_songs = [song for song in merged_songs if song['id'] not in unique_ids and not unique_ids.add(song['id'])]

        return all_songs


# test = TestService()
# print(test.get_all_songs_by_title('Лрбов твоя'))
