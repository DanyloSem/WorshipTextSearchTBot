import requests
import base64
import sys
sys.path.append('..')

from config import APP_ID, SECRET

url = 'https://api.planningcenteronline.com/services/v2/songs/24393585/arrangements'
app_id = APP_ID
secret = SECRET

# Об'єднуємо ім'я користувача та пароль у рядок та кодуємо його в формат Base64
credentials = f'{app_id}:{secret}'
credentials_b64 = base64.b64encode(credentials.encode()).decode()

# Встановлюємо заголовок авторизації з закодованими даними
headers = {
    'Authorization': f'Basic {credentials_b64}'
}

# Виконуємо GET-запит з використанням зазначеного URL та заголовків
response = requests.get(url, headers=headers)

# Перевіряємо статус відповіді та виводимо результат
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f'Помилка {response.status_code}: {response.text}')