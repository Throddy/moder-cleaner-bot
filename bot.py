import os
import asyncio
import urllib.request
import json
from pyrogram import Client
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatMemberStatus

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MY_ID = int(os.environ.get("MY_ID", 0))
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID", 0))

app = Client("nuke_bot_session", api_id=API_ID, api_hash=API_HASH,
             bot_token=BOT_TOKEN)


async def nuke_target_chat():
    async with app:
        print(f"🚀 Бот запущен. Подготовка к зачистке чата {TARGET_CHAT_ID}...")

        # --- ХАК ДЛЯ ОБХОДА PEER_ID_INVALID ---
        # Отправляем сообщение через простой HTTP API.
        # Pyrogram поймает эхо этого сообщения и вытащит из него крипто-ключ чата.
        print("🔄 Пробиваем кэш Telegram (знакомим сессию с чатом)...")
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = json.dumps({
                "chat_id": TARGET_CHAT_ID,
                "text": "Активация протокола защиты...",
                "disable_notification": True
            }).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={
                'Content-Type': 'application/json'})
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"⚠️ Ошибка при отправке HTTP-пинг сообщения: {e}")

        # Даем Pyrogram 3 секунды на обработку обновления
        print("⏳ Жду 3 секунды для синхронизации...")
        await asyncio.sleep(3)
        # ---------------------------------------

        kicked_count = 0
        try:
            print("💥 НАЧИНАЮ МАССОВОЕ УДАЛЕНИЕ!")
            async for member in app.get_chat_members(TARGET_CHAT_ID):
                # АБСОЛЮТНАЯ ЗАЩИТА
                if member.user.id == MY_ID:
                    continue
                # Пропускаем админов
                if member.status in [ChatMemberStatus.ADMINISTRATOR,
                                     ChatMemberStatus.OWNER] or member.user.is_self:
                    continue

                try:
                    await app.ban_chat_member(TARGET_CHAT_ID, member.user.id)
                    kicked_count += 1
                    print(f"[-] Удален бот/пользователь: {member.user.id}")
                    await asyncio.sleep(
                        1)  # Пауза, чтобы Telegram не забанил самого бота
                except FloodWait as e:
                    print(
                        f"⚠️ Лимит Telegram. Приостановка на {e.value} секунд...")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    print(f"❌ Ошибка с {member.user.id}: {e}")

            print(
                f"✅ ЗАЧИСТКА УСПЕШНО ЗАВЕРШЕНА. Всего удалено: {kicked_count}")
        except Exception as e:
            print(f"Критическая ошибка при попытке удалить участников: {e}")


if __name__ == "__main__":
    app.run(nuke_target_chat())