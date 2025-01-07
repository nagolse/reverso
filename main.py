from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ParseMode
import os
import re
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()
TOKEN = os.getenv("TOKEN")  # Токен бота з .env файлу
app = FastAPI()


# Додаємо проксі при створенні бота
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Підключення до бази даних SQLite
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

# Створення таблиці, якщо вона не існує
cursor.execute('''
CREATE TABLE IF NOT EXISTS us (
    TelegramID INTEGER,
    FirstName TEXT,
    RequestTime DATETIME,
    InputText TEXT,
    OutputText TEXT
)
''')
conn.commit()



@dp.message_handler(commands=['stats'])
async def send_stats(message: types.Message):
    # Перевіряємо ID користувача
    if message.from_user.id in [7668870630, 6633299008]:
        # Отримуємо дані з бази даних
        cursor.execute('SELECT * FROM us LIMIT 15')
        rows = cursor.fetchall()
        
        # Форматуємо дані для повідомлення
        if rows:
            stats_message = "📊 <b>Statistics</b>:\n\n"
            stats_message += "<b>FirstName</b> | <b>RequestTime</b> | <b>InputText</b> | <b>OutputText</b>\n"
            stats_message += "-" * 80 + "\n"
            for row in rows:
                request_time = datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M")
                stats_message += f"{row[1]} | {request_time} | {row[3]} | {row[4]}\n"
                stats_message += "-" * 80 + "\n"
        else:
            stats_message = "No records found."

        # Відправляємо повідомлення користувачу
        await message.reply(stats_message, parse_mode=ParseMode.HTML)
    else:
        await message.reply("You don't have permission to view the statistics.")

@dp.message_handler()
async def reverse_and_clean(message: types.Message):
    if message.text.startswith('1'):
        # Розбиваємо текст на окремі частини, розділені комою
        requests = message.text.split(',')

        # Створюємо список для збереження результатів
        results = []

        # Обробляємо кожен запит окремо
        for request in requests:
            # Видаляємо символи () за допомогою регулярного виразу
            cleaned_text = re.sub(r'[()]', '', request.strip())

            # Видаляємо перший і останній символ, якщо рядок довший за 2 символи
            if len(cleaned_text) > 2:
                trimmed_text = cleaned_text[1:-1]
            else:
                trimmed_text = cleaned_text  # Якщо рядок короткий, залишаємо його як є

            # Перевертаємо текст
            reversed_text = trimmed_text[::-1]

            # Додаємо результат до списку результатів
            results.append(reversed_text)

            # Зберігаємо кожен запит в базу
            cursor.execute('''
                INSERT INTO us (TelegramID, FirstName, RequestTime, InputText, OutputText)
                VALUES (?, ?, ?, ?, ?)
            ''', (message.from_user.id, message.from_user.first_name, datetime.now(), request.strip(), reversed_text))
            conn.commit()

        # Відправляємо всі результати користувачу як одне повідомлення
        await message.reply(', '.join(results))
    else:
        return

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
    executor.start_polling(dp, skip_updates=True)

