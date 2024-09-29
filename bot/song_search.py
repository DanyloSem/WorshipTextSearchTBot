import requests
import base64
from logs.log_config import logger
from config import CLIENT_ID, SECRET


class SongSearchService:
    def __init__(self):
        self.headers = self.get_headers()
        self.url = 'https://api.planningcenteronline.com/services/v2/songs?per_page=100&order=title&where'

    def _get_response_json(self, request_url):
        response = requests.get(request_url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f'Помилка {response.status_code}: {response.text}')
            return None

    def get_headers(self):
        credentials = f'{CLIENT_ID}:{SECRET}'
        credentials_b64 = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {credentials_b64}'
        }
        return headers

    def choose_search(self, search_data):
        if search_data['search_method'] == '📚Пошук за назвою':
            return f'{self.url}[title]={search_data['search_text']}'

        elif search_data['search_method'] == '📝Пошук за текстом':
            return f'{self.url}[lyrics]={search_data['search_text']}'

    def fetch_songs_dict(self, song_data, songs_dict):
        index = len(songs_dict)
        for song in song_data['data']:
            song_title = song['attributes']['title']
            song_url = song['links']['self']
            index += 1
            songs_dict[index] = {
                'title': song_title,
                'url': song_url
            }
        return songs_dict

    def get_songs_dict(self, search_data):
        search_url = self.choose_search(search_data)
        songs_data = self._get_response_json(search_url)

        songs_dict = {}
        songs_dict = self.fetch_songs_dict(songs_data, songs_dict)
        while 'next' in songs_data['links']:
            songs_data = self._get_response_json(songs_data['links']['next'])
            songs_dict = self.fetch_songs_dict(songs_data, songs_dict)

        logger.info(f'Songs dict: {songs_dict}')
        return songs_dict

    def get_song_text(self, song_url):
        song_data = self._get_response_json(f'{song_url}/arrangements')
        lyrics = song_data['data'][0]['attributes'].get('lyrics', 'Текст пісні відсутній.')
        return lyrics
