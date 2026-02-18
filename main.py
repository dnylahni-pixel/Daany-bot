import os
import logging
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# ======== توکن‌ها ========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")

# ======== لاگ ========
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

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
        user_data[user_id] = {"history": [], "tasks": []}
    return user_data[user_id]

# ======== دستورات ربات ========
async def start(update, context):
    keyboard = [
        [
            InlineKeyboardButton("📋 تسک‌ها", callback_data="show_tasks"),
            InlineKeyboardButton("🗑 پاک کردن", callback_data="clear_history")
        ]
    ]
    await update.message.reply_text(
        "سلام! من دستیار هوشمند شما هستم.\n\n"
        "/task [متن] - تسک جدید\n"
        "/tasks - لیست تسک‌ها\n"
        "/done [شماره] - انجام شد\n"
        "/clear - پاک کردن تاریخچه",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def add_task(update, context):
    user = get_user(update.effective_user.id)
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("مثال:\n/task خرید نان")
        return

    task = {
        "id": len(user["tasks"]) + 1,
        "text": text,
        "done": False
    }
    user["tasks"].append(task)
    save_data()
    await update.message.reply_text(f"✅ تسک اضافه شد: {text}")

async def show_tasks(update, context):
    user = get_user(update.effective_user.id)
    if not user["tasks"]:
        await update.message.reply_text("هیچ تسکی ندارید.")
        return
    msg = "📋 تسک‌ها:\n\n"
    for t in user["tasks"]:
        msg += f"{'✅' if t['done'] else '⬜'} {t['id']}. {t['text']}\n"
    await update.message.reply_text(msg)

async def done_task(update, context):
    user = get_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("مثال: /done 1")
        return
    task_id = int(context.args[0])
    for t in user["tasks"]:
        if t["id"] == task_id:
            t["done"] = True
            save_data()
            await update.message.reply_text(f"✅ انجام شد: {t['text']}")
            return

async def clear_history(update, context):
    get_user(update.effective_user.id)["history"] = []
    save_data()
    await update.message.reply_text("تاریخچه پاک شد!")

async def handle_message(update, context):
    # فقط متن کاربر رو ذخیره می‌کنیم، بدون AI
    user = get_user(update.effective_user.id)
    user["history"].append(update.message.text)
    save_data()
    await update.message.reply_text("پیام ثبت شد ✅")

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "show_tasks":
        user = get_user(query.from_user.id)
        if not user["tasks"]:
            await query.message.reply_text("هیچ تسکی ندارید.")
        else:
            msg = "📋 تسک‌ها:\n\n"
            for t in user["tasks"]:
                msg += f"{'✅' if t['done'] else '⬜'} {t['id']}. {t['text']}\n"
            await query.message.reply_text(msg)
    elif query.data == "clear_history":
        get_user(query.from_user.id)["history"] = []
        save_data()
        await query.message.reply_text("تاریخچه پاک شد!")

# ======== اجرای ربات ========
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("task", add_task))
    app.add_handler(CommandHandler("tasks", show_tasks))
    app.add_handler(CommandHandler("done", done_task))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("ربات شروع شد!")
    app.run_polling()

if __name__ == "__main__":
    main()