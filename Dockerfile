FROM python:3.11-slim

WORKDIR /app

# Установи зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируй код
COPY bot.py .

# Создай папки для данных
RUN mkdir -p data/emails images logs

# Запусти бота
# Build v3 - removed .env copy - cache bust 2025-11-02 forced rebuild
CMD ["python", "bot.py"]
