import telebot
import asyncio
import threading
import os
from dotenv import load_dotenv

from scanner import start_browser, scan_range


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

user_state = {}

# ⭐ CREATE ONE GLOBAL EVENT LOOP
loop = asyncio.new_event_loop()


def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=start_loop, args=(loop,), daemon=True).start()


# ⭐ START BROWSER INSIDE THAT LOOP
browser_future = asyncio.run_coroutine_threadsafe(
    start_browser(), loop
)

browser = browser_future.result()   # waits safely

print("✅ Browser Started")


# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):

    chat_id = message.chat.id
    user_state[chat_id] = {"step": "first"}

    bot.send_message(chat_id, "🔥 Welcome!\n\nSend First ELD:")


# ================= FLOW =================

@bot.message_handler(func=lambda m: True)
def handle(message):

    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id not in user_state:
        return

    step = user_state[chat_id]["step"]

    # FIRST
    if step == "first":

        if not text.isdigit():
            bot.send_message(chat_id, "❌ Numbers only.")
            return

        user_state[chat_id]["first"] = text
        user_state[chat_id]["step"] = "last"

        bot.send_message(chat_id, "Send Last ELD:")
        return


    # LAST
    if step == "last":

        if not text.isdigit():
            bot.send_message(chat_id, "❌ Numbers only.")
            return

        user_state[chat_id]["last"] = text
        user_state[chat_id]["step"] = "district"

        bot.send_message(chat_id, "Send District:")
        return


    # DISTRICT
    if step == "district":

        district = text.upper()

        first = user_state[chat_id]["first"]
        last = user_state[chat_id]["last"]

        bot.send_message(
            chat_id,
            f"🔍 Scanning permits for {district}...\n⚡ Please wait..."
        )

        # ⭐ RUN IN SAME LOOP (NO THREAD CRASH)
        asyncio.run_coroutine_threadsafe(
            scan_range(bot, browser, chat_id, first, last, district),
            loop
        )

        del user_state[chat_id]


print("✅ BOT RUNNING...")
bot.infinity_polling(skip_pending=True)
