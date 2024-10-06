import re

def clean_text(text):
    # Видаляє всі розділові знаки, крім апострофів (звичайного і спеціального Юнікоду)
    return re.sub(r"[^\w\s'’]", '', text).lower()

# Тестовий рядок
text = "славлю я Твоє Ім’я!"

# Очищення тексту
cleaned_text = clean_text(text)

print(f"Original: {text}")
print(f"Cleaned: {cleaned_text}")