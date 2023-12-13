#импорты
import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from config import TELEGRAM_TOKEN, JSON_KEY_PATH, SPREADSHEET_ID,ADMIN_CHAT_ID

bot = telebot.TeleBot(TELEGRAM_TOKEN)
json_key_path = JSON_KEY_PATH


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(json_key_path, scope)
client = gspread.authorize(creds)

spreadsheet_id = SPREADSHEET_ID

user_input = {}

"""Функции и команды"""


def create_keyboard():
    markup = types.InlineKeyboardMarkup()
    pre_shisha = types.InlineKeyboardButton(text='Премиум кальян', callback_data='premium')
    markup.add(pre_shisha)
    nac_shisha = types.InlineKeyboardButton(text='Национальный кальян', callback_data='national')
    markup.add(nac_shisha)
    return markup

def send_to_google_sheets(data, user_id):
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        clean_data = sanitize_for_sheet(data)
        order_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([order_datetime, clean_data[0], clean_data[1], user_id])
    except Exception as e:
        error_message = f'Произошла ошибка при записи в Google Sheets: {str(e)}'
        log_error(error_message, data)
        raise


def sanitize_for_sheet(data):
    
    words = data.split()

    
    return words[0], words[3]

def log_error(error_message, data):
    with open('error_log.txt', 'a') as log_file:
        log_file.write(f'{error_message}\nData: {data}\n\n')
        bot.send_message(ADMIN_CHAT_ID, f'Произошла ошибка при записи в Google Sheets. Дополнительные детали сохранены в error_log.txt\nError: {str(error_message)}\nData: {str(data)}')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Заказ")
    btn2 = types.KeyboardButton("Ссылка на таблицу")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, text='Функционал', reply_markup=markup)

@bot.message_handler(commands=['order'])
def order(message):
    try:
        markup = create_keyboard()
        bot.send_message(message.chat.id, 'Какой кальян заказали:', reply_markup=markup)
    except Exception as e:
        bot.send_message(ADMIN_CHAT_ID, f'Произошла ошибка: {str(e)}')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        if call.data == 'premium':
            bot.answer_callback_query(call.id, 'Выбран: Премиум кальян')
            bot.send_message(call.message.chat.id, 'Сколько грамм:')
            user_input[call.message.chat.id] = {'type': 'premium'}
        elif call.data == 'national':
            bot.answer_callback_query(call.id, 'Выбран: Национальный кальян')
            bot.send_message(call.message.chat.id, 'Сколько грамм:')
            user_input[call.message.chat.id] = {'type': 'national'}
    except Exception as e:
        bot.send_message(ADMIN_CHAT_ID, f'Произошла ошибка: {str(e)}')

@bot.message_handler(func=lambda message: message.text == "Заказ")
def handle_order_button(message):
    order(message)

@bot.message_handler(func=lambda message: message.text == "Ссылка на таблицу")
def handle_spreadsheet_link(message):
    markup = types.InlineKeyboardMarkup()
    spreadsheet_link = "https://docs.google.com/spreadsheets/d/1YkQu3Os5G6KIOzlj586_KKh6sfT4OGE2z-G4uGFhrac/edit?usp=sharing"
    spreadsheet_button = types.InlineKeyboardButton(text="Открыть таблицу", url=spreadsheet_link)
    markup.add(spreadsheet_button)
    bot.send_message(message.chat.id, "Нажми на кнопку, чтобы открыть таблицу:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_user_input(message):
    try:
        chat_id = message.chat.id

        if chat_id in user_input:
            grams = message.text
            shisha_type = user_input[chat_id]['type']
            user_id = message.from_user.id
            bot.send_message(chat_id, f'Ты заказал {grams} грамм {shisha_type} кальяна.')
            send_to_google_sheets(f'{shisha_type.capitalize()} кальян - {grams} грамм', user_id)
            user_input.pop(chat_id)
    except Exception as e:
        bot.send_message(ADMIN_CHAT_ID, f'Произошла ошибка: {str(e)}')


#беспрерывная работа бота
bot.infinity_polling(none_stop=True)
