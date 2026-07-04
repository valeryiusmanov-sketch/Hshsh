import asyncio
import logging
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message

# ===== КОНФИГ =====
TOKEN = "8664693238:AAGGTtyn8GMgQ5BlXFlHH6JOof3APCdGTfk"  # Твой токен
ADMIN_ID = 8205534130  # Твой Telegram ID
# ==================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилища
muted_users = {}
warns = {}

@dp.message(F.text & F.chat.type == "private")
async def handle_private_messages(message: Message):
    chat_id = message.chat.id
    text = message.text
    
    # ===== .mute N =====
    if text.startswith(".mute "):
        try:
            minutes = int(text.split()[1])
            if minutes < 1 or minutes > 1440:
                await message.answer("❌ От 1 до 1440 минут")
                return
        except:
            await message.answer("❌ Использование: .mute 10")
            return
        
        try:
            chat = await bot.get_chat(chat_id)
            if chat_id not in muted_users:
                muted_users[chat_id] = {}
            muted_users[chat_id][chat_id] = datetime.now() + timedelta(minutes=minutes)
            
            await message.answer(f"✅ {chat.first_name} замучен на {minutes} мин.")
            await bot.send_message(ADMIN_ID, f"🔇 Мут {chat.first_name} на {minutes} мин.")
            asyncio.create_task(auto_unmute(chat_id, chat_id, minutes))
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
        return
    
    # ===== .unmute =====
    elif text == ".unmute":
        chat_id = message.chat.id
        if chat_id in muted_users and chat_id in muted_users[chat_id]:
            del muted_users[chat_id][chat_id]
            chat = await bot.get_chat(chat_id)
            await message.answer(f"✅ Мут снят с {chat.first_name}")
            await bot.send_message(ADMIN_ID, f"🔊 Мут снят с {chat.first_name}")
        else:
            await message.answer("ℹ️ Пользователь не в муте")
        return
    
    # ===== .help =====
    elif text == ".help":
        await message.answer(
            "👋 RootExe — автоматизация личных чатов\n\n"
            ".mute N — мут на N минут\n"
            ".unmute — снять мут\n"
            ".spam текст N — спам (до 30)\n"
            ".txt текст — анимация\n"
            ".info — данные собеседника\n"
            ".warn N — предупреждение (мут после N)\n"
            ".unwarn — снять варн\n"
            ".help — это меню"
        )
        return
    
    # ===== .info =====
    elif text == ".info":
        chat = await bot.get_chat(chat_id)
        await message.answer(
            f"👤 {chat.first_name or 'Нет имени'}\n"
            f"🆔 {chat.id}\n"
            f"👀 @{chat.username or 'нет'}"
        )
        return
    
    # ===== .spam текст N =====
    elif text.startswith(".spam "):
        parts = text.split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("❌ Использование: .spam Привет 5")
            return
        try:
            count = int(parts[2])
            if count > 30:
                count = 30
                await message.answer("⚠️ Ограничено до 30")
        except:
            count = 5
        spam_text = parts[1]
        for i in range(count):
            await message.answer(spam_text)
            await asyncio.sleep(0.3)
        return
    
    # ===== .txt текст =====
    elif text.startswith(".txt "):
        anim_text = text.replace(".txt ", "").strip()
        if not anim_text:
            await message.answer("❌ Напиши текст")
            return
        for char in anim_text:
            await message.answer(char)
            await asyncio.sleep(0.5)
        return
    
    # ===== .warn N =====
    elif text.startswith(".warn "):
        try:
            limit = int(text.split()[1])
            if limit < 1:
                await message.answer("❌ Лимит > 0")
                return
        except:
            limit = 3
        
        user_id = chat_id
        warns[user_id] = warns.get(user_id, 0) + 1
        current_warns = warns[user_id]
        
        chat = await bot.get_chat(user_id)
        await message.answer(f"⚠️ {chat.first_name} получил варн ({current_warns}/{limit})")
        
        if current_warns >= limit:
            if user_id not in muted_users:
                muted_users[user_id] = {}
            muted_users[user_id][user_id] = datetime.now() + timedelta(hours=24)
            await message.answer(f"🚫 {chat.first_name} замучен на 24 часа")
            await bot.send_message(ADMIN_ID, f"🚫 Автомут {chat.first_name} за {limit} варнов")
            asyncio.create_task(auto_unmute(user_id, user_id, 1440))
        return
    
    # ===== .unwarn =====
    elif text == ".unwarn":
        user_id = chat_id
        if user_id in warns and warns[user_id] > 0:
            warns[user_id] -= 1
            chat = await bot.get_chat(user_id)
            await message.answer(f"✅ Варн снят. Осталось: {warns[user_id]}")
        else:
            await message.answer("ℹ️ Нет варнов")
        return
    
    # ===== ФИЛЬТР УДАЛЕНИЯ =====
    # Если сообщение от собеседника (не от бота) и он в муте
    if message.from_user.id != bot.id:
        user_id = message.from_user.id
        if chat_id in muted_users and user_id in muted_users[chat_id]:
            try:
                await bot.delete_message(chat_id, message.message_id)
                await bot.send_message(
                    chat_id,
                    f"🗑️ Сообщение удалено (мут активен)"
                )
                await bot.send_message(
                    ADMIN_ID,
                    f"🗑️ Удалено: {message.text[:50]} от {message.from_user.first_name}"
                )
            except Exception as e:
                print(f"Ошибка удаления: {e}")

async def auto_unmute(chat_id: int, user_id: int, minutes: int):
    """Автоснятие мута"""
    await asyncio.sleep(minutes * 60)
    if chat_id in muted_users and user_id in muted_users[chat_id]:
        del muted_users[chat_id][user_id]
        try:
            chat = await bot.get_chat(chat_id)
            await bot.send_message(chat_id, f"🔓 Мут снят с {chat.first_name}")
        except:
            pass

async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот запущен! Жду команд...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
