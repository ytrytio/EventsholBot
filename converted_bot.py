
#!/usr/bin/env python3

import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from asyncio import run as async_run
from google.cloud import dialogflow_v2 as dialogflow
from google.api_core.exceptions import InvalidArgument
from pathlib import Path
from PIL import Image
from dotenv import dotenv_values

# Загрузка токена и других секретов из файла
secrets = dotenv_values('.env')
TOKEN = secrets["BOT_TOKEN"]

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot=bot)

# Подключение к базе данных SQLite
db = sqlite3.connect('users.db')
cursor = db.cursor()

# Параметры для Dialogflow
DIALOGFLOW_PROJECT_ID = "small-talk-rwvf"
DIALOGFLOW_LANGUAGE_CODE = 'ru'
SESSION_ID = 'sessionId'

session_client = dialogflow.SessionsClient.from_service_account_file('dialog_flow.json')
session_path = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)

@dp.message_handler(Command('start'))
async def start(message: Message):
    await message.reply("Welcome!")

@dp.message_handler(F.text.lower() == 'привет')
async def handle_greeting(message: Message):
    text = message.text
    request = {
        "session": session_path,
        "query_input": {
            "text": {
                "text": text,
                "language_code": DIALOGFLOW_LANGUAGE_CODE,
            }
        }
    }

    try:
        response = session_client.detect_intent(request=request)
        result = response.query_result
        await message.reply(result.fulfillment_text)
    except InvalidArgument as e:
        print(f"ERROR: {e}")

def overlay_images():
    try:
        # Открытие основной карты и флага
        map_img = Image.open("map.png")
        flag_img = Image.open("flag.png")

        # Изменение размера флага
        flag_img = flag_img.resize((100, 100))

        # Наложение флага на карту с указанными координатами
        map_img.paste(flag_img, (300, 450), flag_img if flag_img.mode == 'RGBA' else None)

        # Сохранение результата
        map_img.save("modified_map.png")
        print("Изображение сохранено как modified_map.png")

        # Удаление изображения
        Path("modified_map.png").unlink()
        print("Файл удален")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    # Запуск бота
    async_run(dp.start_polling())
