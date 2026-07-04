from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import asyncio
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8889337701:AAHCNgL6r2GCII_5wYaV8tsqCUBy_WL5ZY8"

user_data = {}

# Фиктивный HTTP-сервер для Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {
        "warn_limit": 3,
        "warn_count": 0,
        "warn_msg_id": None,
        "muted": False,
        "active": True
    }
    keyboard = [[InlineKeyboardButton("Стоп", callback_data="stop")]]
    await update.message.reply_text(
        "@swill_controlbot управляет этим чатом [Стоп]",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def stop_bot(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    if chat_id in user_data:
        user_data[chat_id]["active"] = False
    await query.edit_text("Бот отключён. Напишите /start для включения.")

async def spam(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not user_data.get(chat_id, {}).get("active", True):
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Использование: .spam <число> <текст>")
        return
    try:
        count = int(args[0])
        if count > 1000:
            count = 1000
        text = " ".join(args[1:])
        for _ in range(count):
            await update.message.reply_text(text)
            await asyncio.sleep(0.05)
    except ValueError:
        await update.message.reply_text("Ошибка: число должно быть целым")

async def warn(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not user_data.get(chat_id, {}).get("active", True):
        return
    args = context.args
    if args and args[0].isdigit():
        user_data[chat_id]["warn_limit"] = int(args[0])
    user_data[chat_id]["warn_count"] = 0
    if user_data[chat_id].get("warn_msg_id"):
        try:
            await context.bot.delete_message(chat_id, user_data[chat_id]["warn_msg_id"])
        except:
            pass
    msg = await update.message.reply_text(f"🚫 Варн: 0/{user_data[chat_id]['warn_limit']}")
    user_data[chat_id]["warn_msg_id"] = msg.message_id

async def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id not in user_data or not user_data[chat_id].get("active", True):
        return
    data = user_data[chat_id]
    if update.message.text and update.message.text.startswith("."):
        return
    if data.get("muted", False):
        try:
            await context.bot.delete_message(chat_id, update.message.message_id)
        except:
            pass
        return
    data["warn_count"] += 1
    limit = data["warn_limit"]
    if data["warn_count"] > limit:
        data["warn_count"] = limit
    if data.get("warn_msg_id"):
        try:
            await context.bot.edit_message_text(
                f"🚫 Варн: {data['warn_count']}/{limit}",
                chat_id=chat_id,
                message_id=data["warn_msg_id"]
            )
        except:
            pass
    if data["warn_count"] >= limit:
        data["muted"] = True
        await update.message.reply_text("🔇 Мут активирован (3/3)")

async def mute(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in user_data:
        user_data[chat_id]["muted"] = True
        await update.message.reply_text("🔇 Мут включён")

async def unmute(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in user_data:
        user_data[chat_id]["muted"] = False
        await update.message.reply_text("🔊 Мут выключен")

async def clear(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if chat_id in user_data:
        user_data[chat_id]["warn_count"] = 0
        if user_data[chat_id].get("warn_msg_id"):
            try:
                await context.bot.edit_message_text(
                    f"🚫 Варн: 0/{user_data[chat_id]['warn_limit']}",
                    chat_id=chat_id,
                    message_id=user_data[chat_id]["warn_msg_id"]
                )
            except:
                pass
        await update.message.reply_text("Варны сброшены")

def main():
    # Запускаем HTTP-сервер для Render
    import threading
    run_http_server()
    
    # Запускаем бота
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(stop_bot, pattern="stop"))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
