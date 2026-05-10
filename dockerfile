FROM python:3.14-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем проект
COPY . .

# Создаем папку для статики
RUN mkdir -p staticfiles

EXPOSE 8000

CMD ["gunicorn", "lab8.wsgi:application", "--bind", "0.0.0.0:8000"]