import os
import asyncio
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatMemberStatus

# Получаем данные из переменных окружения
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MY_ID = int(os.environ.get("MY_ID", 0))
# Получаем ID целевого чата
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID", 0))

if not all([API_ID, API_HASH, BOT_TOKEN, TARGET_CHAT_ID]):
    raise ValueError(
        "Не заполнены все переменные в файле .env (особенно TARGET_CHAT_ID)")

app = Client("nuke_bot_session", api_id=API_ID, api_hash=API_HASH,
             bot_token=BOT_TOKEN)


async def nuke_target_chat():
    async with app:
        print(
            f"🚀 Бот запущен. Начинаю зачистку чата {TARGET_CHAT_ID}...")
        kicked_count = 0

        try:
            async for member in app.get_chat_members(TARGET_CHAT_ID):
                # АБСОЛЮТНАЯ ЗАЩИТА: Твой ID в безопасности
                if member.user.id == MY_ID:
                    continue

                # Защита админов, создателя и самого бота
                if member.status in [ChatMemberStatus.ADMINISTRATOR,
                                     ChatMemberStatus.OWNER] or member.user.is_self:
                    continue

                try:
                    await app.ban_chat_member(TARGET_CHAT_ID, member.user.id)
                    kicked_count += 1
                    print(f"[-] Удален пользователь: {member.user.id}")
                    await asyncio.sleep(1)  # Защита от лимитов Telegram

                except FloodWait as e:
                    print(
                        f"⚠️ Ждем")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    print(f"❌ Ошибка")

            print(f"✅ Зачистка завершена. Всего удалено: {kicked_count}")

        except Exception as e:
            print(
                f"Критическая ошибка при доступе к чату: {e}. Бот точно является админом в этом чате?")


if __name__ == "__main__":
    # Запускаем скрипт сразу при включении
    app.run(nuke_target_chat())