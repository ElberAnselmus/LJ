import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import configparser
import random
import sqlite3
from queue import Queue
import threading
import datetime

# Load config
config = configparser.ConfigParser()
config.read("conf.config")
BOT_TOKEN = config["BOT"]["TOKEN"]  # Telegram bot token

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Connect to SQLite database
db_connection = sqlite3.connect("luckyinjector.db", check_same_thread=False)
db_cursor = db_connection.cursor()

# Drop and recreate the user table with the updated structure
# db_cursor.execute('DROP TABLE IF EXISTS user')

db_cursor.execute('''
CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    code INTEGER UNIQUE,
    latest_inject TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
db_connection.commit()

# Read game list from file
with open("game.txt", "r") as file:
    games = [line.strip() for line in file.readlines()]

# Store active options for each user
user_active_options = {}

# Request queue
request_queue = Queue()

# Check if user exists in database
def is_user_exist(user_id):
    db_cursor.execute('SELECT user_id FROM user WHERE user_id = ?', (user_id,))
    return db_cursor.fetchone() is not None

# Get the next available code from the database
def get_next_code():
    db_cursor.execute('SELECT MAX(code) FROM user')
    result = db_cursor.fetchone()
    if result and result[0]:
        return result[0] + 1
    else:
        return 1910001  # Start from 100001 if no users exist yet

# Insert user data into database
def insert_user_data(user_id, username, code):
    db_cursor.execute('''
    INSERT INTO user (user_id, username, code)
    VALUES (?, ?, ?)
    ''', (user_id, username, code))
    db_connection.commit()

# Update the latest_inject timestamp
def update_latest_inject(user_id):
    db_cursor.execute('''
    UPDATE user SET latest_inject = CURRENT_TIMESTAMP WHERE user_id = ?
    ''', (user_id,))
    db_connection.commit()

# Command: /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.chat.id
    username = message.chat.username if message.chat.username else None

    # Check if user already exists in the database
    if not is_user_exist(user_id):
        # Generate unique code
        code = get_next_code()
        # Insert user data with the generated code
        insert_user_data(user_id, username, code)
    else:
        # Update latest_inject timestamp for existing user
        update_latest_inject(user_id)

    # Prompt user to input the activation code
    bot.send_message(message.chat.id, "💎 Selamat datang! Sila masukkan Activation Code untuk verify.")
    bot.register_next_step_handler(message, verify_code)

def verify_code(message):
    user_id = message.chat.id
    entered_code = message.text

    # Check if the entered code matches the user's code in the database
    db_cursor.execute('SELECT code FROM user WHERE user_id = ?', (user_id,))
    result = db_cursor.fetchone()

    if result and str(result[0]) == entered_code:
        bot.send_message(message.chat.id, "🗝️ Verification berjaya! Sila masukkan ID game anda.")
        bot.register_next_step_handler(message, get_game_id)
    else:
        bot.send_message(message.chat.id, "❌ Code Tidak Sah. Sila chat admin @xninze101 untuk membeli Activation Code. \n\nSila tekan /help untuk bantuan.")

def get_game_id(message):
    user_id = message.chat.id
    game_id = message.text  # Store user-provided game ID

    # Validate the game ID input
    if any(char.isalpha() for char in game_id) or len(game_id) < 10:
        bot.send_message(message.chat.id, "❌ Invalid ID Game. Tolong masukkan ID Game yang valid.")
        bot.register_next_step_handler(message, get_game_id)  # Prompt for game ID again
    else:
        bot.send_message(message.chat.id, "👾 Bot sedang scan winrate, sila tunggu sebentar...")
        time.sleep(20)  # Simulate injection delay
        request_queue.put((send_winrate, message))

# KHAS UNTUK SET WINRATE SEMUA GAME ========================================================================================
# # Generate and send winrate message
# def send_winrate(message):
#     winrate_message = "📊 *Winrate Scanning Result* 📊\n\n"

#     # Get current date and time
#     current_date = datetime.datetime.now().strftime("%d-%m-%Y | %H:%M")
#     winrate_message += f"📅 Date: {current_date}\n\n"

#     winrate_message +=  "🎮 Here is the winrate for the selected game 🎮\n\n"

#     for game in games:
#         # Generate random winrate between 40% and 93%
#         winrate = f"-🤖 {game} - {random.uniform(40.14, 82.94):.2f}%"
#         winrate_message += f"{winrate}\n"

#     # Send the winrate results
#     bot.send_message(message.chat.id, winrate_message, parse_mode="Markdown")
#     send_option_inline_keyboard(message.chat.id)

# KHAS UNTUK SET WINRATE SATU GAME PALING BESAR =============================================================================
# # Generate and send winrate message
def send_winrate(message):
    winrate_message = "📊 *Winrate Scanning Result* 📊\n\n"

    # Get current date and time
    current_date = datetime.datetime.now().strftime("%d-%m-%Y | %H:%M")
    winrate_message += f"📅 Date: {current_date}\n\n"

    winrate_message +=  "🎮 Here is the winrate for the selected game 🎮\n\n"

    for game in games:
        if game.lower() == "iceland":
            winrate = f"-🤖 {game} - 91.74%"  # Fixed winrate for "great88"
        else:
            winrate = f"-🤖 {game} - {random.uniform(40.14, 78.94):.2f}%"  # Random winrate for other games
        winrate_message += f"{winrate}\n"

    # Send the winrate results
    bot.send_message(message.chat.id, winrate_message, parse_mode="Markdown")
    send_option_inline_keyboard(message.chat.id)


# Send the main menu with inline buttons
def send_option_inline_keyboard(chat_id):
    # Create inline keyboard
    markup = InlineKeyboardMarkup(row_width=2)
    options = [
        ("FreeSpin 🔴", "freespin"),
        ("Pecah 3 🔴", "injector_pecah_3"),
        ("Ultra BigWin 🔴", "ultra_bigwin"),
        ("Winrate 99% 🔴", "winrate_99%"),
    ]
    for i in range(0, len(options), 2):
        row = options[i:i + 2]
        buttons = [InlineKeyboardButton(label, callback_data=callback_data) for label, callback_data in row]
        markup.row(*buttons)

    # Add a start inject button centered below
    markup.add(InlineKeyboardButton("💉 Start Inject 💉", callback_data="start_inject"))

    # Send message with inline keyboard
    bot.send_message(chat_id, "⚙️ Pilih setting untuk inject:", reply_markup=markup)

# Handle callback queries from inline buttons
@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    user_id = call.message.chat.id
    selected_option = call.data

    if selected_option == "start_inject":
        # Send loading GIF before starting injection
        with open("loading.gif", "rb") as gif:
            bot.send_animation(user_id, gif)
        
        # Start the injection process
        bot.send_message(user_id, "💉 Start Injecting...")
        threading.Thread(target=request_queue.put, args=((simulate_injection, user_id),)).start()
    else:
        # Toggle option status
        if selected_option in user_active_options.get(user_id, set()):
            user_active_options[user_id].remove(selected_option)
        else:
            user_active_options.setdefault(user_id, set()).add(selected_option)

        # Immediately update the inline keyboard without additional notifications
        bot.edit_message_reply_markup(
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=get_updated_inline_keyboard(user_id)
        )

# Function to dynamically update inline keyboard with status
def get_updated_inline_keyboard(chat_id):
    markup = InlineKeyboardMarkup(row_width=2)
    options = [
        ("FreeSpin", "freespin"),
        ("Pecah 3", "injector_pecah_3"),
        ("Ultra BigWin", "ultra_bigwin"),
        ("Winrate 99%", "winrate_99%"),
    ]
    for i in range(0, len(options), 2):
        row = options[i:i + 2]
        buttons = [InlineKeyboardButton(f"{label} {'🟢' if callback_data in user_active_options.get(chat_id, set()) else '🔴'}", callback_data=callback_data) for label, callback_data in row]
        markup.row(*buttons)

    # Add a start inject button centered below
    markup.add(InlineKeyboardButton("💉 Start Inject 💉", callback_data="start_inject"))
    return markup

# Simulate injection process
def simulate_injection(user_id):
    # Delay 1: 10-20%
    message = bot.send_message(user_id, f"⌛ - {random.randint(10, 20)}% Processing Injection...")
    time.sleep(5)  # Simulate injection delay 1

    # Update message for Delay 2: 33-60%
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message.message_id,
        text=f"⌛ - {random.randint(33, 60)}% Processing Injection..."
    )
    time.sleep(5)  # Simulate injection delay 2

    # Update message for Delay 3: 72-92%
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message.message_id,
        text=f"⌛ - {random.randint(72, 92)}% Processing Injection..."
    )
    time.sleep(10)  # Simulate injection delay 3

    # Final message: Injection completed
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message.message_id,
        text="🧧 Injection completed! Semoga kemenangan milik anda. 🧧\n\n - Tekan /start untuk ulang injection. \n - Tekan /help untuk info lebih lanjut."
    )

# Worker thread for processing requests
def worker():
    while True:
        func, arg = request_queue.get()
        func(arg)
        request_queue.task_done()

# Start worker threads
for _ in range(5):  # Adjust number of workers as needed
    threading.Thread(target=worker, daemon=True).start()

# Command: /help
@bot.message_handler(commands=['help'])
def help_handler(message):
    help_message = (
        "⚠️ *Warning* ⚠️\n"
        "- Kemenangan tidak bergantung 100% pada bot, Cara bermain juga penting!\n"
        "- Tidak diwajibkan untuk INJECT berulang kali pada masa yang singkat!\n\n"
        "📋 *Cara pemakaian* 📋\n"
        "- Pastikan guna Bot dengan Game dekat satu device sahaja.\n"
        "- Masukkan ID Game anda.\n"
        "- Tunggu untuk bot scan winrate setiap game.\n"
        "- Ubah settings yang anda inginkan.\n"
        "- Tekan 'Start Inject' untuk memulakan inject boost akaun.\n"
        "- Buka game tanpa menutup tele/bot anda.\n\n"
        "🚀 Semoga kemenangan buat anda.\n\n"
        "📲 Sebarang pertanyaan sila chat min: @xninze101"
    )
    bot.send_message(message.chat.id, help_message, parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()

