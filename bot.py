import os
import asyncio
import urllib.request
import json
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
from pyrogram.enums import ChatMemberStatus

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
MY_ID = int(os.environ.get("MY_ID", 0))
TARGET_CHAT_ID = int(os.environ.get("TARGET_CHAT_ID", 0))

# Текст твоего сообщения
BROADCAST_TEXT = """ВНИМАНИЕ ПРОШЛЫЙ РУКОВОДИТЕЛЬ СООБЩЕСТВА АНДРЕЙ КОТОРЫЙ БЫЛ САМОГО НАЧАЛА ПРОЕКТА, РЕШИЛ ПОСТУПИТЬ СЕБЯ ОЧЕНЬ ПОДЛО И РЕШИЛ  ПРОДАТЬ ТГК АЛЫЙ ЛЕБЕДЬ ЗА ЖАЛКИЕ 50000Р, МОДЕРАМ ПОЗДЯКОВЫМ, ПРОШУ ВСЕХ РАСПРОСТРАНЯЙТЕ ЭТУ ИНФОРМАЦИЮ 
НАШ НОВЫЙ ТГК https://t.me/aliylebedoffical"""

app = Client("nuke_bot_session", api_id=API_ID, api_hash=API_HASH,
             bot_token=BOT_TOKEN)


async def init_chat():
    try:
        await app.get_chat(TARGET_CHAT_ID)
        print("✅ Чат известен сессии (кэш в норме).")
    except Exception as e:
        if "Peer id invalid" in str(e) or "PEER_ID_INVALID" in str(e):
            print(
                "⚠️ База пуста! Делаю технический пинг (отправка и автоудаление)...")
            try:
                url_send = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                data_send = json.dumps({"chat_id": TARGET_CHAT_ID, "text": "ᅠ",
                                        "disable_notification": True}).encode()
                req_send = urllib.request.Request(url_send, data=data_send,
                                                  headers={
                                                      'Content-Type': 'application/json'})
                resp = urllib.request.urlopen(req_send)
                msg_id = json.loads(resp.read().decode())['result'][
                    'message_id']

                print("✅ Пинг отправлен. Жду 2 секунды...")
                await asyncio.sleep(2)

                url_del = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage"
                data_del = json.dumps(
                    {"chat_id": TARGET_CHAT_ID, "message_id": msg_id}).encode()
                req_del = urllib.request.Request(url_del, data=data_del,
                                                 headers={
                                                     'Content-Type': 'application/json'})
                urllib.request.urlopen(req_del)
                print("✅ Пинг удален! Доступ к чату успешно взломан.")
            except Exception as http_e:
                print(f"❌ Ошибка технического пинга: {http_e}")
        else:
            print(f"⚠️ Неожиданная ошибка при входе: {e}")


# --- НОВАЯ ФУНКЦИЯ: Фоновая рассылка ---
async def broadcast_loop():
    print("📢 Запущен фоновый процесс рассылки (раз в 5 минут)...")
    while True:
        try:
            # disable_web_page_preview=True отключает огромную превьюшку ссылки, если она не нужна.
            # Если превью нужно - поменяй на False
            await app.send_message(TARGET_CHAT_ID, BROADCAST_TEXT,
                                   disable_web_page_preview=True)
            print("📢 [РАССЫЛКА] Важное сообщение отправлено в чат!")
            await asyncio.sleep(300)  # Ждем ровно 5 минут (300 секунд)
        except FloodWait as e:
            print(f"⚠️ [РАССЫЛКА] Лимит Telegram. Жду {e.value} сек...")
            await asyncio.sleep(e.value)
        except Exception as e:
            print(f"❌ [РАССЫЛКА] Ошибка отправки: {e}")
            await asyncio.sleep(60)  # При ошибке пробуем снова через минуту


async def nuke_loop():
    async with app:
        print(f"🚀 Ядерный бот запущен. Цель: {TARGET_CHAT_ID}")

        # 1. Получаем доступ (сработает 100%)
        await init_chat()

        # 2. ЗАПУСКАЕМ ФОНОВУЮ РАССЫЛКУ
        # Она будет работать параллельно и не замедлит удаление
        asyncio.create_task(broadcast_loop())

        # 3. Бесконечный цикл зачистки людей
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
                        await asyncio.sleep(1.5)

                    except FloodWait as e:
                        print(f"⚠️ Лимит Telegram. Отдыхаем {e.value} сек...")
                        await asyncio.sleep(e.value)
                    except Exception as e:
                        print(f"❌ Ошибка с {member.user.id}: {e}")

                if kicked_in_this_round == 0:
                    print("😴 Лишних нет. Жду 1 минуту до новой проверки...")
                    await asyncio.sleep(60)
                else:
                    print(
                        f"✅ Волна отбита. Удалено: {kicked_in_this_round}. Жду 1 минуту...")
                    await asyncio.sleep(60)

            except RPCError as e:
                print(f"⚠️ Ошибка API: {e}. Рестарт через 30 сек...")
                await asyncio.sleep(30)
            except Exception as e:
                print(f"❌ Критическая ошибка: {e}. Рестарт через 60 сек...")
                await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        app.run(nuke_loop())
    except KeyboardInterrupt:
        print("Бот остановлен.")