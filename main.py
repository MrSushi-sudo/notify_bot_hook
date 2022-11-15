import pathlib
import threading
import pytz
import sqlite3
import telebot
import schedule

from datetime import datetime
from time import sleep

bot = telebot.TeleBot('5620571226:AAHdC64gER17Xy054c94954Oor4eMDw8PJ0')
conn = sqlite3.connect('notify_bot.db', check_same_thread=False)
conn.row_factory = lambda cursor, row: row[0]
cursor = conn.cursor()

bot_greeting = 'Привет я бот Hook Production для уведомлений об оплате налога'


def db_table_user(user_id: int, username: str, message: str):
    cursor.execute('INSERT OR IGNORE INTO notify_user (user_id, username, message) VALUES (?, ?, ?);', (user_id, username, message))
    conn.commit()


def db_table_date(date_1=None, date_2=None):
    exist_date_1 = cursor.execute('SELECT EXISTS(SELECT date_1 FROM notify_date);').fetchone()
    exist_date_2 = cursor.execute('SELECT EXISTS(SELECT date_2 FROM notify_date);').fetchone()
    if date_1 and exist_date_1:
        cursor.execute('UPDATE notify_date SET date_1 = ?;', (date_1,))
    elif date_2 and exist_date_2:
        cursor.execute('UPDATE notify_date SET date_2 = ?;', (date_2,))
    else:
        cursor.execute('INSERT OR IGNORE INTO notify_date (date_1, date_2) VALUES (?, ?);', (date_1, date_2))
    conn.commit()


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    chat_id = message.chat.id
    username = message.chat.username
    db_table_user(user_id=chat_id, username=username, message='Оплатите налог и вышлите чек')
    bot.send_message(chat_id, text=bot_greeting)


@bot.message_handler(commands=['change_date_1', 'change_date_2'])
def change_settings(message):
    if message.text == '/change_date_1':
        send_msg = bot.send_message(message.chat.id, text='Введите первую дату')
        bot.register_next_step_handler(send_msg, first_date)
    elif message.text == '/change_date_2':
        send_msg = bot.send_message(message.chat.id, text='Введите вторую дату')
        bot.register_next_step_handler(send_msg, second_date)


def first_date(message):
    db_table_date(date_1=message.text)
    bot.send_message(message.chat.id, text='Первая дата изменена')


def second_date(message):
    db_table_date(date_2=message.text)
    bot.send_message(message.chat.id, text='Вторая дата изменена')


@bot.message_handler(commands=['get_all_users'])
def all_users(message):
    text = ''
    users = cursor.execute('SELECT ("ID Пользователя: " || user_id || " Никнейм: @" || username || " Сообщение: " || ifnull(message, "не задано")) FROM notify_user;').fetchall()
    for user in users:
        text += f'<b>{user}</b>\n'
    bot.send_message(message.chat.id, text=text, parse_mode='HTML')


@bot.message_handler(commands=['change_user_message'])
def change_message(message):
    send_msg = bot.send_message(message.chat.id, text='Введите юзернейм пользователя')
    bot.register_next_step_handler(send_msg, select_user)


def select_user(message):
    username = message.text
    send_msg = bot.send_message(message.chat.id, text=f'Выбран пользователь: {username}, введите сообщение:')
    bot.register_next_step_handler(send_msg, new_message, username)


def new_message(message, username):
    # user_message = cursor.execute('SELECT message FROM notify_user WHERE user_id=?;', (username,)).fetchone()
    cursor.execute('UPDATE notify_user SET message=? WHERE user_id=?;', (message.text, username))
    bot.send_message(message.chat.id, text=f'Сообщение изменено, новое сообщение: "{message.text}"')


def auto_send_message():
    users = cursor.execute('SELECT user_id FROM notify_user;').fetchall()
    exist_date_1 = cursor.execute('SELECT date_1 FROM notify_date;').fetchone()
    exist_date_2 = cursor.execute('SELECT date_2 FROM notify_date;').fetchone()
    today = datetime.now(pytz.utc).day
    if exist_date_1 or exist_date_2:
        for user in users:
            if today == exist_date_1 or today == exist_date_2:
                bot.send_message(chat_id=user, text='Пожалуйста оплатите налог')
                send_msg = bot.send_message(user, text='Отправьте чек:')
                bot.register_next_step_handler(send_msg, load_check)


@bot.message_handler(commands=['load_check'])
def load_check(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    pathlib.Path(f'media/check/{message.chat.username}').mkdir(exist_ok=True)
    filename = message.document.file_name + '-' + datetime.now(pytz.utc)
    src = f'media/check/{message.chat.username}' + filename
    with open(src, 'wb') as new_file:
        new_file.write(downloaded_file)
    bot.send_message(message.chat.id, f'Файл отправлен Алине Мельник, по всем вопросам: @melkalina')
    send_msg = bot.send_message(message.chat.username, text='Отправьте чек:')
    bot.register_next_step_handler(send_msg, send_to_office_manager, filename)


def send_to_office_manager(message, filename):
    bot.send_message(399169196, f'Фото чека от @{message.chat.username}')
    bot.send_photo(399169196, filename, 'rb')


# def run_bot():
#     bot.polling(none_stop=True, interval=0)
bot.polling(none_stop=True, interval=0)


def run_scheduler():
    schedule.every().day.at('16:00').do(auto_send_message)

    while True:
        schedule.run_pending()
        sleep(1)


# if __name__ == '__main__':
#     task_1 = threading.Thread(target=run_bot)
#     # task_2 = threading.Thread(target=run_scheduler)
#     task_1.start()
#     # task_2.start()

# schedule.every(1).minutes.do(auto_send_message)
# schedule.every().day.at('18:00').do(send_message)

# @bot.message_handler(commands=['Изменить время'])
# def change_time(time):
