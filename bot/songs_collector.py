from bot.song_search import SongSearchService
import time
import json


class SongCollector(SongSearchService):
    def __init__(self):
        super().__init__()  # Initialize the parent class
        # self.songs_ids = self.collect_songs_ids()
        # self.songs_data = self.collect_songs_data()
        self.songs_data = self.get_songs_from_json()
        # self.modified_songs = self.modify_songs()

    def get_songs_from_json(self):
        with open('songs_data.json', 'r', encoding='utf-8') as file:
            songs = json.load(file)
            return songs

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

    # def modify_songs(self):
    #     songs = self.songs_data
    #     cleaned_songs = {}
    #     for song_id, song_data in songs.items():
    #         cleaned_song_data = {}
    #         for key, value in song_data.items():
    #             cleaned_key = self.clean_text(key)
    #             cleaned_value = self.clean_text(value)
    #             cleaned_song_data[cleaned_key] = cleaned_value
    #         cleaned_songs[song_id] = cleaned_song_data
    #     return cleaned_songs
