import os
import requests
import base64

from dotenv import load_dotenv


TITLE_SEARCH_URL = 'https://api.planningcenteronline.com/services/v2/songs?order=title&where[title]='
LYRICS_SEARCH_URL = 'https://api.planningcenteronline.com/services/v2/songs?order=title&where[lyrics]='

def get_headers():
    load_dotenv()
    app_id = os.getenv('APP_ID')
    secret = os.getenv('SECRET')

    credentials = f'{app_id}:{secret}'
    credentials_b64 = base64.b64encode(credentials.encode()).decode()

    headers = {
        'Authorization': f'Basic {credentials_b64}'
    }
    return headers

def choose_search(search_method):
    if search_method == '📚Пошук за назвою':
        return TITLE_SEARCH_URL
    if search_method == '📝Пошук за текстом':
        return LYRICS_SEARCH_URL

def get_response_json(request_url, headers):
    response = requests.get(request_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Помилка {response.status_code}: {response.text}')
        return None

def fetch_songs_dict(song_data, songs_dict):
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

def get_songs_dict(search_data):
    search_url = choose_search(search_data['search_method'])
    search_text = search_data['search_text']
    complete_search_url = ''.join([search_url, search_text])

    headers = get_headers()
    songs_data = get_response_json(complete_search_url, headers)

    songs_dict = {}
    songs_dict = fetch_songs_dict(songs_data, songs_dict)
    
    while 'next' in songs_data['links']:
        songs_data = get_response_json(songs_data['links']['next'], headers)
        songs_dict = fetch_songs_dict(songs_data, songs_dict)
    return songs_dict

def get_song_text(song_url):
    headers = get_headers()
    song_data = get_response_json(f'{song_url}/arrangements', headers)
    lyrics = song_data['data'][0]['attributes'].get('lyrics', 'Текст пісні відсутній.')
    return lyrics
