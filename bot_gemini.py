import os
import logging
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === SOZLAMALAR ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "TOKENINGIZNI_SHU_YERGA_QOYING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "GEMINI_KEYNI_SHU_YERGA_QOYING")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === GEMINI SOZLASH ===
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# === KITOBLAR ===
KITOBLAR = """
1. O'tkan kunlar — Abdulla Qodiriy — 35,000 so'm
2. Mehrobdan chayon — Abdulla Qodiriy — 32,000 so'm
3. Sariq devni minib — Xudoiberdi To'xtaboyev — 28,000 so'm
4. Shum bola — G'afur G'ulom — 25,000 so'm
5. Navoiy — Oybek — 40,000 so'm
6. Kichkina shahzoda — Antoine de Saint-Exupéry — 22,000 so'm
7. Alxemik — Paulo Coelho — 30,000 so'm
"""

SYSTEM_PROMPT = f"""Sen "Kitob Do'koni" Telegram botisisan. Faqat o'zbek tilida javob ber.

Do'konimizdagi kitoblar:
{KITOBLAR}

Qoidalar:
- Qisqa va do'stona javob ber (3-5 jumla)
- Kitob so'rasa narx va qisqacha ma'lumot ber
- Buyurtma uchun: ismini va manzilini so'ra
- Ish vaqti: Dushanba-Shanba 09:00-18:00
- Manzil: Toshkent, Chilonzor 5-kvartal, 12-uy
- Telefon: +998 90 123-45-67
- Har doim iliq va samimiy bo'l"""

# Foydalanuvchi suhbat tarixi
user_chats = {}

# === KLAVIATURA ===
def main_keyboard():
    keyboard = [
        [KeyboardButton("📚 Kitoblar ro'yxati"), KeyboardButton("🔍 Kitob qidirish")],
        [KeyboardButton("🛒 Buyurtma berish"), KeyboardButton("📞 Aloqa")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# === AI JAVOB ===
async def get_ai_response(user_id: int, message: str) -> str:
    if user_id not in user_chats:
        user_chats[user_id] = model.start_chat(history=[])

    chat = user_chats[user_id]
    full_message = f"{SYSTEM_PROMPT}\n\nFoydalanuvchi: {message}" if len(chat.history) == 0 else message

    response = chat.send_message(full_message)
    return response.text

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Assalomu alaykum, {user.first_name}! 👋\n\n"
        "📚 Kitob Do'koniga xush kelibsiz!\n"
        "Quyidagi tugmalardan birini tanlang yoki savolingizni yozing:",
        reply_markup=main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        reply = await get_ai_response(user_id, text)
        await update.message.reply_text(reply, reply_markup=main_keyboard())
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await update.message.reply_text(
            "Kechirasiz, texnik xatolik. Iltimos, qayta urinib ko'ring.",
            reply_markup=main_keyboard()
        )

# === MAIN ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushdi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
