import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import anthropic

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
user_data = {}

SYSTEM_PROMPT = "تو یک دستیار هوشمند فارسی‌زبان هستی. همیشه به فارسی پاسخ بده. تاریخ امروز: " + datetime.now().strftime("%Y/%m/%d")

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"history": [], "tasks": []}
    return user_data[user_id]

def ask_claude(user_id, message):
    user = get_user(user_id)
    user["history"].append({"role": "user", "content": message})
    if len(user["history"]) > 20:
        user["history"] = user["history"][-20:]
    try:
        response = client.messages.create(model="claude-sonnet-4-6", max_tokens=1024, system=SYSTEM_PROMPT, messages=user["history"])
        reply = response.content[0].text
        user["history"].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return "خطا در ارتباط با هوش مصنوعی. دوباره امتحان کنید."

async def start(update, context):
    keyboard = [[InlineKeyboardButton("📋 تسک‌ها", callback_data="show_tasks"), InlineKeyboardButton("🗑 پاک کردن", callback_data="clear_history")]]
    await update.message.reply_text("سلام! من دستیار هوشمند شما هستم.\n\n/task [متن] - تسک جدید\n/tasks - لیست تسک‌ها\n/done [شماره] - انجام شد\n/clear - پاک کردن تاریخچه", reply_markup=InlineKeyboardMarkup(keyboard))

async def add_task(update, context):
    user = get_user(update.effective_user.id)
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("مثال: /task خرید نان")
        return
    user["tasks"].append({"id": len(user["tasks"]) + 1, "text": text, "done": False})
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
            await update.message.reply_text(f"✅ انجام شد: {t['text']}")
            return

async def clear_history(update, context):
    get_user(update.effective_user.id)["history"] = []
    await update.message.reply_text("تاریخچه پاک شد!")

async def handle_message(update, context):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = ask_claude(update.effective_user.id, update.message.text)
    await update.message.reply_text(reply)

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
        await query.message.reply_text("تاریخچه پاک شد!")

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
