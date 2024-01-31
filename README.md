# Homework Bot - Бот для проверки статуса домашней работы в Яндекс.Практикум с помощью telegram
python telegram bot

# Стек:
- Python
- python-dotenv
- python-telegram-bot

# Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:nicros22/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

```
source venv/Scripts/activate
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Записать в переменные окружения (файл .env) необходимые ключи:
- API токен, от Яндекс.Практикум
- токен телеграм-бота
- chat ID телеграмма
