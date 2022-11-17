import threading
import pytz
import sqlite3
import telebot
import schedule
import magic

from datetime import datetime
from time import sleep
from pathlib import Path
from telebot.types import BotCommand

bot = telebot.TeleBot('5620571226:AAHdC64gER17Xy054c94954Oor4eMDw8PJ0')
conn = sqlite3.connect('notify_bot.db', check_same_thread=False)
conn.row_factory = lambda cursor, row: row[0]
cursor = conn.cursor()
#399169196
stop = False
OFFICE_MANAGER_ID = 677051855
OFFICE_MANAGER_NAME = 'Алине Мельник'
OFFICE_MANAGER_USERNAME = '@melkalina'

month = {'1': 'Января', '2': 'Февраля', '3': 'Марта', '4': 'Апреля', '5': 'Мая', '6': 'Июня',
         '7': 'Июля', '8': 'Августа', '9': 'Сентября', '10': 'Октября', '11': 'Ноября', '12': 'Декабря'}


commands = [BotCommand('help', 'Помощь'), BotCommand('info', 'Информация'),
            BotCommand('exit', 'Выйти из выполняемой команды'),
            BotCommand('get_all_users', 'Вывести всех пользователей (только для администратора)'),
            BotCommand('change_date_1', 'Изменить первую дату (только для администратора)'),
            BotCommand('change_date_2', 'Изменить вторую дату (только для администратора)'),
            BotCommand('change_user_message', 'Изменить сообщение пользователя (только для администратора)'),
            BotCommand('delete_user', 'Удалить пользователя из базы (только для администратора)'),
            BotCommand('load_check', 'Загрузить чек вручную (срабатывает автоматически после уведомления)')
            ]
bot.set_my_commands(commands=commands)


def log(message: str):
    date = datetime.now().strftime('%d-%m-%Y %H:%M')
    print('<!------!>')
    print(f'{message} — {date}')
    with open('bot.log', 'a+') as file:
        file.write(f'{message} — {date}\n')
        file.close()


def db_table_user(user_id: int, username: str, message: str):
    cursor.execute('INSERT OR IGNORE INTO notify_user (user_id, username, message) VALUES (?, ?, ?);',
                   (user_id, username, message))
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
    if chat_id != OFFICE_MANAGER_ID:
        db_table_user(user_id=chat_id, username=username, message='Оплатите налог и вышлите чек')
        log(f'В базу добавлен пользователь @{username}')
    bot.send_message(chat_id, text='Привет я бот Hook Production для уведомлений об оплате налога')


@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
                     text='Бот написан @PpaBwa, пока что работает в тестовом режиме. И я обычно не пишу ботов, не пинайте мне больно.')


@bot.message_handler(commands=['delete_user'])
def delete_user(message):
    if message.chat.id == OFFICE_MANAGER_ID:
        send_msg = bot.send_message(message.chat.id, text='Выберите пользователя для удаления')
        bot.register_next_step_handler(send_msg, delete_from_base)
    else:
        bot.send_message(message.chat.id, text='Эта команда доступна только администраторам')


def delete_from_base(message):
    if message.chat.id == OFFICE_MANAGER_ID:
        user = cursor.execute('SELECT username FROM notify_user WHERE username = ?;', (message.text,)).fetchone()
        if message.text == '/exit':
            bot.send_message(message.chat.id, text='Вы вышли из выполняемой команды')
        elif user:
            cursor.execute('DELETE FROM notify_user WHERE username = ?;', (message.text,))
            log(f'Пользователь {message.text} удален из базы администратором: {OFFICE_MANAGER_USERNAME}')
            bot.send_message(message.chat.id, text=f'Пользователь {message.text} удален из базы')
        else:
            send_msg = bot.send_message(message.chat.id, text='Введенный пользователь не обнаружен в базе, попробуйте ещё раз')
            log(f'Введенный пользователь не обнаружен в базе, попробуйте ещё раз')
            bot.register_next_step_handler(send_msg, delete_from_base)
    else:
        bot.send_message(message.chat.id, text='Эта команда доступна только администраторам')


@bot.message_handler(commands=['change_date_1', 'change_date_2'])
def change_settings(message):
    if message.chat.id == OFFICE_MANAGER_ID:
        if message.text == '/change_date_1':
            send_msg = bot.send_message(message.chat.id, text='Введите первую дату')
            bot.register_next_step_handler(send_msg, first_date)
        elif message.text == '/change_date_2':
            send_msg = bot.send_message(message.chat.id, text='Введите вторую дату')
            bot.register_next_step_handler(send_msg, second_date)
    else:
        bot.send_message(message.chat.id, text='Эта команда доступна только администраторам')


def first_date(message):
    if 0 < int(message.text) <= 31:
        db_table_date(date_1=message.text)
        bot.send_message(message.chat.id, text=f'Первая дата изменена на {message.text}')
        log(f'Первая дата изменена на {message.text} администратором: {OFFICE_MANAGER_ID}')
    elif message.text == '/exit':
        bot.send_message(message.chat.id, text='Вы вышли из выполняемой команды')
    else:
        send_msg = bot.send_message(message.chat.id,
                                    text='Неверный формат даты, введите число (1-31 в зависимости от месяца)')
        log('Неверно введена первая дата')
        bot.register_next_step_handler(send_msg, first_date)


def second_date(message):
    if 0 < int(message.text) <= 31:
        db_table_date(date_2=message.text)
        log(f'Вторая дата изменена на {message.text} администратором: {OFFICE_MANAGER_ID}')
        bot.send_message(message.chat.id, text=f'Вторая дата изменена на {message.text}')
    elif message.text == '/exit':
        bot.send_message(message.chat.id, text='Вы вышли из выполняемой команды')
    else:
        send_msg = bot.send_message(message.chat.id,
                                    text='Неверный формат даты, введите число (1-31 в зависимости от месяца)')
        log('Неверно введена вторая дата')
        bot.register_next_step_handler(send_msg, second_date)


@bot.message_handler(commands=['get_all_users'])
def all_users(message):
    if message.chat.id == OFFICE_MANAGER_ID:
        text = ''
        users = cursor.execute(
            'SELECT ("ID Пользователя: " || user_id || " Никнейм: @" || username || " Сообщение: " || ifnull(message, "не задано")) FROM notify_user;').fetchall()
        for user in users:
            text += f'<b>{user}</b>\n'
        bot.send_message(message.chat.id, text=text, parse_mode='HTML')
        log(f'Выведен список пользователей администратором: {OFFICE_MANAGER_USERNAME}')
    else:
        bot.send_message(message.chat.id, text='Эта команда доступна только администраторам')


@bot.message_handler(commands=['change_user_message'])
def change_message(message):
    if message.chat.id == OFFICE_MANAGER_ID:
        send_msg = bot.send_message(message.chat.id, text='Введите никнейм пользователя')
        bot.register_next_step_handler(send_msg, select_user)
    else:
        bot.send_message(message.chat.id, text='Эта команда доступна только администраторам')


def select_user(message):
    user = cursor.execute('SELECT username FROM notify_user WHERE username = ?;', (message.text,)).fetchone()
    if message.text == '':
        send_msg = bot.send_message(message.chat.id, text='Не введен никнейм пользователя')
        bot.register_next_step_handler(send_msg, select_user)
    elif message.text == '/exit':
        bot.send_message(message.chat.id, text='Вы вышли из выполняемой команды')
    elif not user:
        send_msg = bot.send_message(message.chat.id, text='Пользователь не обнаружен в базе, введите никнейм ещё раз')
        bot.register_next_step_handler(send_msg, select_user)
    else:
        username = message.text
        send_msg = bot.send_message(message.chat.id, text=f'Выбран пользователь: @{username}, введите сообщение:')
        bot.register_next_step_handler(send_msg, new_message, username)


def new_message(message, username):
    cursor.execute('UPDATE notify_user SET message = ? WHERE username = ?;', (message.text, username))
    text = f'Сообщение изменено администратором {OFFICE_MANAGER_USERNAME}, новое сообщение пользователя @{username}: "{message.text}"'
    log(text)
    bot.send_message(message.chat.id, text=text)


def auto_send_message():
    users = cursor.execute('SELECT user_id FROM notify_user;').fetchall()
    exist_date_1 = cursor.execute('SELECT date_1 FROM notify_date;').fetchone()
    exist_date_2 = cursor.execute('SELECT date_2 FROM notify_date;').fetchone()
    today = datetime.now(pytz.utc).day
    if exist_date_1 or exist_date_2:
        for user in users:
            if user != OFFICE_MANAGER_ID and today == exist_date_1 or today == exist_date_2:
                message = cursor.execute('SELECT message FROM notify_user WHERE username = ?;', (user,)).fetchone()
                bot.send_message(user, text=message)
                send_msg = bot.send_message(user, text='Отправьте фото чека:')
                log(f'Уведомление для пользователя @{message.chat.username} за {datetime.now().strftime("%d-%m-%Y %H:%M")} выполнено')
                bot.register_next_step_handler(send_msg, load_check)


@bot.message_handler(commands=['load_check'])
def check(message):
    send_msg = bot.send_message(message.chat.id, text='Загрузите фото чека в формате jpg или png')
    bot.register_next_step_handler(send_msg, load_check)


def load_check(message):
    if message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        image_type = magic.from_buffer(downloaded_file)
        if 'JPG' in image_type or 'JPEG' in image_type or 'PNG' in image_type:
            filename = f'Чек от {message.chat.username}' + ' - ' + datetime.now(pytz.utc).strftime('%d') + ' ' + month[
                str(datetime.now(pytz.utc).month)] + ' ' + datetime.now(pytz.utc).strftime('%Y')
            file_exist = Path(f'checks/{message.chat.username}/{filename}.jpg')
            if file_exist.is_file():
                bot.send_message(message.chat.id, text='Фото за эту дату в данном месяце уже загружено')
            else:
                Path(f'checks/{message.chat.username}').mkdir(parents=True, exist_ok=True)
                src = f'checks/{message.chat.username}/{filename}.jpg'
                with open(src, 'wb') as new_file:
                    new_file.write(downloaded_file)
                bot.send_message(message.chat.id,
                                 f'Файл отправлен {OFFICE_MANAGER_NAME}, по всем вопросам: {OFFICE_MANAGER_USERNAME}')
                bot.send_message(OFFICE_MANAGER_ID,
                                 f'Фото чека от @{message.chat.username} за {datetime.now(pytz.utc).strftime("%d")} '
                                 f'{month[str(datetime.now(pytz.utc).month)]} {datetime.now(pytz.utc).strftime("%Y")}:')
                log(f'Фото чека от @{message.chat.username} за {datetime.now(pytz.utc).strftime("%d")} '
                    f'{month[str(datetime.now(pytz.utc).month)]} {datetime.now(pytz.utc).strftime("%Y")} отправлено')
                bot.send_photo(OFFICE_MANAGER_ID, photo=open(src, 'rb'))
        else:
            send_msg = bot.send_message(message.chat.id, text='Неправильный тип файла (нужно либо jpg, либо png), попробуйте ещё раз')
            log(f'Пользователь @{message.chat.username} пытался отправить неправильный тип файла')
            bot.register_next_step_handler(send_msg, load_check)
    elif message.text == '/exit':
        bot.send_message(message.chat.id, text='Вы вышли из выполняемой команды')
    else:
        send_msg = bot.send_message(message.chat.id,
                                    text='Неправильный тип файла (нужно либо jpg, либо png), попробуйте ещё раз')
        log(f'Пользователь @{message.chat.username} пытался отправить неправильный тип файла')
        bot.register_next_step_handler(send_msg, load_check)


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
