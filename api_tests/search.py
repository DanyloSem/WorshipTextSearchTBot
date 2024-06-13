import requests
import base64
import sys
sys.path.append('..')
from config import APP_ID, SECRET


LYRICS_SEARCH_URL = 'https://api.planningcenteronline.com/services/v2/songs?order=title&where[lyrics]='
TITLE_SEARCH_URL = 'https://api.planningcenteronline.com/services/v2/songs?order=title&where[title]='

app_id = APP_ID
secret = SECRET


def choose_search():
    while True:
        search_type = input('1.Пошук за назвою\n2.Пошук за текстом\nВиберіть варіант: ')
        if search_type == '1':
            return TITLE_SEARCH_URL
        if search_type == '2':
            return LYRICS_SEARCH_URL
        else:
            print('Введіть цифру 1 або 2.')

def validate_song_title(title):
    if not title.isalpha():
        print('Назва пісні має містити лише букви. Спробуйте ще раз.')
        return False
    return True

def validate_song_choice(choice, max_index):
    if not choice.isdigit() or not (1 <= int(choice) <= max_index):
        print(f'Введіть число від 1 до {max_index}. Спробуйте ще раз.')
        return False
    return True

def get_response_json(request_url, headers):
    response = requests.get(request_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Помилка {response.status_code}: {response.text}')
        return None

def get_songs_dict(data, existing_songs_dict):
    index = len(existing_songs_dict)
    for song in data['data']:
        song_title = song['attributes']['title']
        song_url = song['links']['self']
        index += 1
        existing_songs_dict[index] = {
            'title': song_title,
            'url': song_url
        }
    return existing_songs_dict

def choose_song(songs_dict):
    for index, song_atrs in songs_dict.items():
        print(f"{index}. {song_atrs['title']}")
    while True:
        chosen_song = input('Введи номер вибраної пісні: ')
        if validate_song_choice(chosen_song, len(songs_dict)):
            return int(chosen_song)

def get_song_text(song_data):
    if 'data' in song_data and song_data['data']:
        lyrics = song_data['data'][0]['attributes'].get('lyrics', 'Текст пісні відсутній.')
        print(lyrics)
    else:
        print('Текст пісні не знайдено.')

search_url = choose_search()
while True:
    user_input = input('Введи назву пісні для пошуку: ')
    if validate_song_title(user_input):
        break


credentials = f'{app_id}:{secret}'
credentials_b64 = base64.b64encode(credentials.encode()).decode()

headers = {
    'Authorization': f'Basic {credentials_b64}'
}

songs_dict = {}

complete_search_url = ''.join([search_url, user_input])
title_search_data = get_response_json(complete_search_url, headers)

if title_search_data is not None:
    songs_dict = get_songs_dict(title_search_data, songs_dict)
    while 'next' in title_search_data['links']:
        title_search_data = get_response_json(title_search_data['links']['next'], headers)
        if title_search_data is not None:
            songs_dict = get_songs_dict(title_search_data, songs_dict)
        else:
            break

    if songs_dict:
        chosen_song = choose_song(songs_dict)
        chosen_song_url = ''.join([songs_dict[chosen_song]['url'], '/arrangements'])
        song_data = get_response_json(chosen_song_url, headers)
        if song_data is not None:
            get_song_text(song_data)
    else:
        print('Пісні не знайдено.')
else:
    print('Пісні не знайдено.')
