import sqlite3
import telebot
import schedule

from time import sleep


bot = telebot.TeleBot('5620571226:AAHdC64gER17Xy054c94954Oor4eMDw8PJ0')
conn = sqlite3.connect('notify_bot.db', check_same_thread=False)
conn.row_factory = lambda cursor, row: row[0]
cursor = conn.cursor()


bot_greeting = 'Привет я бот Hook Production для уведомлений об оплате налога'


def db_table_val(user_id: int):
    cursor.execute('INSERT OR IGNORE INTO notify_user (user_id) VALUES (?)', (user_id,))
    conn.commit()


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    chat_id = message.chat.id
    db_table_val(user_id=chat_id)
    bot.send_message(chat_id, text=bot_greeting)


def auto_send_message():
    users = cursor.execute('SELECT user_id FROM notify_user').fetchall()
    for user in users:
        bot.send_message(chat_id=user, text='Пожалуйста оплатите налог')


bot.polling(none_stop=True)

schedule.every(5).seconds.do(auto_send_message)

while True:
    schedule.run_pending()
    sleep(1)

# schedule.every(1).minutes.do(auto_send_message)
# schedule.every().day.at('18:00').do(send_message)

# @bot.message_handler(commands=['Изменить время'])
# def change_time(time):
