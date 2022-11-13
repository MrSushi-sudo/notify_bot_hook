import telebot

bot = telebot.TeleBot('')

bot_greeting = 'Привет я бот Hook Production для уведомления об оплате налога'


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message):
    bot.send_message(message.chat.id, 'Welcome', bot_greeting)


# @bot.message_handler(commands=['Изменить время'])
# def change_time(time):
