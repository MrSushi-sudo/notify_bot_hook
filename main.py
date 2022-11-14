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


def db_table_user(user_id: int):
    cursor.execute('INSERT OR IGNORE INTO notify_user (user_id) VALUES (?)', (user_id,))
    conn.commit()


def db_table_date(date_1=None, date_2=None):
    exist_date_1 = cursor.execute('SELECT EXISTS(SELECT date_1 FROM notify_date)').fetchone()
    exist_date_2 = cursor.execute('SELECT EXISTS(SELECT date_2 FROM notify_date)').fetchone()
    if date_1 and exist_date_1:
        cursor.execute('UPDATE notify_date SET date_1 = ?;', (date_1,))
    elif date_2 and exist_date_2:
        cursor.execute('UPDATE notify_date SET date_2 = ?;', (date_2,))
    else:
        cursor.execute('INSERT OR IGNORE INTO notify_date (date_1, date_2) VALUES (?, ?)', (date_1, date_2))
    conn.commit()


# def db_table_date_2(date_2: int):
#     cursor.execute('INSERT OR IGNORE INTO notify_date (date_2) VALUES (?)', (date_2,))
#     conn.commit()


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    chat_id = message.chat.id
    db_table_user(user_id=chat_id)
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
    users = cursor.execute('SELECT user_id FROM notify_user').fetchall()
    for user in users:
        text += f'<b>Юзернейм: {user.username}</b>\n' \
                f'<b>Сообщение {user.message}</b>\n' \
                f'<b>ID юзера: {user.user_id}</b>\n'
    bot.send_message(message.chat.id, text=text, parse_mode='HTML')


def auto_send_message():
    users = cursor.execute('SELECT user_id FROM notify_user').fetchall()
    exist_date_1 = cursor.execute('SELECT date_1 FROM notify_date').fetchone()
    exist_date_2 = cursor.execute('SELECT date_2 FROM notify_date').fetchone()
    today = datetime.now(pytz.utc).day
    if exist_date_1 or exist_date_2:
        for user in users:
            if today == exist_date_1 or today == exist_date_2:
                bot.send_message(chat_id=user, text='Пожалуйста оплатите налог')


# schedule.every().day().at('17:00').do(auto_send_message)

def run_bot():
    bot.polling(none_stop=True, interval=0)


def run_scheduler():
    schedule.every().day.at('16:00').do(auto_send_message)

    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    task_1 = threading.Thread(target=run_bot)
    task_2 = threading.Thread(target=run_scheduler)
    task_1.start()
    task_2.start()

# schedule.every(1).minutes.do(auto_send_message)
# schedule.every().day.at('18:00').do(send_message)

# @bot.message_handler(commands=['Изменить время'])
# def change_time(time):
