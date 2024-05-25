import requests
import base64
import sys
sys.path.append('..')

from config import APP_ID, SECRET

TITLE_SEARCH_URL = 'https://api.planningcenteronline.com/services/v2/songs?where[title]='
URL_FOR_SONG_ID = 'https://api.planningcenteronline.com/services/v2/songs/'

app_id = APP_ID
secret = SECRET

user_input = input('Введи назву для пошуку: ')

credentials = f'{app_id}:{secret}'
credentials_b64 = base64.b64encode(credentials.encode()).decode()

headers = {
    'Authorization': f'Basic {credentials_b64}'
}

def get_response_json(request_url, headers):
    complete_url = ''.join([request_url, user_input])
    response = requests.get(complete_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Помилка {response.status_code}: {response.text}')

def get_songs_dict(data):
    songs_dict = {}
    for song in data['data']:
        song_title = song['attributes']['title']
        song_id = song['id']
        songs_dict[song_title] = song_id
    return songs_dict

def choose_song(songs_dict):
    [print(f"{i + 1}. {song_title}") for i, song_title in enumerate(songs_dict)]
    chosen_song = int(input('Введи номер вибраної пісні: '))
    print(chosen_song)
    chosen_song_id = list(songs_dict.values())[chosen_song]
    print(chosen_song_id)
    return chosen_song_id

def get_song_text(data):
    lyrics = data['data']['attributes']['lyrics']
    print(lyrics)


title_search_data = get_response_json(TITLE_SEARCH_URL, headers)
if title_search_data is not None:
    songs_dict = get_songs_dict(title_search_data)
    chosen_song_id = choose_song(songs_dict)
    if chosen_song_id is not None:
        chosen_song_url = ''.join([URL_FOR_SONG_ID, chosen_song_id, '/arrangements'])
        print(chosen_song_url)
        song_search_data = get_response_json(chosen_song_url, headers)
        if song_search_data is not None:
            get_song_text(song_search_data)


