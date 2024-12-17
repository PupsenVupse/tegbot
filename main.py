import telebot
import datetime
import threading

bot = telebot.TeleBot('7886182046:AAGrBiAPs47ECoLSBosaRVItqGLQvqdZr5E')

# Словарь для хранения данных пользователей
user_data = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет! Я бот-напоминалка. Чтобы создать напоминание, введите /reminder.')

@bot.message_handler(commands=['reminder'])
def reminder_message(message):
    bot.send_message(message.chat.id, 'Введите название напоминания:')
    bot.register_next_step_handler(message, set_reminder_name)

def set_reminder_name(message):
    user_data[message.chat.id] = {'reminder_name': message.text}
    bot.send_message(message.chat.id, 'Нужно ли вам периодическое напоминание? (да/нет)')

@bot.message_handler(func=lambda message: message.text.lower() in ['да', 'нет'])
def handle_periodicity_decision(message):
    if message.text.lower() == 'да':
        bot.send_message(message.chat.id, 'Выберите периодичность напоминания в минутах:', reply_markup=create_periodicity_keyboard())
    else:
        bot.send_message(message.chat.id, 'Выберите дату для первого напоминания или введите дату вручную (в формате YYYY-MM-DD):', reply_markup=create_date_keyboard())

def create_periodicity_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('1', '5', '10', '15', '30', '60')
    return markup

def create_date_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=7)
    today = datetime.date.today()
    days = [(today + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    for day in days:
        markup.add(day)
    markup.add('Назад')
    return markup

@bot.message_handler(func=lambda message: message.text.isdigit() and 1 <= int(message.text) <= 60)
def set_reminder_interval(message):
    interval = int(message.text)
    user_data[message.chat.id]['interval'] = interval
    bot.send_message(message.chat.id, 'Сколько раз вы хотите повторить напоминание? (введите число)')
    bot.register_next_step_handler(message, set_reminder_repeat)

def set_reminder_repeat(message):
    try:
        repeat_count = int(message.text)
        user_data[message.chat.id]['repeat_count'] = repeat_count
        bot.send_message(message.chat.id, 'Выберите дату для первого напоминания или введите дату вручную (в формате YYYY-MM-DD):', reply_markup=create_date_keyboard())
    except ValueError:
        bot.send_message(message.chat.id, 'Пожалуйста, введите корректное число повторений.')

@bot.message_handler(func=lambda message: True)
def handle_date_selection(message):
    if message.text == 'Назад':
        bot.send_message(message.chat.id, 'Нужно ли вам периодическое напоминание? (да/нет)')
    else:
        # Проверяем, является ли введенная дата корректной
        try:
            if message.text.count('-') == 2 and all(part.isdigit() for part in message.text.split('-')):
                user_data[message.chat.id]['reminder_date'] = message.text
                bot.send_message(message.chat.id, 'Вы выбрали дату: {}'.format(message.text))
                bot.send_message(message.chat.id, 'Введите время для первого напоминания в формате HH:MM (секунды будут автоматически установлены в 00):')
                bot.register_next_step_handler(message, handle_time_input)
            else:
                bot.send_message(message.chat.id, 'Неверный формат даты. Пожалуйста, введите дату в формате YYYY-MM-DD.')
        except ValueError:
            bot.send_message(message.chat.id, 'Неверный формат даты. Пожалуйста, введите дату в формате YYYY-MM-DD.')

@bot.message_handler(func=lambda message: True)
def handle_time_input(message):
    try:
        reminder_time_str = message.text
        reminder_date = user_data[message.chat.id]['reminder_date']
        # Устанавливаем секунды в 00
        reminder_time = datetime.datetime.strptime(f"{reminder_date} {reminder_time_str}:00", '%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        delta = reminder_time - now

        if delta.total_seconds() <= 0:
            bot.send_message(message.chat.id, 'Вы выбрали прошедшее время, попробуйте еще раз.')
        else:
            reminder_name = user_data[message.chat.id]['reminder_name']
            interval = user_data[message.chat.id].get('interval', None)
            repeat_count = user_data[message.chat.id].get('repeat_count', 1)

            bot.send_message(message.chat.id, 'Напоминание "{}" установлено на {}.'.format(reminder_name, reminder_time))
            if interval:
                reminder_timer = threading.Timer(delta.total_seconds(), send_reminder, [message.chat.id, reminder_name, interval, repeat_count])
                reminder_timer.start()
    except ValueError:
        bot.send_message(message.chat.id, 'Неверный формат времени. Пожалуйста, введите время в формате HH:MM (секунды будут автоматически установлены в 00).')

def send_reminder(chat_id, reminder_name, interval, repeat_count):
    bot.send_message(chat_id, 'Время получить ваше напоминание "{}"!'.format(reminder_name))
    if repeat_count > 1:
        reminder_timer = threading.Timer(interval * 60, send_reminder, [chat_id, reminder_name, interval, repeat_count - 1])
        reminder_timer.start()

@bot.message_handler(func=lambda message: True)
def handle_all_message(message):
    bot.send_message(message.chat.id, 'Я не понимаю, что вы говорите. Чтобы создать напоминание, введите /reminder.')

if __name__ == '__main__':
    bot.polling(none_stop=True)