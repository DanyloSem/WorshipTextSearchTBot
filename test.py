import re


def get_match_by_count(text, desired_count):
    ''' Логіка отримання повного збігу з запитом, віштовхуючись від кількості слів в запиті'''
    pattern = rf'(<b class="match term\d+">[^<]+</b>\s*){{{desired_count}}}'
    match = re.search(pattern, text)
    return match.group() if match else None


# Текст рядка
text = '''І славити Його Ім'я.\n\n<b class="match term0">Ми</b> будем танцювати,\n<b class="match term0">Ми</b> <b class="match term1">будемо</b> співати,\n<b class="match term0">Ми</b> будем прославляти,\n<b class="match term0">Ми</b> <b class="match term1">будемо</b> <b class="match term2">радіти</b>'''

# Бажана кількість підряд тегів
desired_count = 3

match = get_match_by_count(text, desired_count)

# Перевірка, чи є збіг
if match:
    # Виводимо знайдений текст
    print(f"Знайдено {desired_count} частинки підряд: {match.group()}")
else:
    print(f"{desired_count} частинки підряд не знайдено.")


def find_fragment_and_words(text, fragment):
    # Знайдемо індекс початку фрагмента
    start_index = text.find(fragment)

    if start_index == -1:
        return None  # Якщо фрагмент не знайдений

    # Витягнемо сам фрагмент
    fragment_end_index = start_index + len(fragment)
    result = text[start_index:fragment_end_index]

    # Тепер знаходимо наступні слова
    remaining_text = text[fragment_end_index:].strip()

    # Розділяємо на слова
    words = remaining_text.split()

    # Додаємо до результату наступні 0-4 слова
    result += ' ' + ' '.join(words[:4])

    return result