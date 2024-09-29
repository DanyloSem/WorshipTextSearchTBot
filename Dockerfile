# Вказуємо базовий образ, який містить Python
FROM python:3.12-slim

# Вказуємо директорію в контейнері для нашого проекту
WORKDIR /worship_text_tbot

# Копіюємо файли з локальної машини в контейнер
COPY requirements.txt .

# Встановлюємо бібліотеки, що зазначені в requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь код проекту в контейнер
COPY . .

# Вказуємо команду для запуску нашого бота
CMD ["python3", "run.py"]