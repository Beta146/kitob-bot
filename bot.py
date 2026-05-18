import os
import logging
import requests
from threading import Thread
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Flask server
flask_app = Flask(name)

@flask_app.route('/')
def home():
    return "Bot is alive"

def run_flask():
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

Thread(target=run_flask, daemon=True).start()

# Bot sozlamalari
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)

KITOBLAR = "1.Otkan kunlar-35000 2.Navoiy-40000 3.Shum bola-25000 4.Alxemik-30000"
SYSTEM_PROMPT = f"Sen Kitob Dokonining Telegram botisan. Faqat uzbek tilida javob ber. Kitoblar: {KITOBLAR}. Qisqa javob ber. Tel: +998 90 123-45-67"

user_histories = {}

def get_ai_response(user_id, message):
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "parts": [{"text": message}]})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]}, "contents": user_histories[user_id]}
    response = requests.post(url, json=payload)
    data = response.json()
    reply = data["candidates"][0]["content"]["parts"][0]["text"]
    user_histories[user_id].append({"role": "model", "parts": [{"text": reply}]})
    return reply

def main_keyboard():
    keyboard = [
        [KeyboardButton("📚 Kitoblar"), KeyboardButton("🔍 Qidirish")],
        [KeyboardButton("🛒 Buyurtma"), KeyboardButton("📞 Aloqa")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}! 👋\n📚 Kitob Do'koniga xush kelibsiz!",
        reply_markup=main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        reply = get_ai_response(update.effective_user.id, update.message.text)
        await update.message.reply_text(reply, reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text("Xatolik. Qayta urining.")

def main():
    Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot ishga tushdi!")
    app.run_polling(drop_pending_updates=True)

if name == "main":
    main()
