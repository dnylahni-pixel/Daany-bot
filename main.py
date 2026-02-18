import os
import logging
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

# ======== توکن‌ها ========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# ======== لاگ ========
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# ======== کلاینت Claude ========
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ======== فایل داده‌ها ========
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

user_data = load_data()

# ======== مدیریت کاربران ========
def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"history": []}
    return user_data[user_id]

# ======== پرسش از Claude ========
def ask_claude(user_id, message):
    user = get_user(user_id)
    user["history"].append({"role": "user", "content": message})
    if len(user["history"]) > 20:
        user["history"] = user["history"][-20:]
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=f"تو یک دستیار هوشمند فارسی‌زبان هستی. همیشه به فارسی پاسخ بده. تاریخ امروز: {datetime.now().strftime('%Y/%m/%d')}",
            messages=user["history"]
        )
        reply = response.content[0].text
        user["history"].append({"role": "assistant", "content": reply})
        save_data()
        return reply
    except Exception as e:
        return "خطا در ارتباط با هوش مصنوعی. دوباره امتحان کنید."

# ======== پیام‌های کاربر ========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ask_claude(update.effective_user.id, update.message.text)
    await update.message.reply_text(reply)

# ======== اجرای ربات ========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات شروع شد!")
    app.run_polling()

if __name__ == "__main__":
    main()