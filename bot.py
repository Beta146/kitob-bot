import os
import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KITOBLAR = """
1. O'tkan kunlar — Abdulla Qodiriy — 35,000 so'm
2. Mehrobdan chayon — Abdulla Qodiriy — 32,000 so'm
3. Sariq devni minib — To'xtaboyev — 28,000 so'm
4. Shum bola — G'afur G'ulom — 25,000 so'm
5. Navoiy — Oybek — 40,000 so'm
6. Kichkina shahzoda — 22,000 so'm
7. Alxemik — Paulo Coelho — 30,000 so'm
"""

SYSTEM_PROMPT = f"""Sen Kitob Dokonining Telegram botisan. Faqat uzbek tilida javob ber.
Dokonimizdagi kitoblar: {KITOBLAR}
Qoidalar:
- Qisqa va dostona javob ber (3-4 jumla)
- Kitob sorase narx va qisqacha malumot ber
- Buyurtma uchun ism va manzil sora
- Ish vaqti: Dushanba-Shanba 09:00-18:00
- Manzil: Samarqand
- Telefon: +998 90 123-45-67"""

user_histories = {}

def get_ai_response(user_id, message):
    if user_id not in user_histories:
        user_histories[user_id] = []
    
    user_histories[user_id].append({"role": "user", "parts": [{"text": message}]})
    
    if len(user_histories[user_id]) > 20:
        user_histories[user_id] = user_histories[user_id][-20:]
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": user_histories[user_id]
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    reply = data["candidates"][0]["content"]["parts"][0]["text"]
    user_histories[user_id].append({"role": "model", "parts": [{"text": reply}]})
    return reply

def main_keyboard():
    keyboard = [
        [KeyboardButton("📚 Kitoblar ro'yxati"), KeyboardButton("🔍 Kitob qidirish")],
        [KeyboardButton("🛒 Buyurtma berish"), KeyboardButton("📞 Aloqa")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}! 👋\n\n📚 Kitob Do'koniga xush kelibsiz!",
        reply_markup=main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        reply = get_ai_response(user_id, text)
        await update.message.reply_text(reply, reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text("Kechirasiz, xatolik. Qayta urinib koring.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if _name_ == "_main_":
    main()
