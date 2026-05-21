
import logging
import requests
from dotenv import load_dotenv
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
 
# === .env dan o'qish ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID"))
 
# === PORTFOLIO ===
PORTFOLIO_INFO = """
Ism: Lobar
Kasb: Python o'rganuvchi dasturchi
Ko'nikmalar: Python, Aiogram, HTML/CSS, Git
Qiziqishlar: Telegram botlar yaratish, dasturlash
Maqsad: Kelajakda murakkab loyihalar yaratib, jamoada ishlash
"""
 
SYSTEM_PROMPT = f"""Sen Lobar ismli Python dasturchi qizning portfolio botisan.
Lobar haqida: {PORTFOLIO_INFO}
Qoidalar:
- Har doim O'zbek tilida javob ber
- Samimiy va do'stona bo'l
- Lobar haqida so'rashsa yuqoridagi ma'lumotdan foydalanib javob ber
- Dasturlash, Python, botlar haqida savollar bo'lsa tushuntirib ber
- Javoblarni qisqa yoz (2-4 gap)
"""
 
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
 
# === AI JAVOB ===
def ask_ai(user_text: str, history: list) -> str:
    conversation = SYSTEM_PROMPT + "\n\n"
    for msg in history[-6:]:
        if msg["role"] == "user":
            conversation += f"Foydalanuvchi: {msg['content']}\n"
        else:
            conversation += f"Bot: {msg['content']}\n"
    conversation += f"Foydalanuvchi: {user_text}\nBot:"
 
    response = requests.post(
        "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3",
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        json={
            "inputs": conversation,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 0.7,
                "return_full_text": False
            }
        },
        timeout=30
    )
    result = response.json()
    if isinstance(result, list):
        text = result[0].get("generated_text", "").strip()
        if "\nFoydalanuvchi:" in text:
            text = text.split("\nFoydalanuvchi:")[0].strip()
        return text if text else "Tushunmadim, qayta yozing 😊"
    return "Hozir javob bera olmayapman, keyinroq urinib ko'ring."
 
# === HANDLERLAR ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📋 Portfolio ko'rish")],
        [KeyboardButton("✉️ Lobar'ga xabar yuborish")],
        [KeyboardButton("📞 Aloqa ma'lumotlari")],
    ]
    await update.message.reply_text(
        "👋 Salom! Men Lobar'ning portfolio botiman.\nIstalgan savol bering — javob beraman! 🤖",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
 
async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👩‍💻 *Lobar haqida*\n\n"
        "📌 Ism: Lobar\n"
        "🎯 Soha: Python dasturchi (o'rganuvchi)\n"
        "🛠 Ko'nikmalar: Python, Aiogram, HTML/CSS, Git\n"
        "❤️ Sevimli mashg'ulot: Telegram botlar yaratish\n"
        "🌐 Website: lobar.dev",
        parse_mode="Markdown"
    )
 
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Aloqa ma'lumotlari*\n\n"
        "✈️ Telegram: @lobar\\_username\n"
        "📧 Email: lobar@email.com\n"
        "💻 GitHub: github.com/lobar\n"
        "🌐 Website: lobar.dev",
        parse_mode="Markdown"
    )
 
async def ai_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
 
    if user_text == "📋 Portfolio ko'rish":
        await portfolio(update, context)
        return
    elif user_text == "✉️ Lobar'ga xabar yuborish":
        await update.message.reply_text("✏️ Xabaringizni yozing, Lobar'ga yetkazaman!")
        context.user_data["waiting_message"] = True
        return
    elif user_text == "📞 Aloqa ma'lumotlari":
        await contact(update, context)
        return
 
    if context.user_data.get("waiting_message"):
        context.user_data["waiting_message"] = False
        user = update.message.from_user
        try:
            await context.bot.send_message(
                chat_id=YOUR_TELEGRAM_ID,
                text=f"📨 Yangi xabar!\n👤 {user.first_name} (@{user.username or 'yoq'})\n💬 {user_text}"
            )
            await update.message.reply_text("✅ Xabaringiz Lobar'ga yetkazildi!")
        except Exception:
            await update.message.reply_text("❌ Xatolik yuz berdi.")
        return
 
    try:
        await update.message.chat.send_action("typing")
        history = context.user_data.get("history", [])
        reply = ask_ai(user_text, history)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply})
        context.user_data["history"] = history[-10:]
        await update.message.reply_text(reply)
    except Exception as e:
        logging.error(f"Xato: {e}")
        await update.message.reply_text("🤔 Hozir javob bera olmayapman, qayta urinib ko'ring.")
 
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_reply))
    print("✅ Bot ishga tushdi!")
    app.run_polling()
 
if __name__ == "__main__":
    main()