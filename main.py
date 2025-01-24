import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import time
import configparser
import random
import json  # Import JSON untuk simpan special code dan user ID

# Load config
config = configparser.ConfigParser()
config.read("conf.config")
BOT_TOKEN = config["BOT"]["TOKEN"]  # Telegram bot token

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Read game list from file
with open("game.txt", "r") as file:
    games = [line.strip() for line in file.readlines()]

# Store active options for each user
user_active_options = {}

# Check if special code is valid and bind it to user ID
def is_code_valid(entered_code, user_id):
    try:
        with open("userkey.json", "r") as file:
            codes = json.load(file)
        # Check if the code exists and matches the user ID
        if entered_code in codes and codes[entered_code] == str(user_id):
            return True
        return False
    except FileNotFoundError:
        return False

# Assign code to user in the file
def assign_code_to_user(entered_code, user_id):
    try:
        with open("userkey.json", "r") as file:
            codes = json.load(file)
    except FileNotFoundError:
        codes = {}

    # Check if the code already exists
    if entered_code not in codes:
        codes[entered_code] = str(user_id)
        # Save the updated data back to file
        with open("userkey.json", "w") as file:
            json.dump(codes, file, indent=4)

# Command: /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    # Prompt user to input the special code
    bot.send_message(message.chat.id, "💎 Selamat datang! Sila masukkan Special Code untuk verify.")
    bot.register_next_step_handler(message, verify_code)

def verify_code(message):
    user_id = message.chat.id
    entered_code = message.text

    # Check if the entered code is valid and bound to the user ID
    if is_code_valid(entered_code, user_id):
        bot.send_message(message.chat.id, "🗝️ Verification berjaya! Sila tunggu, 👾 Bot sedang scan winrate...")
        time.sleep(2)  # Simulate scanning delay
        send_winrate(message)
    else:
        bot.send_message(message.chat.id, "❌ Code Tidak Sah. Sila chat admin @xninze101 untuk membeli Activation Code. \n\nSila tekan /help untuk bantuan.")

# Generate and send winrate message
def send_winrate(message):
    winrate_message = "📊 *Winrate Scanning Result* 📊\n\n"
    for game in games:
        # Generate random winrate between 75% and 93%
        winrate = f"-🤖 {game} - {random.randint(40, 93)}%"
        winrate_message += f"{winrate}\n"

    # Send the winrate results
    bot.send_message(message.chat.id, winrate_message, parse_mode="Markdown")
    bot.send_message(message.chat.id, "Sila masukkan ID game anda:")
    bot.register_next_step_handler(message, get_game_id)

def get_game_id(message):
    user_id = message.chat.id  # Store user-provided game ID
    # Create reply keyboard for options
    send_option_keyboard(message.chat.id)

def send_option_keyboard(chat_id):
    # Create keyboard with status indicators
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    options = [
        "INJECTOR PECAH 3",
        "SEAWORLD BIGWIN INJECTOR",
        "DETECTOR FREESPIN",
        "WINRATE 99%",
        "MEGA ULTRA BIGWIN INJECTOR"
    ]
    for option in options:
        status = " 🟢" if option in user_active_options.get(chat_id, set()) else " 🔴"
        markup.add(KeyboardButton(f"{option} {status}"))
    markup.add(KeyboardButton("💉Start Inject💉"))

    # Send the keyboard to the user
    bot.send_message(chat_id, "Pilih setting untuk inject:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, inject_handler)

def inject_handler(message):
    user_id = message.chat.id
    selected_option = message.text.rstrip(" 🟢🔴")  # Extract the option without the status symbol

    if selected_option == "💉Start Inject💉":
        # Send loading GIF before starting injection
        with open("loading.gif", "rb") as gif:
            bot.send_animation(user_id, gif)
        
        # Start the injection process
        bot.send_message(user_id, "💉 Start Injecting...")
        time.sleep(3)  # Simulate injection delay
        bot.send_message(user_id, "Successfully completed the injection... Wish you all the best dan semoga kemenangan milik anda. ✨")
    else:
        # Toggle the activation status of the selected option
        if selected_option in user_active_options.get(user_id, set()):
            user_active_options[user_id].remove(selected_option)
            bot.send_message(user_id, f"{selected_option} dinyahaktifkan.")
        else:
            user_active_options.setdefault(user_id, set()).add(selected_option)
            bot.send_message(user_id, f"{selected_option} diaktifkan.")

        # Resend updated keyboard with status indicators
        send_option_keyboard(user_id)

# Command: /help
@bot.message_handler(commands=['help'])
def help_handler(message):
    help_message = (
        "⚠️ *Warning* ⚠️\n"
        "- Kemenangan tidak bergantung 100% pada bot, Cara bermain juga penting!\n"
        "- Tidak diwajibkan untuk INJECT berulang kali pada masa yang singkat!\n\n"
        "📋 *Cara pemakaian* 📋\n"
        "- Pastikan guna Bot dengan Game dekat satu device sahaja.\n"
        "- Tunggu untuk bot scan winrate setiap game.\n"
        "- Masukkan ID Game anda.\n"
        "- Ubah settings yang anda inginkan.\n"
        "- Tekan 'Start Inject' untuk memulakan inject boost akaun.\n"
        "- Buka game tanpa menutup tele/bot anda.\n\n"
        "🚀 Semoga kemenangan buat anda."
    )
    bot.send_message(message.chat.id, help_message, parse_mode="Markdown")


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()
