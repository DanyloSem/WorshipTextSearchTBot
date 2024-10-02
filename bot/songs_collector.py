from bot.song_search import SongSearchService
import time
import json


class SongCollector(SongSearchService):
    def __init__(self):
        super().__init__()  # Initialize the parent class
        self.songs_ids = self.collect_songs_ids()
        self.songs_data = self.collect_songs_data()

    def collect_songs_ids(self):
        songs_ids = {}
        url = 'https://api.planningcenteronline.com/services/v2/songs?per_page=100'
        songs_data = self._get_response_json(url)
        while songs_data:
            for song in songs_data['data']:
                songs_ids[song['id']] = song['attributes']['title']
            next_url = songs_data['links'].get('next')
            if not next_url:
                break
            songs_data = self._get_response_json(next_url)
        return songs_ids

    def collect_songs_data(self):
        songs_data = {}
        url = 'https://api.planningcenteronline.com/services/v2/songs/'
        for index, (song_id, song_title) in enumerate(self.songs_ids.items(), start=1):
            song_data = self._get_response_json(f'{url}{song_id}/arrangements')
            songs_data[song_id] = {
                song_title: song_data['data'][0]['attributes'].get('lyrics', 'Текст пісні відсутній.')
            }
            time.sleep(0.21)  # Add a delay to ensure 100 requests in 21 seconds
            print(f'Collected data for song #{index}: {song_title}')
        return songs_data

    def save_songs_data_to_json(self, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.songs_data, f, ensure_ascii=False, indent=4)


# Example usage:

