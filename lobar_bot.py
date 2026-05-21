
import logging
import requests
import time
from dotenv import load_dotenv
import os
 
# === .env dan o'qish ===
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID"))
 
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
 
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
 
# === Foydalanuvchi holati ===
user_data = {}
 
# === TELEGRAM API funksiyalari ===
def send_message(chat_id, text, reply_markup=None, parse_mode=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    requests.post(f"{BASE_URL}/sendMessage", json=payload)
 
def send_chat_action(chat_id, action="typing"):
    requests.post(f"{BASE_URL}/sendChatAction", json={"chat_id": chat_id, "action": action})
 
def get_updates(offset=None):
    params = {"timeout": 30, "offset": offset}
    try:
        response = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        return response.json()
    except Exception as e:
        logging.error(f"getUpdates xato: {e}")
        return {"result": []}
 
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
 
# === KEYBOARD ===
def main_keyboard():
    return {
        "keyboard": [
            [{"text": "📋 Portfolio ko'rish"}],
            [{"text": "✉️ Lobar'ga xabar yuborish"}],
            [{"text": "📞 Aloqa ma'lumotlari"}],
        ],
        "resize_keyboard": True
    }
 
# === XABARNI QAYTA ISHLASH ===
def handle_message(chat_id, user_text, user):
    if chat_id not in user_data:
        user_data[chat_id] = {"history": [], "waiting_message": False}
 
    data = user_data[chat_id]
 
    if user_text == "/start":
        send_message(
            chat_id,
            "👋 Salom! Men Lobar'ning portfolio botiman.\nIstalgan savol bering — javob beraman! 🤖",
            reply_markup=main_keyboard()
        )
        return
 
    if user_text == "📋 Portfolio ko'rish":
        send_message(
            chat_id,
            "👩‍💻 *Lobar haqida*\n\n"
            "📌 Ism: Lobar\n"
            "🎯 Soha: Python dasturchi (o'rganuvchi)\n"
            "🛠 Ko'nikmalar: Python, Aiogram, HTML/CSS, Git\n"
            "❤️ Sevimli mashg'ulot: Telegram botlar yaratish\n"
            "🌐 Website: lobar.dev",
            parse_mode="Markdown"
        )
        return
 
    if user_text == "📞 Aloqa ma'lumotlari":
        send_message(
            chat_id,
            "📞 *Aloqa ma'lumotlari*\n\n"
            "✈️ Telegram: @lobar\\_username\n"
            "📧 Email: lobar@email.com\n"
            "💻 GitHub: github.com/lobar\n"
            "🌐 Website: lobar.dev",
            parse_mode="Markdown"
        )
        return
 
    if user_text == "✉️ Lobar'ga xabar yuborish":
        data["waiting_message"] = True
        send_message(chat_id, "✏️ Xabaringizni yozing, Lobar'ga yetkazaman!")
        return
 
    if data.get("waiting_message"):
        data["waiting_message"] = False
        first_name = user.get("first_name", "")
        username = user.get("username", "yoq")
        try:
            send_message(
                YOUR_TELEGRAM_ID,
                f"📨 Yangi xabar!\n👤 {first_name} (@{username})\n💬 {user_text}"
            )
            send_message(chat_id, "✅ Xabaringiz Lobar'ga yetkazildi!")
        except Exception:
            send_message(chat_id, "❌ Xatolik yuz berdi.")
        return
 
    # AI javob
    send_chat_action(chat_id)
    history = data.get("history", [])
    reply = ask_ai(user_text, history)
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": reply})
    data["history"] = history[-10:]
    send_message(chat_id, reply)
 
# === ASOSIY LOOP ===
def main():
    print("✅ Bot ishga tushdi!")
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates.get("result", []):
            offset = update["update_id"] + 1
            message = update.get("message", {})
            if not message:
                continue
            chat_id = message["chat"]["id"]
            user_text = message.get("text", "")
            user = message.get("from", {})
            if user_text:
                try:
                    handle_message(chat_id, user_text, user)
                except Exception as e:
                    logging.error(f"Xato: {e}")
                    send_message(chat_id, "🤔 Hozir javob bera olmayapman, qayta urinib ko'ring.")
        time.sleep(0.5)
 
if __name__ == "__main__":
    main()