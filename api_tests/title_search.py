import requests
import base64
import sys
sys.path.append('..')

from config import APP_ID, SECRET

TITLE_SEARCH_URL = 'https://api.planningcenteronline.com/services/v2/songs?where[title]='

app_id = APP_ID
secret = SECRET

user_input = input('Введи назву для пошуку: ')

credentials = f'{app_id}:{secret}'
credentials_b64 = base64.b64encode(credentials.encode()).decode()

headers = {
    'Authorization': f'Basic {credentials_b64}'
}

def get_response_json(request_url, headers):
    response = requests.get(request_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Помилка {response.status_code}: {response.text}')

def get_songs_dict(data):
    songs_dict = {}
    index = 0
    for song in data['data']:
        song_title = song['attributes']['title']
        song_url = song['links']['self']
        index += 1
        songs_dict[index] = {
            'title': song_title,
            'url': song_url
        }
    return songs_dict

def choose_song(songs_dict):
    [print(f"{index}. {song_atrs['title']}") for index, song_atrs in songs_dict.items()]
    chosen_song = int(input('Введи номер вибраної пісні: '))
    return chosen_song

def get_song_text(song_data):
    lyrics = song_data['data'][0]['attributes']['lyrics']
    print(lyrics)


complete_search_url = ''.join([TITLE_SEARCH_URL, user_input])
title_search_data = get_response_json(complete_search_url, headers)
songs_dict = get_songs_dict(title_search_data)
chosen_song = choose_song(songs_dict)
chosen_song_url = ''.join([songs_dict[chosen_song]['url'], '/arrangements'])
song_data = get_response_json(chosen_song_url, headers)
get_song_text(song_data)


