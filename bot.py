import os
import asyncio
import urllib.request
import json
from pyrogram import Client
from pyrogram.errors import FloodWait, PeerIdInvalid, RPCError
from pyrogram.enums import ChatMemberStatus

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MY_ID = int(os.environ.get("MY_ID", 0))
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID", 0))

app = Client("nuke_bot_session", api_id=API_ID, api_hash=API_HASH,
             bot_token=BOT_TOKEN)


async def init_chat():
    try:
        await app.get_chat(TARGET_CHAT_ID)
        print("✅ Чат известен сессии.")
    except PeerIdInvalid:
        print("⚠️ Делаю НЕВИДИМЫЙ пинг для получения доступа к чату...")
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendChatAction"
            data = json.dumps(
                {"chat_id": TARGET_CHAT_ID, "action": "typing"}).encode(
                'utf-8')
            req = urllib.request.Request(url, data=data, headers={
                'Content-Type': 'application/json'})
            urllib.request.urlopen(req)
            print("✅ Невидимый пинг прошел. Жду 3 секунды...")
            await asyncio.sleep(3)
        except Exception as e:
            print(f"❌ Ошибка HTTP-пинга: {e}")
    except Exception as e:
        print(f"⚠️ Ошибка при проверке чата: {e}")


async def wipe_messages():
    print("\n🗑 НАЧИНАЮ ПОЛНУЮ ОЧИСТКУ ИСТОРИИ СООБЩЕНИЙ...")
    message_ids = []
    deleted_count = 0

    try:
        # Проходимся по всей истории чата
        async for message in app.get_chat_history(TARGET_CHAT_ID):
            message_ids.append(message.id)

            # Telegram разрешает удалять пачками максимум по 100 штук
            if len(message_ids) >= 100:
                try:
                    await app.delete_messages(TARGET_CHAT_ID, message_ids)
                    deleted_count += len(message_ids)
                    print(f"[~] Стерто {deleted_count} сообщений...")
                    message_ids.clear()
                    await asyncio.sleep(
                        1.5)  # Пауза, чтобы не получить бан от антиспама
                except FloodWait as e:
                    print(
                        f"⚠️ Лимит на удаление сообщений. Жду {e.value} секунд...")
                    await asyncio.sleep(e.value)

        # Удаляем остатки (если их меньше 100)
        if message_ids:
            await app.delete_messages(TARGET_CHAT_ID, message_ids)
            deleted_count += len(message_ids)

        print(
            f"✅ ИСТОРИЯ ЧАТА ПОЛНОСТЬЮ ОЧИЩЕНА! Удалено сообщений: {deleted_count}\n")
    except Exception as e:
        print(f"❌ Ошибка при удалении сообщений: {e}")


async def nuke_loop():
    async with app:
        print(f"🚀 Ядерный бот запущен. Цель: {TARGET_CHAT_ID}")

        # 1. Получаем доступ
        await init_chat()

        # 2. СНАЧАЛА УДАЛЯЕМ ВСЕ СООБЩЕНИЯ
        await wipe_messages()

        # 3. ЗАТЕМ УДАЛЯЕМ ВСЕХ УЧАСТНИКОВ (в бесконечном цикле)
        while True:
            kicked_in_this_round = 0
            print("\n🔄 Начинаю сканирование списка участников...")

            try:
                async for member in app.get_chat_members(TARGET_CHAT_ID):
                    if member.user.id == MY_ID:
                        continue
                    if member.status in [ChatMemberStatus.ADMINISTRATOR,
                                         ChatMemberStatus.OWNER] or member.user.is_self:
                        continue

                    try:
                        await app.ban_chat_member(TARGET_CHAT_ID,
                                                  member.user.id)
                        kicked_in_this_round += 1
                        print(
                            f"[-] Снесен: {member.user.id} ({member.user.first_name or 'Без имени'})")
                        await asyncio.sleep(1)

                    except FloodWait as e:
                        print(
                            f"⚠️ Лимит Telegram. Отдыхаем {e.value} секунд...")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        print(f"❌ Ошибка с {member.user.id}: {e}")

                if kicked_in_this_round == 0:
                    print("😴 Лишних нет. Ухожу в режим ожидания на 5 минут...")
                    await asyncio.sleep(300)
                else:
                    print(
                        f"✅ Волна отбита. Удалено: {kicked_in_this_round}. Жду 1 минуту...")
                    await asyncio.sleep(60)

            except RPCError as e:
                print(f"⚠️ Ошибка API: {e}. Рестарт цикла через 30 секунд...")
                await asyncio.sleep(30)
            except Exception as e:
                print(
                    f"❌ Критическая ошибка: {e}. Рестарт цикла через 60 секунд...")
                await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        app.run(nuke_loop())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")